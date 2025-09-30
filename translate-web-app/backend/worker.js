const Bull = require('bull');
const path = require('path');
const fs = require('fs').promises;
const { spawn } = require('child_process');

// Load .env from project root
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

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

// Create Bull queue
const translationQueue = new Bull('translation-queue', redisConfig);

// Process translation jobs
translationQueue.process('translate-document', async (job) => {
  console.log(`Processing job ${job.id}:`, job.data);

  const { filePath, targetLanguage, sourceLanguage, originalName } = job.data;

  try {
    // Update progress
    await job.progress(10);

    // Prepare output filename
    const ext = path.extname(originalName);
    const baseName = path.basename(originalName, ext);
    const outputFileName = `translated_${baseName}${ext}`;
    const outputPath = path.join(__dirname, 'outputs', outputFileName);

    // Ensure output directory exists
    await fs.mkdir(path.join(__dirname, 'outputs'), { recursive: true });

    await job.progress(20);

    // Convert relative path to absolute path
    const absoluteFilePath = path.isAbsolute(filePath)
      ? filePath
      : path.join(__dirname, filePath);

    // Path to the Python script (in the project root)
    const pythonScript = path.join(__dirname, '../../translate_doc.py');

    // Check if Python script exists
    try {
      await fs.access(pythonScript);
    } catch (error) {
      throw new Error(`Python script not found at ${pythonScript}`);
    }

    await job.progress(30);

    // Spawn Python process to run translation
    const result = await new Promise((resolve, reject) => {
      const args = [
        pythonScript,
        absoluteFilePath,
        '-o', outputPath,
        '-t', targetLanguage
      ];

      if (sourceLanguage && sourceLanguage !== 'auto') {
        args.push('-s', sourceLanguage);
      }

      console.log(`Running: python ${args.join(' ')}`);

      const pythonProcess = spawn('python', args);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        console.log(`Python stdout: ${output}`);

        // Try to parse progress from output
        const progressMatch = output.match(/(\d+)%/);
        if (progressMatch) {
          const progress = parseInt(progressMatch[1]);
          job.progress(Math.min(90, 30 + (progress * 0.6))); // Map 0-100% to 30-90%
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        const output = data.toString();
        stderr += output;
        console.error(`Python stderr: ${output}`);
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(`Python process exited with code ${code}. Error: ${stderr}`));
        }
      });

      pythonProcess.on('error', (error) => {
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });
    });

    await job.progress(95);

    // Verify output file exists
    try {
      await fs.access(outputPath);
    } catch (error) {
      throw new Error(`Output file was not created: ${outputPath}`);
    }

    await job.progress(100);

    console.log(`Job ${job.id} completed successfully`);

    return {
      outputFile: outputFileName,
      message: 'Translation completed successfully'
    };

  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);
    throw error;
  }
});

// Queue event listeners
translationQueue.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

translationQueue.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err.message);
});

translationQueue.on('progress', (job, progress) => {
  console.log(`Job ${job.id} progress: ${progress}%`);
});

console.log('Worker started, waiting for jobs...');
console.log('Connected to Redis:', redisUrl);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing worker...');
  await translationQueue.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, closing worker...');
  await translationQueue.close();
  process.exit(0);
});