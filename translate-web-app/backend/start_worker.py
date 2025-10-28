"""
Convenient script to start RQ worker for translation jobs
Usage: python start_worker.py
"""

import os
import sys
from pathlib import Path
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Verify Redis URL
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL:
    print("ERROR: REDIS_URL environment variable is required")
    sys.exit(1)

# Verify Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable is required")
    sys.exit(1)

try:
    # Test Redis connection with SSL certificate verification disabled
    redis_conn = Redis.from_url(
        REDIS_URL,
        decode_responses=False,
        ssl_cert_reqs=None  # Disable SSL certificate verification for self-signed certs
    )
    redis_conn.ping()
    print(f"✓ Redis connection successful")
except Exception as e:
    print(f"ERROR: Cannot connect to Redis: {e}")
    sys.exit(1)

# Create worker
print("Starting RQ worker for 'translation' queue...")
worker = Worker(['translation'], connection=redis_conn)

# Worker configuration
WORKER_CONCURRENCY = int(os.environ.get('WORKER_CONCURRENCY', '5'))
print(f"Worker concurrency: {WORKER_CONCURRENCY}")

# Start worker
worker.work()
