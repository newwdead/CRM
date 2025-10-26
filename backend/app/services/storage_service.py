"""
Storage Service
High-level service for managing image and OCR data storage
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .base import BaseService
from ..integrations.minio.client import MinIOClient
from ..integrations.minio.config import MinIOConfig

logger = logging.getLogger(__name__)


class StorageService(BaseService):
    """
    Storage service for business card images and OCR data
    
    Features:
    - Upload/download business card images
    - Store OCR processing results
    - Manage training data (Phase 6)
    - Integration with MinIO
    """
    
    def __init__(self, db: Session, minio_client: Optional[MinIOClient] = None):
        """
        Initialize storage service
        
        Args:
            db: SQLAlchemy database session
            minio_client: MinIO client instance (creates new if None)
        """
        super().__init__(db)
        self.minio = minio_client or MinIOClient()
    
    def save_business_card_image(
        self,
        contact_id: int,
        image_data: bytes,
        filename: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Save business card image to storage
        
        Args:
            contact_id: Contact ID
            image_data: Image bytes
            filename: Original filename
            metadata: Additional metadata
        
        Returns:
            Storage path if successful, None otherwise
        """
        if not self.minio.is_available():
            logger.warning("⚠️ MinIO not available, image not stored")
            return None
        
        try:
            object_name = self.minio.upload_image(
                image_data=image_data,
                contact_id=contact_id,
                filename=filename,
                metadata=metadata
            )
            
            if object_name:
                logger.info(f"✅ Saved image for contact {contact_id}")
            
            return object_name
            
        except Exception as e:
            logger.error(f"❌ Failed to save image: {e}", exc_info=True)
            return None
    
    def get_business_card_image(self, storage_path: str) -> Optional[bytes]:
        """
        Retrieve business card image from storage
        
        Args:
            storage_path: Object name in MinIO
        
        Returns:
            Image bytes if successful, None otherwise
        """
        if not self.minio.is_available():
            logger.warning("⚠️ MinIO not available")
            return None
        
        try:
            image_data = self.minio.download_image(storage_path)
            
            if image_data:
                logger.info(f"✅ Retrieved image: {storage_path}")
            
            return image_data
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve image: {e}", exc_info=True)
            return None
    
    def save_ocr_result(
        self,
        contact_id: int,
        ocr_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save OCR processing result
        
        Args:
            contact_id: Contact ID
            ocr_data: OCR result dictionary
        
        Returns:
            Storage path if successful, None otherwise
        """
        if not self.minio.is_available():
            logger.warning("⚠️ MinIO not available, OCR result not stored")
            return None
        
        try:
            object_name = self.minio.upload_ocr_result(
                contact_id=contact_id,
                ocr_data=ocr_data
            )
            
            if object_name:
                logger.info(f"✅ Saved OCR result for contact {contact_id}")
            
            return object_name
            
        except Exception as e:
            logger.error(f"❌ Failed to save OCR result: {e}", exc_info=True)
            return None
    
    def save_training_sample(
        self,
        image_data: bytes,
        annotations: Dict[str, Any],
        sample_id: str
    ) -> Optional[str]:
        """
        Save training sample for model fine-tuning (Phase 6)
        
        Args:
            image_data: Image bytes
            annotations: Label Studio annotations
            sample_id: Unique sample ID
        
        Returns:
            Storage path if successful, None otherwise
        """
        if not self.minio.is_available():
            logger.warning("⚠️ MinIO not available, training sample not stored")
            return None
        
        try:
            object_name = self.minio.upload_training_sample(
                image_data=image_data,
                annotations=annotations,
                sample_id=sample_id
            )
            
            if object_name:
                logger.info(f"✅ Saved training sample: {sample_id}")
            
            return object_name
            
        except Exception as e:
            logger.error(f"❌ Failed to save training sample: {e}", exc_info=True)
            return None
    
    def get_image_url(
        self,
        storage_path: str,
        expiry_hours: int = 1
    ) -> Optional[str]:
        """
        Get temporary presigned URL for image access
        
        Args:
            storage_path: Object name in MinIO
            expiry_hours: URL expiry time in hours
        
        Returns:
            Presigned URL if successful, None otherwise
        """
        if not self.minio.is_available():
            return None
        
        from datetime import timedelta
        
        try:
            url = self.minio.get_presigned_url(
                bucket_name=self.minio.config.images_bucket,
                object_name=storage_path,
                expiry=timedelta(hours=expiry_hours)
            )
            
            return url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate URL: {e}")
            return None
    
    def is_storage_available(self) -> bool:
        """Check if MinIO storage is available"""
        return self.minio.is_available()
