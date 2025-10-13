const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
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

module.exports = {
  uploadToS3,
  downloadFromS3,
  getS3Stream,
  BUCKET_NAME,
  s3Client
};
