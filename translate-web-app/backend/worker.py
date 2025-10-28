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


def process_translation(input_path: str, filename: str, target_language: str, output_dir: str):
    """
    Process translation job

    Args:
        input_path: Path to input file
        filename: Original filename
        target_language: Target language for translation
        output_dir: Directory for output files

    Returns:
        str: Output filename on success
    """
    job = get_current_job()

    try:
        # Update job metadata
        job.meta['progress'] = 5
        job.meta['message'] = 'Starting translation...'
        job.save_meta()

        # Determine output path
        input_file = Path(input_path)
        output_filename = f"{input_file.stem}_translated_{target_language}{input_file.suffix}"
        output_path = Path(output_dir) / output_filename

        # Progress callback
        def progress_callback(progress: float):
            """Update job progress"""
            percent = int(progress * 100)
            job.meta['progress'] = percent
            job.meta['message'] = f"Translating... {percent}%"
            job.save_meta()

        # Perform translation
        result = translator.translate_document(
            input_path=input_path,
            output_path=str(output_path),
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

                # Upload to S3 if configured
                if s3_helper:
                    s3_key = f"outputs/{actual_output_filename}"
                    upload_success = s3_helper.upload_file(str(actual_output_path), s3_key)
                    if upload_success:
                        # Delete local file after successful upload
                        try:
                            os.remove(actual_output_path)
                        except:
                            pass

                job.meta['progress'] = 100
                job.meta['message'] = 'Translation completed successfully'
                job.save_meta()

                return actual_output_filename
            else:
                # Non-PDF translation
                # Upload to S3 if configured
                if s3_helper:
                    s3_key = f"outputs/{output_filename}"
                    upload_success = s3_helper.upload_file(str(output_path), s3_key)
                    if upload_success:
                        # Delete local file after successful upload
                        try:
                            os.remove(output_path)
                        except:
                            pass

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
        # Clean up input file
        try:
            os.remove(input_path)
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
