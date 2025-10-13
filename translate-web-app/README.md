# Document Translation Web Application

A scalable web application for translating documents while preserving formatting and layout. Built with Node.js, React, and Redis for high-performance background processing.

## Features

- 📄 **Multiple Format Support**: PDF, DOCX, PPTX, TXT, and Markdown files
- 🌍 **Multi-language Translation**: Support for 10+ target languages powered by Google Gemini
- ⚡ **High Performance**: Dynamic parallel processing with up to 256 workers
- 🔄 **Real-time Updates**: WebSocket-based progress tracking
- 📊 **Queue Management**: Redis-backed job queue for scalability
- 🔒 **Secure Processing**: Files are automatically cleaned up after processing
- 🎨 **Modern UI**: Built with shadcn/ui components
- 🧠 **Smart Allocation**: Dynamically allocates workers (up to 16 pages concurrently, 64 workers per page)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│    Redis    │
│  (Next.js)  │     │  (Express)  │     │   (Queue)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Worker 1  │     │   Worker N  │
                    │   (Bull)    │     │   (Bull)    │
                    └─────────────┘     └─────────────┘
```

## Prerequisites

- Node.js 18+
- Python 3.9+
- Docker & Docker Compose (optional)
- Google Gemini API Key

## Installation

### 1. Clone the repository

```bash
cd translate-doc
```

### 2. Install Python dependencies

```bash
pip install google-genai pymupdf python-pptx python-docx pdfplumber reportlab python-dotenv
```

### 3. Set up environment variables

Copy `.env.example` to `.env` in the **project root**:

```bash
cp .env.example .env
```

Then update the `.env` file with your credentials:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Redis Configuration
REDIS_URL=rediss://...  # Your Redis URL

# Server Configuration
PORT=3001
NODE_ENV=development

# Worker Configuration
WORKER_CONCURRENCY=5
JOB_TIMEOUT=600000
```

**Note**: Both backend and worker will automatically load this root `.env` file.

### 4. Install Node.js dependencies

```bash
# Backend
cd translate-web-app/backend
npm install

# Worker
cd ../worker
npm install

# Frontend
cd ../frontend
npm install
```

## Running the Application

### Development Mode

Start each service in separate terminals:

```bash
# Terminal 1: Backend server
cd translate-web-app/backend
npm run dev

# Terminal 2: Worker service
cd translate-web-app/worker
npm start

# Terminal 3: Frontend
cd translate-web-app/frontend
npm run dev
```

Access the application at `http://localhost:3000`

### Production Mode (Docker)

1. Ensure the `.env` file in the **project root** is properly configured (docker-compose will mount it)

2. Build and start all services:

```bash
cd translate-web-app
docker-compose up --build
```

Access the application at `http://localhost`

**Note**: Docker containers will use the `.env` file from the project root, which is mounted read-only into the containers.

## API Endpoints

### Backend API (Port 3001)

- `POST /api/translate` - Upload file for translation
- `GET /api/job/:jobId` - Get job status
- `GET /api/download/:fileName` - Download translated file
- `GET /api/stats` - Get queue statistics
- `GET /api/jobs` - List recent jobs
- `DELETE /api/job/:jobId` - Cancel a job

### WebSocket Events

- `subscribe-job` - Subscribe to job updates
- `unsubscribe-job` - Unsubscribe from job updates
- `job-update` - Receive job status updates

## Configuration

### Worker Concurrency

Adjust the number of concurrent translation jobs in `.env`:

```env
WORKER_CONCURRENCY=5
```

### Scaling Workers

To scale workers in Docker:

```bash
docker-compose up --scale worker=3
```

## File Size Limits

- Maximum file size: 10MB (configurable in `.env`)
- Supported formats: PDF, DOCX, PPTX, TXT, MD

## Security Considerations

1. **API Key Security**: Never commit your Gemini API key to version control
2. **File Cleanup**: Uploaded and translated files are automatically deleted after processing
3. **Redis Security**: Use TLS-enabled Redis connection (rediss://)
4. **Rate Limiting**: Consider implementing rate limiting for production use

## Monitoring

### Queue Statistics

View real-time queue statistics at the `/api/stats` endpoint:

```json
{
  "queue": {
    "waiting": 5,
    "active": 2,
    "completed": 150,
    "failed": 3,
    "total": 160
  }
}
```

### Job Status

Track individual job progress through WebSocket updates or polling the `/api/job/:jobId` endpoint.

## Troubleshooting

### Python Dependencies

If translation fails, ensure all Python packages are installed:

```bash
pip install -r requirements.txt
```

### Redis Connection

Test Redis connection:

```bash
redis-cli -u $REDIS_URL ping
```

### Worker Logs

Check worker logs for translation errors:

```bash
docker-compose logs worker
```

## Performance Optimization

1. **Dynamic Parallel Processing**: The system uses up to 256 workers with smart allocation:
   - **PDF/PPTX**: Up to 16 pages/slides concurrently, 64 workers per page
   - **DOCX**: Dynamic allocation based on document size
   - **Markdown**: Smart code block detection, parallel text block translation
2. **Redis Queue**: Efficient job distribution across multiple workers
3. **WebSocket**: Real-time updates without polling overhead
4. **Google Gemini AI**: Fast and accurate translation with gemini-2.0-flash-lite-preview model

## Deployment

### Heroku Deployment

For deploying to Heroku with AWS S3 storage, see the comprehensive [DEPLOYMENT.md](./DEPLOYMENT.md) guide.

**Quick Links**:
- [Quick Start Guide](./DEPLOYMENT.md#quick-start)
- [Manual Deployment](./DEPLOYMENT.md#manual-deployment)
- [AWS S3 Configuration](./DEPLOYMENT.md#aws-s3-configuration)
- [Troubleshooting](./DEPLOYMENT.md#troubleshooting)

**What's Included**:
- ✅ Backend + Worker deployment to Heroku
- ✅ Frontend deployment to Heroku
- ✅ AWS S3 integration for persistent file storage
- ✅ Redis queue setup
- ✅ Environment variable configuration
- ✅ Scaling and monitoring guides

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.