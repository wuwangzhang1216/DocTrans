const Bull = require('bull');
const path = require('path');
const fs = require('fs').promises;
const DocumentTranslator = require('./translator');
// Load .env from project root (parent of translate-web-app)
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// Redis configuration from environment variable
const redisUrl = process.env.REDIS_URL;

if (!redisUrl) {
  console.error('Error: REDIS_URL not found in environment variables');
  process.exit(1);
}

const redisConfig = {
  redis: redisUrl,
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

// Create queue
const translationQueue = new Bull('translation-queue', redisConfig);

// Initialize translator
const translator = new DocumentTranslator();

// Worker configuration
const WORKER_CONCURRENCY = parseInt(process.env.WORKER_CONCURRENCY) || 5;

// Check dependencies on startup
(async () => {
  try {
    console.log('Checking Python dependencies...');
    await translator.checkPythonDependencies();
    console.log('All dependencies ready');
  } catch (error) {
    console.error('Failed to initialize:', error.message);
    process.exit(1);
  }
})();

// Process translation jobs
translationQueue.process('translate-document', WORKER_CONCURRENCY, async (job) => {
  const {
    fileName,
    originalName,
    filePath,
    targetLanguage,
    sourceLanguage,
    userId
  } = job.data;

  // Fix the file path to use absolute path from backend
  const absoluteFilePath = path.resolve(__dirname, '..', 'backend', filePath);

  console.log(`Processing job ${job.id} - File: ${originalName}`);

  try {
    // Report initial progress
    await job.progress(5);

    // Generate output file path
    const fileExt = path.extname(originalName);
    const baseName = path.basename(originalName, fileExt);
    const outputFileName = `${baseName}_${targetLanguage}_${Date.now()}${fileExt}`;
    const outputPath = path.join(__dirname, '../backend/outputs', outputFileName);

    // Ensure output directory exists
    await fs.mkdir(path.dirname(outputPath), { recursive: true });

    // Report progress
    await job.progress(10);

    // Perform translation
    console.log(`Translating ${originalName} to ${targetLanguage}...`);

    await translator.translateDocument(
      absoluteFilePath,
      outputPath,
      targetLanguage,
      process.env.GEMINI_API_KEY,
      async (progress) => {
        // Map translation progress (10-90%)
        const mappedProgress = Math.min(90, 10 + Math.ceil(progress * 80));
        await job.progress(mappedProgress);
      }
    );

    // Verify output file exists
    await fs.access(outputPath);

    // Report completion
    await job.progress(95);

    // Clean up input file
    try {
      await fs.unlink(absoluteFilePath);
    } catch (error) {
      console.error('Error cleaning up input file:', error);
    }

    // Final progress
    await job.progress(100);

    console.log(`Job ${job.id} completed successfully`);

    return {
      success: true,
      outputFile: outputFileName,
      outputPath: outputPath,
      originalName: originalName,
      targetLanguage: targetLanguage,
      completedAt: new Date().toISOString()
    };

  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);

    // Clean up files on error
    try {
      await fs.unlink(filePath);
    } catch (cleanupError) {
      console.error('Cleanup error:', cleanupError);
    }

    throw error;
  }
});

// Queue event handlers
translationQueue.on('error', (error) => {
  console.error('Queue error:', error);
});

translationQueue.on('stalled', (job) => {
  console.warn(`Job ${job.id} stalled and will be retried`);
});

translationQueue.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result.outputFile);
});

translationQueue.on('failed', (job, error) => {
  console.error(`Job ${job.id} failed:`, error.message);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing queue...');
  await translationQueue.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, closing queue...');
  await translationQueue.close();
  process.exit(0);
});

console.log(`Worker started with concurrency: ${WORKER_CONCURRENCY}`);
console.log('Waiting for jobs...');
