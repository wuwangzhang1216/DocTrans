const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');
const Bull = require('bull');
const { Server } = require('socket.io');
const http = require('http');
// Load .env from project root (parent of translate-web-app)
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    methods: ['GET', 'POST']
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Ensure directories exist
const ensureDirectories = async () => {
  const dirs = ['./uploads', './outputs', './public'];
  for (const dir of dirs) {
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (error) {
      console.error(`Error creating directory ${dir}:`, error);
    }
  }
};

ensureDirectories();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = './uploads';
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    // Ensure proper UTF-8 encoding for the original filename
    const originalName = Buffer.from(file.originalname, 'latin1').toString('utf8');
    const uniqueName = `${uuidv4()}_${originalName}`;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 10485760 // 10MB default
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['.pdf', '.docx', '.pptx', '.txt', '.md'];
    // Fix UTF-8 encoding for filename
    const originalName = Buffer.from(file.originalname, 'latin1').toString('utf8');
    const ext = path.extname(originalName).toLowerCase();
    if (allowedTypes.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${ext} not supported`));
    }
  }
});

// Redis connection configuration from environment variable
const redisUrl = process.env.REDIS_URL;

if (!redisUrl) {
  console.error('Error: REDIS_URL not found in environment variables');
  process.exit(1);
}

const redisConfig = {
  redis: {
    port: process.env.REDIS_PORT || 6379,
    host: process.env.REDIS_HOST,
    password: process.env.REDIS_PASSWORD,
    tls: {
      rejectUnauthorized: false
    },
    maxRetriesPerRequest: 3,
    enableReadyCheck: false,
    retryStrategy: (times) => {
      if (times > 3) {
        console.error('Redis connection failed after 3 retries');
        return null;
      }
      return Math.min(times * 100, 3000);
    }
  },
  defaultJobOptions: {
    removeOnComplete: 100,
    removeOnFail: 100,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  }
};

// Create Bull queue for translation jobs
const translationQueue = new Bull('translation-queue', redisConfig);

// Job status tracking
const jobStatuses = new Map();

const statusPriority = {
  queued: 0,
  processing: 1,
  completed: 2,
  failed: 3
};

const clampProgress = (value) => {
  if (typeof value === 'object' && value !== null) {
    if (typeof value.progress === 'number') {
      value = value.progress;
    } else if (typeof value.value === 'number') {
      value = value.value;
    }
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.min(100, Math.max(0, Math.round(numeric)));
};

const normalizeQueueState = (state) => {
  switch (state) {
    case 'completed':
      return 'completed';
    case 'failed':
      return 'failed';
    case 'active':
      return 'processing';
    default:
      return 'queued';
  }
};

const defaultMessageForStatus = (status, progress) => {
  switch (status) {
    case 'processing':
      return `Processing: ${progress}%`;
    case 'completed':
      return 'Translation completed successfully';
    case 'failed':
      return 'Translation failed';
    default:
      return 'Job queued for processing';
  }
};

// Socket.io connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('subscribe-job', (jobId) => {
    socket.join(`job-${jobId}`);

    // Send current status if available
    if (jobStatuses.has(jobId)) {
      socket.emit('job-update', {
        jobId,
        ...jobStatuses.get(jobId)
      });
    }
  });

  socket.on('unsubscribe-job', (jobId) => {
    socket.leave(`job-${jobId}`);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Queue event listeners
translationQueue.on('progress', (job, progress) => {
  const normalizedProgress = clampProgress(progress);
  const status = {
    status: 'processing',
    progress: normalizedProgress,
    message: defaultMessageForStatus('processing', normalizedProgress)
  };
  jobStatuses.set(job.id.toString(), status);
  io.to(`job-${job.id}`).emit('job-update', {
    jobId: job.id,
    ...status
  });
});

translationQueue.on('completed', async (job, result) => {
  const status = {
    status: 'completed',
    progress: 100,
    outputFile: result?.outputFile,
    message: defaultMessageForStatus('completed', 100)
  };
  jobStatuses.set(job.id.toString(), status);
  io.to(`job-${job.id}`).emit('job-update', {
    jobId: job.id,
    ...status
  });
});

translationQueue.on('failed', async (job, err) => {
  const status = {
    status: 'failed',
    progress: 0,
    error: err.message,
    message: defaultMessageForStatus('failed', 0)
  };
  jobStatuses.set(job.id.toString(), status);
  io.to(`job-${job.id}`).emit('job-update', {
    jobId: job.id,
    ...status
  });
});

// API Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Upload and translate file
app.post('/api/translate', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { targetLanguage = 'Chinese', sourceLanguage = 'auto' } = req.body;

    // Create job data
    // Fix UTF-8 encoding for the original filename
    const originalName = Buffer.from(req.file.originalname, 'latin1').toString('utf8');

    const jobData = {
      fileName: req.file.filename,
      originalName: originalName,
      filePath: req.file.path,
      targetLanguage,
      sourceLanguage,
      uploadTime: new Date().toISOString(),
      userId: req.headers['x-user-id'] || 'anonymous'
    };

    // Add job to queue
    const job = await translationQueue.add('translate-document', jobData, {
      timeout: parseInt(process.env.JOB_TIMEOUT) || 600000 // 10 minutes default
    });

    // Initialize job status
    jobStatuses.set(job.id.toString(), {
      status: 'queued',
      progress: 0,
      message: 'Job queued for processing'
    });

    res.json({
      success: true,
      jobId: job.id,
      message: 'File uploaded and queued for translation'
    });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get job status
app.get('/api/job/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    const cachedStatus = jobStatuses.get(jobId) || null;
    const job = await translationQueue.getJob(jobId);

    if (!job) {
      if (cachedStatus) {
        return res.json({
          jobId,
          ...cachedStatus
        });
      }
      return res.status(404).json({ error: 'Job not found' });
    }

    const [queueStateRaw, queueProgressRaw] = await Promise.all([
      job.getState(),
      job.progress()
    ]);

    const queueStatus = normalizeQueueState(queueStateRaw);
    let progress = clampProgress(queueProgressRaw);

    if (cachedStatus && typeof cachedStatus.progress === 'number') {
      progress = Math.max(progress, clampProgress(cachedStatus.progress));
    }

    let status = queueStatus;
    if (cachedStatus && cachedStatus.status) {
      const cachedPriority = statusPriority[cachedStatus.status] ?? 0;
      const queuePriority = statusPriority[queueStatus] ?? 0;
      status = cachedPriority >= queuePriority ? cachedStatus.status : queueStatus;
    }

    if (status === 'completed') {
      progress = 100;
    } else if (status === 'failed') {
      progress = 0;
    }

    let outputFile = cachedStatus?.outputFile;
    if (!outputFile && status === 'completed') {
      const result = job.returnvalue;
      if (result && result.outputFile) {
        outputFile = result.outputFile;
      }
    }

    let error = cachedStatus?.error;
    if (!error && status === 'failed') {
      error = job.failedReason || (Array.isArray(job.stacktrace) && job.stacktrace.length ? job.stacktrace[0] : undefined);
    }

    let message = cachedStatus?.message;
    if (!message || cachedStatus?.status !== status) {
      message = defaultMessageForStatus(status, progress);
    }

    const responsePayload = {
      jobId,
      status,
      progress,
      message,
      outputFile,
      error
    };

    jobStatuses.set(jobId, {
      status: responsePayload.status,
      progress: responsePayload.progress,
      message: responsePayload.message,
      outputFile: responsePayload.outputFile,
      error: responsePayload.error
    });

    res.json(responsePayload);

  } catch (error) {
    console.error('Get job error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Download translated file
app.get('/api/download/:fileName', async (req, res) => {
  try {
    const { fileName } = req.params;
    const filePath = path.join('./outputs', fileName);

    // Check if file exists
    await fs.access(filePath);

    // Properly encode the filename for UTF-8 characters
    const encodedFileName = encodeURIComponent(fileName);

    // Set proper headers for UTF-8 filename support
    res.setHeader('Content-Type', 'application/octet-stream');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename*=UTF-8''${encodedFileName}`
    );

    // Send the file
    res.sendFile(path.resolve(filePath), (err) => {
      if (err) {
        console.error('Download error:', err);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Error downloading file' });
        }
      }
    });

  } catch (error) {
    console.error('Download error:', error);
    res.status(404).json({ error: 'File not found' });
  }
});

