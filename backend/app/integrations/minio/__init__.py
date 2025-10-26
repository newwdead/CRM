"""
MinIO Storage Integration
S3-compatible object storage for business card images and OCR results
"""
from .client import MinIOClient
from .config import MinIOConfig, BUCKET_NAMES

__all__ = [
    'MinIOClient',
    'MinIOConfig',
    'BUCKET_NAMES',
]

