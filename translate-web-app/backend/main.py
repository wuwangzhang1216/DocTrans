"""
FastAPI Backend for Document Translation
Simplified architecture - direct Python integration, no subprocess overhead
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

# Load environment variables FIRST
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Explicitly set GEMINI_API_KEY environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    # Try loading it directly from .env file
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    GEMINI_API_KEY = line.split('=', 1)[1].strip()
                    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
                    break
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")

# Add parent directory to path to import translators
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from translators import DocumentTranslator
from s3_helper import get_s3_helper

# Initialize FastAPI app
app = FastAPI(title="DocTrans API", version="2.0")

# CORS configuration
ALLOWED_ORIGINS = os.environ.get(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,https://www.doctranslab.com,https://doctranslab.com,https://doctrans-frontend-wz-eeda0a3df81a.herokuapp.com'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR = Path(__file__).parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Verify API key is loaded
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Configure max workers based on environment (lower for Heroku's memory constraints)
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '4'))  # Default 4 for Heroku

translator = DocumentTranslator(
    api_key=GEMINI_API_KEY,
    model="gemini-2.0-flash-lite",
    max_workers=MAX_WORKERS
)

# Initialize S3 helper
s3_helper = get_s3_helper()

# Job storage (in-memory for now, can be replaced with Redis later)
jobs = {}

# WebSocket connections
active_connections = {}

class JobStatus(BaseModel):
    jobId: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0-100
    message: str
    outputFile: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "DocTrans FastAPI Backend", "version": "2.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/translate")
async def translate_document(
    file: UploadFile = File(...),
    targetLanguage: str = Form("Chinese")
):
    """Upload and translate document"""

    print(f"[DEBUG] Received targetLanguage: {targetLanguage}")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.pptx', '.txt', '.md']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")

    # Save uploaded file
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    input_path = UPLOAD_DIR / unique_filename

    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Translation queued",
        "input_path": str(input_path),
        "filename": file.filename,
        "target_language": targetLanguage,
        "created_at": datetime.now().isoformat()
    }

    # Start translation in background
    asyncio.create_task(process_translation(job_id))

    return {
        "success": True,
        "jobId": job_id,
        "message": "File uploaded and queued for translation"
    }

async def process_translation(job_id: str):
    """Process translation job in background"""

    job = jobs[job_id]
    input_path = job["input_path"]
    target_language = job["target_language"]

    try:
        # Update status
        job["status"] = "processing"
        job["progress"] = 5
        job["message"] = "Starting translation..."
        await broadcast_job_update(job_id)

        # Determine output path
        input_file = Path(input_path)
        output_filename = f"{input_file.stem}_translated_{target_language}{input_file.suffix}"
        output_path = OUTPUT_DIR / output_filename

        # Get event loop for thread-safe scheduling
        loop = asyncio.get_event_loop()

        # Progress callback (synchronous, updates job dict)
        def progress_callback(progress: float):
            """Update job progress"""
            percent = int(progress * 100)
            job["progress"] = percent
            job["message"] = f"Translating... {percent}%"
            # Schedule broadcast from executor thread safely
            asyncio.run_coroutine_threadsafe(broadcast_job_update(job_id), loop)

        # Perform translation (runs in executor to not block)
        result = await loop.run_in_executor(
            None,
            lambda: translator.translate_document(
                input_path=str(input_path),
                output_path=str(output_path),
                target_language=target_language,
                progress_callback=progress_callback
            )
        )

        if result:
            # Success
            # For PDFs, result is a tuple (mono_path, dual_path), for others it's True/False
            if isinstance(result, tuple) and len(result) == 2:
                # PDF translation - use the mono path
                mono_path, dual_path = result
                actual_output_path = Path(mono_path)
                actual_output_filename = actual_output_path.name

                # Upload to S3 if configured
                s3_key = None
                if s3_helper:
                    s3_key = f"outputs/{actual_output_filename}"
                    upload_success = await loop.run_in_executor(
                        None,
                        lambda: s3_helper.upload_file(str(actual_output_path), s3_key)
                    )
                    if upload_success:
                        # Delete local file after successful upload
                        try:
                            os.remove(actual_output_path)
                        except:
                            pass

                job["status"] = "completed"
                job["progress"] = 100
                job["message"] = "Translation completed successfully"
                job["output_file"] = actual_output_filename
                job["output_path"] = str(actual_output_path)
                job["s3_key"] = s3_key
                await broadcast_job_update(job_id)
            else:
                # Non-PDF translation
                # Upload to S3 if configured
                s3_key = None
                if s3_helper:
                    s3_key = f"outputs/{output_filename}"
                    upload_success = await loop.run_in_executor(
                        None,
                        lambda: s3_helper.upload_file(str(output_path), s3_key)
                    )
                    if upload_success:
                        # Delete local file after successful upload
                        try:
                            os.remove(output_path)
                        except:
                            pass

                job["status"] = "completed"
                job["progress"] = 100
                job["message"] = "Translation completed successfully"
                job["output_file"] = output_filename
                job["output_path"] = str(output_path)
                job["s3_key"] = s3_key
                await broadcast_job_update(job_id)
        else:
            raise Exception("Translation failed")

    except Exception as e:
        # Failed
        job["status"] = "failed"
        job["progress"] = 0
        job["message"] = "Translation failed"
        job["error"] = str(e)
        await broadcast_job_update(job_id)
    finally:
        # Clean up input file
        try:
            os.remove(input_path)
        except:
            pass

async def broadcast_job_update(job_id: str):
    """Broadcast job update to connected WebSocket clients"""
    if job_id in active_connections:
        job = jobs[job_id]
        status = {
            "jobId": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "outputFile": job.get("output_file"),
            "error": job.get("error")
        }

        for websocket in active_connections[job_id]:
            try:
                await websocket.send_json(status)
            except:
                pass

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates"""
    await websocket.accept()

    # Add to active connections
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)

    try:
        # Send current status immediately
        if job_id in jobs:
            job = jobs[job_id]
            await websocket.send_json({
                "jobId": job_id,
                "status": job["status"],
                "progress": job["progress"],
                "message": job["message"],
                "outputFile": job.get("output_file"),
                "error": job.get("error")
            })

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[job_id].remove(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return {
        "jobId": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "outputFile": job.get("output_file"),
        "error": job.get("error")
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download translated file"""

    # If S3 is configured, use presigned URL
    if s3_helper:
        s3_key = f"outputs/{filename}"
        presigned_url = s3_helper.generate_presigned_url(s3_key, expiration=3600)

        if presigned_url:
            # Redirect to S3 presigned URL
            return RedirectResponse(url=presigned_url)
        else:
            raise HTTPException(status_code=404, detail="File not found in S3")

    # Fallback to local file if S3 is not configured
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
