"""AWS S3 integration for uploading PDFs and outputs."""
import os
import logging
from pathlib import Path
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSStorage:
    """Handles AWS S3 uploads for PDFs and outputs."""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1', enabled: bool = True):
        """Initialize AWS storage.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            enabled: Whether AWS integration is enabled
        """
        self.logger = logging.getLogger(__name__)
        self.bucket_name = bucket_name
        self.region = region
        self.enabled = enabled and BOTO3_AVAILABLE
        
        if not BOTO3_AVAILABLE:
            self.logger.warning("boto3 not available - AWS integration disabled")
            self.enabled = False
            return
        
        if not self.enabled:
            self.logger.info("AWS integration disabled in config")
            return
        
        try:
            self.s3_client = boto3.client('s3', region_name=region)
            self.logger.info(f"AWS S3 client initialized for bucket: {bucket_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS S3 client: {e}")
            self.enabled = False
    
    def upload_file(self, local_path: str, s3_key: Optional[str] = None) -> bool:
        """Upload a file to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key (defaults to filename)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            self.logger.debug("AWS upload skipped (disabled)")
            return False
        
        if not os.path.exists(local_path):
            self.logger.error(f"File not found: {local_path}")
            return False
        
        if s3_key is None:
            s3_key = Path(local_path).name
        
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            self.logger.info(f"Uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return True
        except NoCredentialsError:
            self.logger.error("AWS credentials not found. Please configure AWS credentials.")
            self.logger.error("Run: aws configure")
            return False
        except ClientError as e:
            self.logger.error(f"Failed to upload to S3: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error uploading to S3: {e}")
            return False
    
    def upload_directory(self, local_dir: str, s3_prefix: str = "") -> int:
        """Upload all files in a directory to S3.
        
        Args:
            local_dir: Local directory path
            s3_prefix: S3 key prefix (folder)
            
        Returns:
            Number of files successfully uploaded
        """
        if not self.enabled:
            return 0
        
        if not os.path.isdir(local_dir):
            self.logger.error(f"Directory not found: {local_dir}")
            return 0
        
        uploaded_count = 0
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_dir)
                s3_key = os.path.join(s3_prefix, relative_path).replace('\\', '/')
                
                if self.upload_file(local_path, s3_key):
                    uploaded_count += 1
        
        self.logger.info(f"Uploaded {uploaded_count} files from {local_dir}")
        return uploaded_count
    
    def get_s3_uri(self, s3_key: str) -> str:
        """Get S3 URI for a key.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            S3 URI string
        """
        return f"s3://{self.bucket_name}/{s3_key}"
    
    def get_https_url(self, s3_key: str) -> str:
        """Get HTTPS URL for a key.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            HTTPS URL string
        """
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