// Get queue statistics
app.get('/api/stats', async (req, res) => {
  try {
    const [waiting, active, completed, failed] = await Promise.all([
      translationQueue.getWaitingCount(),
      translationQueue.getActiveCount(),
      translationQueue.getCompletedCount(),
      translationQueue.getFailedCount()
    ]);

    res.json({
      queue: {
        waiting,
        active,
        completed,
        failed,
        total: waiting + active + completed + failed
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Stats error:', error);
    res.status(500).json({ error: error.message });
  }
});

// List recent jobs
app.get('/api/jobs', async (req, res) => {
  try {
    const { status = 'all', limit = 20, offset = 0 } = req.query;

    let jobs = [];

    if (status === 'all' || status === 'completed') {
      const completed = await translationQueue.getCompleted(limit, offset);
      jobs = jobs.concat(completed);
    }

    if (status === 'all' || status === 'active') {
      const active = await translationQueue.getActive();
      jobs = jobs.concat(active);
    }

    if (status === 'all' || status === 'waiting') {
      const waiting = await translationQueue.getWaiting(0, limit);
      jobs = jobs.concat(waiting);
    }

    if (status === 'all' || status === 'failed') {
      const failed = await translationQueue.getFailed(0, limit);
      jobs = jobs.concat(failed);
    }

    const jobList = await Promise.all(jobs.map(async (job) => ({
      id: job.id,
      status: await job.getState(),
      progress: job.progress(),
      data: {
        originalName: job.data.originalName,
        targetLanguage: job.data.targetLanguage,
        uploadTime: job.data.uploadTime
      },
      createdAt: new Date(job.timestamp).toISOString()
    })));

    res.json(jobList);

  } catch (error) {
    console.error('List jobs error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Cancel a job
app.delete('/api/job/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    const job = await translationQueue.getJob(jobId);
    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    await job.remove();
    jobStatuses.delete(jobId);

    res.json({ success: true, message: 'Job cancelled' });

  } catch (error) {
    console.error('Cancel job error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Clean up old jobs
app.post('/api/cleanup', async (req, res) => {
  try {
    const grace = req.body.grace || 3600000; // 1 hour default

    await translationQueue.clean(grace, 'completed');
    await translationQueue.clean(grace, 'failed');

    res.json({ success: true, message: 'Cleanup completed' });

  } catch (error) {
    console.error('Cleanup error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File too large' });
    }
  }

  console.error('Server error:', error);
  res.status(500).json({ error: error.message || 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`WebSocket server ready for connections`);
});