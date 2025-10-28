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
from redis import Redis
from rq import Queue
from rq.job import Job

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

# Redis configuration
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable is required")

# Initialize Redis connection with SSL certificate verification disabled for self-signed certs
redis_conn = Redis.from_url(
    REDIS_URL,
    decode_responses=False,
    ssl_cert_reqs=None  # Disable SSL certificate verification
)
translation_queue = Queue('translation', connection=redis_conn)

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

    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.pptx', '.txt', '.md']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")

    # Read file content
    content = await file.read()

    # Upload to S3 first (required for Heroku multi-dyno architecture)
    unique_filename = f"{uuid.uuid4()}_{file.filename}"

    if s3_helper:
        # Upload to S3
        s3_key = f"uploads/{unique_filename}"
        upload_success = s3_helper.upload_file_content(content, s3_key)

        if not upload_success:
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")

        # Enqueue job with S3 key
        job = translation_queue.enqueue(
            'worker.process_translation',
            args=(s3_key, file.filename, targetLanguage),
            job_timeout='10m',
            result_ttl=3600,  # Keep result for 1 hour
            failure_ttl=3600
        )
    else:
        # Fallback: save locally (only works for single dyno)
        input_path = UPLOAD_DIR / unique_filename
        with open(input_path, "wb") as f:
            f.write(content)

        # Enqueue job with local path
        job = translation_queue.enqueue(
            'worker.process_translation_local',
            args=(str(input_path), file.filename, targetLanguage, str(OUTPUT_DIR)),
            job_timeout='10m',
            result_ttl=3600,
            failure_ttl=3600
        )

    return {
        "success": True,
        "jobId": job.id,
        "message": "File uploaded and queued for translation"
    }

async def broadcast_job_update(job_id: str):
    """Broadcast job update to connected WebSocket clients"""
    if job_id in active_connections:
        try:
            job = Job.fetch(job_id, connection=redis_conn)

            # Map RQ status to our status
            status_map = {
                'queued': 'queued',
                'started': 'processing',
                'finished': 'completed',
                'failed': 'failed'
            }

            status = {
                "jobId": job_id,
                "status": status_map.get(job.get_status(), 'queued'),
                "progress": job.meta.get('progress', 0),
                "message": job.meta.get('message', 'Processing...'),
                "outputFile": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None
            }

            for websocket in active_connections[job_id]:
                try:
                    await websocket.send_json(status)
                except:
                    pass
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
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            status_map = {
                'queued': 'queued',
                'started': 'processing',
                'finished': 'completed',
                'failed': 'failed'
            }

            await websocket.send_json({
                "jobId": job_id,
                "status": status_map.get(job.get_status(), 'queued'),
                "progress": job.meta.get('progress', 0),
                "message": job.meta.get('message', 'Processing...'),
                "outputFile": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None
            })
        except:
            pass

        # Keep connection alive and poll for updates
        while True:
            await asyncio.sleep(1)
            await broadcast_job_update(job_id)
    except WebSocketDisconnect:
        active_connections[job_id].remove(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)

        # Map RQ status to our status
        status_map = {
            'queued': 'queued',
            'started': 'processing',
            'finished': 'completed',
            'failed': 'failed'
        }

        return {
            "jobId": job_id,
            "status": status_map.get(job.get_status(), 'queued'),
            "progress": job.meta.get('progress', 0),
            "message": job.meta.get('message', 'Processing...'),
            "outputFile": job.result if job.is_finished else None,
            "error": str(job.exc_info) if job.is_failed else None
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found")

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
