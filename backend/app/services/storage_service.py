"""
Storage Service - MinIO object storage for images and models
"""
import os
import io
import logging
from typing import Optional

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in MinIO"""
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            logger.warning("MinIO client not available")
            self.client = None
            return
        
        try:
            self.client = Minio(
                os.getenv('MINIO_ENDPOINT', 'minio:9000'),
                access_key=os.getenv('MINIO_ROOT_USER', 'admin'),
                secret_key=os.getenv('MINIO_ROOT_PASSWORD', 'minio123456'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            self._ensure_buckets()
            logger.info("MinIO storage service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO: {e}")
            self.client = None
    
    def _ensure_buckets(self):
        """Create required buckets"""
        buckets = ['business-cards', 'trained-models', 'training-data']
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except Exception as e:
                logger.error(f"Failed to create bucket {bucket}: {e}")
    
    def upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        """Upload business card image"""
        if not self.client:
            return None
        try:
            self.client.put_object(
                'business-cards',
                filename,
                io.BytesIO(image_data),
                length=len(image_data),
                content_type='image/jpeg'
            )
            return f'business-cards/{filename}'
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            return None
    
    def get_image(self, object_path: str) -> Optional[bytes]:
        """Get image from MinIO"""
        if not self.client:
            return None
        try:
            bucket, filename = object_path.split('/', 1)
            response = self.client.get_object(bucket, filename)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error(f"Failed to get image: {e}")
            return None


def get_storage_service() -> StorageService:
    """Get storage service instance"""
    return StorageService()
