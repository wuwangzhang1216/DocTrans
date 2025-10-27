"""
Configure S3 Bucket Lifecycle Policy
Run this script once to set up automatic deletion of old files
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from s3_helper import get_s3_helper


def configure_lifecycle(days_to_expire: int = 7):
    """
    Configure S3 bucket to automatically delete files after N days

    Args:
        days_to_expire: Number of days to keep files (default: 7)
    """
    s3_helper = get_s3_helper()

    if not s3_helper:
        print("[ERROR] S3 is not configured. Please check your .env file.")
        print("  Required variables: S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        return False

    print(f"Configuring S3 lifecycle policy for bucket: {s3_helper.bucket_name}")
    print(f"Files in 'outputs/' will be automatically deleted after {days_to_expire} days")

    success = s3_helper.configure_lifecycle_policy(days_to_expire)

    if success:
        print("\n[SUCCESS] Lifecycle policy configured successfully!")
        print(f"  - Files older than {days_to_expire} days will be automatically deleted")
        print(f"  - Policy applies to objects with prefix 'outputs/'")
        return True
    else:
        print("\n[ERROR] Failed to configure lifecycle policy")
        print("  Please check your AWS credentials and bucket permissions")
        return False


if __name__ == "__main__":
    # Default: delete files after 7 days
    days = 7

    # Allow custom days via command line argument
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Usage: python configure_s3_lifecycle.py [days_to_expire]")
            print("Example: python configure_s3_lifecycle.py 14  # Delete after 14 days")
            sys.exit(1)

    configure_lifecycle(days)
