"""
RQ Worker for processing translation jobs from Redis queue
"""

import os
import sys
from pathlib import Path

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
from rq import get_current_job

# Initialize translator
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '4'))
translator = DocumentTranslator(
    api_key=GEMINI_API_KEY,
    model="gemini-2.0-flash-lite",
    max_workers=MAX_WORKERS
)

# Initialize S3 helper
s3_helper = get_s3_helper()


def process_translation(s3_key: str, filename: str, target_language: str):
    """
    Process translation job (S3-based for multi-dyno support)

    Args:
        s3_key: S3 key of uploaded file
        filename: Original filename
        target_language: Target language for translation

    Returns:
        str: Output S3 key on success
    """
    job = get_current_job()

    try:
        if not s3_helper:
            raise Exception("S3 not configured - cannot process job")

        # Update job metadata
        job.meta['progress'] = 5
        job.meta['message'] = 'Downloading file from storage...'
        job.save_meta()

        # Download from S3 to temp location
        import tempfile
        temp_dir = tempfile.mkdtemp()
        input_path = Path(temp_dir) / filename

        download_success = s3_helper.download_file(s3_key, str(input_path))
        if not download_success:
            raise Exception(f"Failed to download file from S3: {s3_key}")

        # Determine output path
        output_filename = f"{input_path.stem}_translated_{target_language}{input_path.suffix}"
        output_path = Path(temp_dir) / output_filename

        # Progress callback
        def progress_callback(progress: float):
            """Update job progress"""
            percent = int(progress * 100)
            job.meta['progress'] = percent
            job.meta['message'] = f"Translating... {percent}%"
            job.save_meta()

        # Perform translation - ensure all paths are strings
        result = translator.translate_document(
            input_path=str(input_path.resolve()),  # Absolute path as string
            output_path=str(output_path.resolve()),  # Absolute path as string
            target_language=target_language,
            progress_callback=progress_callback
        )

        if result:
            # Success
            # For PDFs, result is a tuple (mono_path, dual_path), for others it's True/False
            if isinstance(result, tuple) and len(result) == 2:
                # PDF translation - use the mono path
                mono_path, dual_path = result
                actual_output_path = Path(mono_path)
                actual_output_filename = actual_output_path.name

                # Upload to S3
                output_s3_key = f"outputs/{actual_output_filename}"
                upload_success = s3_helper.upload_file(str(actual_output_path), output_s3_key)

                if not upload_success:
                    raise Exception("Failed to upload result to S3")

                job.meta['progress'] = 100
                job.meta['message'] = 'Translation completed successfully'
                job.save_meta()

                return actual_output_filename
            else:
                # Non-PDF translation
                output_s3_key = f"outputs/{output_filename}"
                upload_success = s3_helper.upload_file(str(output_path), output_s3_key)

                if not upload_success:
                    raise Exception("Failed to upload result to S3")

                job.meta['progress'] = 100
                job.meta['message'] = 'Translation completed successfully'
                job.save_meta()

                return output_filename
        else:
            raise Exception("Translation failed")

    except Exception as e:
        # Failed
        job.meta['progress'] = 0
        job.meta['message'] = 'Translation failed'
        job.meta['error'] = str(e)
        job.save_meta()
        raise
    finally:
        # Clean up temp files
        try:
            import shutil
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

        # Clean up uploaded file from S3
        try:
            if 's3_key' in locals() and s3_helper:
                s3_helper.delete_file(s3_key)
        except:
            pass


if __name__ == '__main__':
    # Run worker (can be started with: rq worker translation)
    from redis import Redis
    from rq import Worker

    REDIS_URL = os.environ.get('REDIS_URL')
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is required")

    redis_conn = Redis.from_url(
        REDIS_URL,
        decode_responses=False,
        ssl_cert_reqs=None  # Disable SSL certificate verification
    )

    # Create worker
    worker = Worker(['translation'], connection=redis_conn)

    print("Worker started. Listening for translation jobs...")
    worker.work()
