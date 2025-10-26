"""
MinIO Client
Storage client for business card images and OCR data
"""
import logging
import io
import json
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error

from .config import MinIOConfig, PUBLIC_READ_POLICY, PRIVATE_POLICY

logger = logging.getLogger(__name__)


class MinIOClient:
    """
    MinIO client for object storage
    
    Features:
    - Image upload/download
    - OCR results storage
    - Training data management
    - Model versioning
    """
    
    def __init__(self, config: Optional[MinIOConfig] = None):
        """
        Initialize MinIO client
        
        Args:
            config: MinIO configuration (uses default if None)
        """
        self.config = config or MinIOConfig()
        self.client = None
        self._initialized = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MinIO client connection"""
        try:
            logger.info(f"🔌 Connecting to MinIO at {self.config.endpoint}...")
            
            self.client = Minio(
                self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure
            )
            
            # Test connection
            self.client.list_buckets()
            
            # Initialize buckets
            self._initialize_buckets()
            
            self._initialized = True
            logger.info("✅ MinIO client initialized successfully")
            
        except S3Error as e:
            logger.error(f"❌ MinIO S3 error: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO: {e}")
            self.client = None
    
    def _initialize_buckets(self):
        """Create required buckets if they don't exist"""
        buckets = [
            (self.config.images_bucket, True),  # (name, is_private)
            (self.config.ocr_results_bucket, True),
            (self.config.training_data_bucket, True),
            (self.config.models_bucket, True),
        ]
        
        for bucket_name, is_private in buckets:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"📦 Created bucket: {bucket_name}")
                    
                    # Set bucket policy
                    policy = PRIVATE_POLICY if is_private else PUBLIC_READ_POLICY
                    policy_str = json.dumps(policy).replace('{}', bucket_name)
                    self.client.set_bucket_policy(bucket_name, policy_str)
                else:
                    logger.info(f"📦 Bucket exists: {bucket_name}")
            except S3Error as e:
                logger.warning(f"⚠️ Could not create/configure bucket {bucket_name}: {e}")
    
    def is_available(self) -> bool:
        """Check if MinIO client is available"""
        return self._initialized and self.client is not None
    
    def upload_image(
        self,
        image_data: bytes,
        contact_id: int,
        filename: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Upload business card image
        
        Args:
            image_data: Image bytes
            contact_id: Contact ID
            filename: Original filename
            metadata: Additional metadata
        
        Returns:
            Object name (path) if successful, None otherwise
        """
        if not self.is_available():
            logger.error("❌ MinIO client not available")
            return None
        
        try:
            # Generate object name with contact_id prefix
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"contacts/{contact_id}/{timestamp}_{filename}"
            
            # Prepare metadata
            meta = metadata or {}
            meta.update({
                'contact_id': str(contact_id),
                'upload_time': datetime.now().isoformat(),
                'original_filename': filename
            })
            
            # Upload
            self.client.put_object(
                bucket_name=self.config.images_bucket,
                object_name=object_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type=self._get_content_type(filename),
                metadata=meta
            )
            
            logger.info(f"✅ Uploaded image: {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"❌ Failed to upload image: {e}")
            return None
    
    def download_image(self, object_name: str) -> Optional[bytes]:
        """
        Download business card image
        
        Args:
            object_name: Object name (path) in MinIO
        
        Returns:
            Image bytes if successful, None otherwise
        """
        if not self.is_available():
            logger.error("❌ MinIO client not available")
            return None
        
        try:
            response = self.client.get_object(
                bucket_name=self.config.images_bucket,
                object_name=object_name
            )
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"✅ Downloaded image: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"❌ Failed to download image: {e}")
            return None
    
    def upload_ocr_result(
        self,
        contact_id: int,
        ocr_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Upload OCR processing result
        
        Args:
            contact_id: Contact ID
            ocr_data: OCR result dictionary
        
        Returns:
            Object name if successful, None otherwise
        """
        if not self.is_available():
            logger.error("❌ MinIO client not available")
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"ocr/{contact_id}/{timestamp}_result.json"
            
            # Convert to JSON
            json_data = json.dumps(ocr_data, indent=2, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')
            
            # Upload
            self.client.put_object(
                bucket_name=self.config.ocr_results_bucket,
                object_name=object_name,
                data=io.BytesIO(json_bytes),
                length=len(json_bytes),
                content_type='application/json',
                metadata={'contact_id': str(contact_id)}
            )
            
            logger.info(f"✅ Uploaded OCR result: {object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"❌ Failed to upload OCR result: {e}")
            return None
    
    def upload_training_sample(
        self,
        image_data: bytes,
        annotations: Dict[str, Any],
        sample_id: str
    ) -> Optional[str]:
        """
        Upload training sample with annotations (for Phase 6)
        
        Args:
            image_data: Image bytes
            annotations: Label Studio annotations
            sample_id: Unique sample identifier
        
        Returns:
            Object name if successful, None otherwise
        """
        if not self.is_available():
            logger.error("❌ MinIO client not available")
            return None
        
        try:
            # Upload image
            image_name = f"training/{sample_id}.jpg"
            self.client.put_object(
                bucket_name=self.config.training_data_bucket,
                object_name=image_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type='image/jpeg'
            )
            
            # Upload annotations
            annotations_name = f"training/{sample_id}.json"
            json_data = json.dumps(annotations, indent=2, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')
            
            self.client.put_object(
                bucket_name=self.config.training_data_bucket,
                object_name=annotations_name,
                data=io.BytesIO(json_bytes),
                length=len(json_bytes),
                content_type='application/json'
            )
            
            logger.info(f"✅ Uploaded training sample: {sample_id}")
            return image_name
            
        except Exception as e:
            logger.error(f"❌ Failed to upload training sample: {e}")
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf',
            'heic': 'image/heic',
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """Delete an object from MinIO"""
        if not self.is_available():
            return False
        
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"🗑️  Deleted object: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"❌ Failed to delete object: {e}")
            return False
    
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expiry: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Get presigned URL for temporary access
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            expiry: URL expiry time
        
        Returns:
            Presigned URL if successful, None otherwise
        """
        if not self.is_available():
            return None
        
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expiry
            )
            return url
        except S3Error as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None

