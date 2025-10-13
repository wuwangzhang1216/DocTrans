const Bull = require('bull');
const path = require('path');
const fs = require('fs').promises;
const DocumentTranslator = require('./translator');
const { downloadFromS3, uploadToS3 } = require('./s3Helper');
// Load .env from project root (parent of translate-web-app)
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// Redis configuration from environment variable
const redisUrl = process.env.REDIS_URL;

if (!redisUrl) {
  console.error('Error: REDIS_URL not found in environment variables');
  process.exit(1);
}

// Parse Redis URL manually for Bull compatibility
const parseRedisUrl = (url) => {
  const urlObj = new URL(url);
  return {
    host: urlObj.hostname,
    port: parseInt(urlObj.port, 10),
    password: urlObj.password || undefined,
    db: urlObj.pathname ? parseInt(urlObj.pathname.slice(1), 10) || 0 : 0,
    tls: urlObj.protocol === 'rediss:' ? { rejectUnauthorized: false } : undefined
  };
};

const redisOptions = parseRedisUrl(redisUrl);
console.log('Worker Redis config:', { host: redisOptions.host, port: redisOptions.port, hasTLS: !!redisOptions.tls });

const redisConfig = {
  redis: redisOptions,
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
    s3Key,
    targetLanguage,
    sourceLanguage,
    userId
  } = job.data;

  console.log(`Processing job ${job.id} - File: ${originalName}`);
  console.log(`S3 Key: ${s3Key}`);

  // Create temp directories
  const tempDir = path.join(__dirname, 'temp');
  await fs.mkdir(tempDir, { recursive: true });

  const localInputPath = path.join(tempDir, `input_${job.id}_${fileName}`);
  const localOutputPath = path.join(tempDir, `output_${job.id}_${fileName}`);

  try {
    // Report initial progress
    await job.progress(5);

    // Download file from S3 to local temp
    console.log(`Downloading from S3: ${s3Key}`);
    await downloadFromS3(s3Key, localInputPath);
    console.log(`Downloaded to: ${localInputPath}`);

    // Report progress
    await job.progress(10);

    // Perform translation
    console.log(`Translating ${originalName} to ${targetLanguage}...`);

    const translationResult = await translator.translateDocument(
      localInputPath,
      localOutputPath,
      targetLanguage,
      process.env.GEMINI_API_KEY,
      async (progress) => {
        // Map translation progress (10-85%)
        const mappedProgress = Math.min(85, 10 + Math.ceil(progress * 75));
        await job.progress(mappedProgress);
      }
    );

    // Use actual output path from Python (for PDFs) or the expected path
    let actualOutputPath = localOutputPath;
    let actualOutputFileName = path.basename(localOutputPath);

    if (translationResult.paths) {
      if (translationResult.paths.mono) {
        // PDF translation returns mono and dual paths
        actualOutputPath = translationResult.paths.mono;
        actualOutputFileName = path.basename(actualOutputPath);
        console.log(`PDF translation complete. Mono: ${actualOutputPath}`);
        console.log(`Dual version: ${translationResult.paths.dual}`);
      } else if (translationResult.paths.output) {
        actualOutputPath = translationResult.paths.output;
        actualOutputFileName = path.basename(actualOutputPath);
      }
    }

    // Verify output file exists
    await fs.access(actualOutputPath);

    // Upload result to S3
    await job.progress(90);
    const outputS3Key = `outputs/${actualOutputFileName}`;
    console.log(`Uploading result to S3: ${outputS3Key}`);
    await uploadToS3(actualOutputPath, outputS3Key);
    console.log(`Result uploaded to S3: ${outputS3Key}`);

    // Handle dual path for PDFs
    if (translationResult.paths && translationResult.paths.dual) {
      const dualFileName = path.basename(translationResult.paths.dual);
      const dualS3Key = `outputs/${dualFileName}`;
      console.log(`Uploading dual version to S3: ${dualS3Key}`);
      await uploadToS3(translationResult.paths.dual, dualS3Key);
    }

    // Clean up local temp files
    try {
      await fs.unlink(localInputPath);
      await fs.unlink(actualOutputPath);
      if (translationResult.paths && translationResult.paths.dual) {
        await fs.unlink(translationResult.paths.dual);
      }
    } catch (error) {
      console.error('Error cleaning up temp files:', error);
    }

    // Final progress
    await job.progress(100);

    console.log(`Job ${job.id} completed successfully`);

    const result = {
      success: true,
      outputFile: actualOutputFileName,
      outputPath: actualOutputPath,
      originalName: originalName,
      targetLanguage: targetLanguage,
      completedAt: new Date().toISOString()
    };

    // Add dual path for PDFs if available
    if (translationResult.paths && translationResult.paths.dual) {
      result.dualOutputPath = translationResult.paths.dual;
      result.dualOutputFile = path.basename(translationResult.paths.dual);
    }

    return result;

  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);

    // Clean up temp files on error
    try {
      await fs.unlink(localInputPath);
    } catch (cleanupError) {
      console.error('Cleanup error:', cleanupError);
    }
    try {
      await fs.unlink(localOutputPath);
    } catch (cleanupError) {
      // Ignore if output doesn't exist
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
