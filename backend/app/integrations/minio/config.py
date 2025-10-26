"""
MinIO Configuration
Storage settings for business card images and OCR results
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class MinIOConfig:
    """Configuration for MinIO storage"""
    
    # Connection settings
    endpoint: str = os.getenv('MINIO_ENDPOINT', 'minio:9000')
    access_key: str = os.getenv('MINIO_ROOT_USER', 'minioadmin')
    secret_key: str = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
    secure: bool = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
    
    # Bucket names
    images_bucket: str = 'business-cards'
    ocr_results_bucket: str = 'ocr-results'
    training_data_bucket: str = 'training-data'
    models_bucket: str = 'models'
    
    # Object settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: tuple = ('.jpg', '.jpeg', '.png', '.pdf', '.heic')
    
    # Retention settings
    images_expiry_days: Optional[int] = None  # None = no expiry
    ocr_results_expiry_days: Optional[int] = 90  # 3 months
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.endpoint:
            raise ValueError("MinIO endpoint is required")
        if not self.access_key or not self.secret_key:
            raise ValueError("MinIO credentials are required")


# Default config instance
DEFAULT_CONFIG = MinIOConfig()

# Bucket names for easy access
BUCKET_NAMES = {
    'images': 'business-cards',
    'ocr_results': 'ocr-results',
    'training_data': 'training-data',
    'models': 'models'
}


# Bucket policies
PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::{}/*"]
        }
    ]
}

PRIVATE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::{}/*"]
        }
    ]
}

