const { S3Client, GetObjectCommand, PutObjectCommand, ListObjectsV2Command, DeleteObjectsCommand } = require('@aws-sdk/client-s3');
const { Upload } = require('@aws-sdk/lib-storage');
const fs = require('fs');
const { Readable } = require('stream');

// Initialize S3 client
const s3Client = new S3Client({
  region: process.env.AWS_REGION || 'us-west-2',
  credentials: process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY ? {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  } : undefined // Will use default credential chain if not specified
});

const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'doctranslab';

/**
 * Upload a file to S3
 * @param {string} filePath - Local file path
 * @param {string} s3Key - S3 object key
 * @returns {Promise<string>} - S3 URL
 */
async function uploadToS3(filePath, s3Key) {
  const fileStream = fs.createReadStream(filePath);

  const upload = new Upload({
    client: s3Client,
    params: {
      Bucket: BUCKET_NAME,
      Key: s3Key,
      Body: fileStream,
    },
  });

  await upload.done();
  return `s3://${BUCKET_NAME}/${s3Key}`;
}

/**
 * Download a file from S3 to local filesystem
 * @param {string} s3Key - S3 object key
 * @param {string} localPath - Local file path to save to
 */
async function downloadFromS3(s3Key, localPath) {
  const command = new GetObjectCommand({
    Bucket: BUCKET_NAME,
    Key: s3Key,
  });

  const response = await s3Client.send(command);
  const writeStream = fs.createWriteStream(localPath);

  return new Promise((resolve, reject) => {
    response.Body.pipe(writeStream)
      .on('error', reject)
      .on('finish', resolve);
  });
}

/**
 * Get a readable stream from S3
 * @param {string} s3Key - S3 object key
 * @returns {Promise<Readable>} - Readable stream
 */
async function getS3Stream(s3Key) {
  const command = new GetObjectCommand({
    Bucket: BUCKET_NAME,
    Key: s3Key,
  });

  const response = await s3Client.send(command);
  return response.Body;
}

/**
 * Clean up old files from S3 (older than specified age)
 * @param {number} maxAgeMs - Maximum age in milliseconds
 * @returns {Promise<{deleted: number, errors: number}>} - Cleanup results
 */
async function cleanupOldFiles(maxAgeMs = 3600000) { // Default 1 hour
  const now = Date.now();
  const prefixes = ['uploads/', 'outputs/'];
  let totalDeleted = 0;
  let totalErrors = 0;

  for (const prefix of prefixes) {
    try {
      // List all objects with the prefix
      const listCommand = new ListObjectsV2Command({
        Bucket: BUCKET_NAME,
        Prefix: prefix,
      });

      const listResponse = await s3Client.send(listCommand);

      if (!listResponse.Contents || listResponse.Contents.length === 0) {
        continue;
      }

      // Filter files older than maxAgeMs
      const oldFiles = listResponse.Contents.filter(obj => {
        const fileAge = now - new Date(obj.LastModified).getTime();
        return fileAge > maxAgeMs;
      });

      if (oldFiles.length === 0) {
        continue;
      }

      // Delete old files in batches (S3 limit is 1000 per request)
      const batchSize = 1000;
      for (let i = 0; i < oldFiles.length; i += batchSize) {
        const batch = oldFiles.slice(i, i + batchSize);

        const deleteCommand = new DeleteObjectsCommand({
          Bucket: BUCKET_NAME,
          Delete: {
            Objects: batch.map(obj => ({ Key: obj.Key })),
            Quiet: false,
          },
        });

        const deleteResponse = await s3Client.send(deleteCommand);

        totalDeleted += deleteResponse.Deleted?.length || 0;
        totalErrors += deleteResponse.Errors?.length || 0;

        if (deleteResponse.Deleted?.length > 0) {
          console.log(`Deleted ${deleteResponse.Deleted.length} old files from ${prefix}`);
        }
        if (deleteResponse.Errors?.length > 0) {
          console.error(`Failed to delete ${deleteResponse.Errors.length} files from ${prefix}`);
        }
      }
    } catch (error) {
      console.error(`Error cleaning up ${prefix}:`, error);
      totalErrors++;
    }
  }

  return { deleted: totalDeleted, errors: totalErrors };
}

/**
 * Start automatic cleanup timer
 * @param {number} intervalMs - Cleanup interval in milliseconds
 * @param {number} maxAgeMs - Maximum file age in milliseconds
 */
function startAutoCleanup(intervalMs = 3600000, maxAgeMs = 3600000) {
  console.log(`Starting S3 auto-cleanup: running every ${intervalMs / 1000}s, deleting files older than ${maxAgeMs / 1000}s`);

  // Run cleanup immediately on start
  cleanupOldFiles(maxAgeMs).then(result => {
    console.log(`Initial cleanup completed: ${result.deleted} deleted, ${result.errors} errors`);
  }).catch(error => {
    console.error('Initial cleanup failed:', error);
  });

  // Schedule periodic cleanup
  const timer = setInterval(async () => {
    try {
      const result = await cleanupOldFiles(maxAgeMs);
      console.log(`Scheduled cleanup completed: ${result.deleted} deleted, ${result.errors} errors`);
    } catch (error) {
      console.error('Scheduled cleanup failed:', error);
    }
  }, intervalMs);

  return timer;
}

module.exports = {
  uploadToS3,
  downloadFromS3,
  getS3Stream,
  cleanupOldFiles,
  startAutoCleanup,
  BUCKET_NAME,
  s3Client
};
