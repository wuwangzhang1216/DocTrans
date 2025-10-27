"""
AWS S3 Helper Module
Handles file uploads, downloads, and lifecycle management for translated documents
"""

import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional
from datetime import datetime

class S3Helper:
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Initialize S3 helper

        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key (defaults to env var)
            aws_secret_access_key: AWS secret key (defaults to env var)
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id or os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3

        Args:
            local_path: Local file path
            s3_key: S3 object key (path in bucket)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine content type based on file extension
            ext = Path(local_path).suffix.lower()
            content_type_map = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.txt': 'text/plain',
                '.md': 'text/markdown'
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')

            # Upload file
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ContentDisposition': f'attachment; filename="{Path(local_path).name}"'
                }
            )

            print(f"[SUCCESS] Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True

        except ClientError as e:
            print(f"[ERROR] Failed to upload {local_path}: {e}")
            return False

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            print(f"[ERROR] Failed to generate presigned URL for {s3_key}: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3

        Args:
            s3_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            print(f"[SUCCESS] Deleted s3://{self.bucket_name}/{s3_key}")
            return True

        except ClientError as e:
            print(f"[ERROR] Failed to delete {s3_key}: {e}")
            return False

    def configure_lifecycle_policy(self, days_to_expire: int = 7):
        """
        Configure S3 bucket lifecycle policy to auto-delete old files

        Args:
            days_to_expire: Number of days after which files are deleted
        """
        try:
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'DeleteOldTranslatedDocs',
                        'Status': 'Enabled',
                        'Prefix': 'outputs/',  # Only delete files in outputs/ prefix
                        'Expiration': {
                            'Days': days_to_expire
                        }
                    }
                ]
            }

            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )

            print(f"[SUCCESS] Configured lifecycle policy: delete files after {days_to_expire} days")
            return True

        except ClientError as e:
            print(f"[ERROR] Failed to configure lifecycle policy: {e}")
            return False

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3

        Args:
            s3_key: S3 object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False


# Initialize global S3 helper instance
def get_s3_helper() -> Optional[S3Helper]:
    """
    Get S3 helper instance with configuration from environment variables

    Returns:
        S3Helper instance or None if not configured
    """
    bucket_name = os.environ.get('S3_BUCKET_NAME')

    if not bucket_name:
        print("[WARNING] S3_BUCKET_NAME not configured, using local storage")
        return None

    return S3Helper(
        bucket_name=bucket_name,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region=os.environ.get('AWS_REGION', 'us-east-1')
    )
