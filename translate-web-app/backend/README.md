# Backend Service

Python FastAPI backend with Redis queue for document translation.

## Architecture

- **FastAPI**: REST API server for handling upload/download requests
- **Redis + RQ**: Job queue for background translation processing
- **WebSocket**: Real-time job status updates

## Setup

### 1. Install Dependencies

```bash
pip install -r ../../requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with:

```env
GEMINI_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379
# or for Redis Cloud:
# REDIS_URL=rediss://default:password@host:port
```

## Running

### Start Backend Server

```bash
python main.py
```

The server will start on `http://localhost:3001`

### Start Worker

In a separate terminal:

```bash
python start_worker.py
```

Or use RQ CLI:

```bash
rq worker translation --url $REDIS_URL
```

## API Endpoints

- `POST /api/translate` - Upload document for translation
- `GET /api/job/{jobId}` - Get job status
- `GET /api/download/{filename}` - Download translated file
- `GET /api/health` - Health check
- `WS /ws/{jobId}` - WebSocket for real-time updates

## Job Flow

1. Client uploads file via `POST /api/translate`
2. Server saves file and enqueues job to Redis
3. Worker picks up job from queue
4. Worker processes translation with progress updates
5. Worker saves result to Redis
6. Client gets result via WebSocket or polling `/api/job/{jobId}`
7. Client downloads via `/api/download/{filename}`

## Scaling

To scale workers, simply start multiple worker processes:

```bash
# Terminal 1
python start_worker.py

# Terminal 2
python start_worker.py

# Terminal 3
python start_worker.py
```

All workers will share the same Redis queue and process jobs in parallel.
