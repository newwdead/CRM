"""
Celery tasks for async processing
"""
import os
import io
import uuid
import json
import time
import zipfile
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from celery import Task
from sqlalchemy.orm import Session

from .celery_app import celery_app
from .database import SessionLocal
from .models import Contact
from .integrations.ocr.providers import OCRManager  # Old OCR v1.0
from .integrations.ocr.providers_v2 import OCRManagerV2  # NEW OCR v2.0
from .integrations.ocr.utils import enhance_ocr_result
from .core import qr as qr_utils
from .integrations.ocr.image_utils import downscale_image_bytes, create_thumbnail
from .services.layoutlm_service import get_layoutlm_service
from .services.validator_service import ValidatorService
from .services.storage_service import StorageService
from .integrations.label_studio.service import LabelStudioService
from .integrations.label_studio.active_learning import ActiveLearningService
from PIL import Image

logger = logging.getLogger(__name__)

# Initialize OCR managers (v1.0 fallback + v2.0 primary)
ocr_manager_v1 = OCRManager()  # Old Tesseract-based (fallback)
ocr_manager_v2 = OCRManagerV2(enable_layoutlm=True)  # NEW PaddleOCR + LayoutLMv3
layoutlm_service = get_layoutlm_service()

# Initialize Label Studio and Active Learning
label_studio_service = LabelStudioService()
active_learning_service = ActiveLearningService()

# Use v2.0 by default
ocr_manager = ocr_manager_v2  # PRIMARY: Use OCR v2.0 for all new cards

logger.info("🚀 OCR v2.0 initialized: PaddleOCR + LayoutLMv3 + Validator + Label Studio ready")


def _process_card_sync(
    image_data: bytes,
    filename: str,
    provider: str = 'auto',
    user_id: int = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Synchronous version of process_single_card for use in batch processing.
    Does not use Celery task context.
    """
    _db = db if db else SessionLocal()
    try:
        logger.info(f"Processing card (sync): {filename}")
        
        # Save file
        file_ext = os.path.splitext(filename)[1].lower()
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join('/app/uploads', safe_name)
        
        with open(save_path, 'wb') as f:
            f.write(image_data)
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_path)
        
        # Try QR code first
        qr_data = qr_utils.process_image_with_qr(image_data)
        
        data = None
        raw_json = None
        recognition_method = None
        
        if qr_data and any(qr_data.values()):
            # QR code found
            data = qr_data
            recognition_method = 'qr_code'
            raw_json = json.dumps({
                'method': 'qr_code',
                'data': qr_data
            }, ensure_ascii=False)
            logger.info(f"QR code extracted from {filename}")
        else:
            # Check OCR version setting
            from .core.utils import get_setting
            ocr_version = get_setting(_db, "ocr_version", "v2.0")
            
            # Increased limit for high-res business cards
            ocr_input = downscale_image_bytes(image_data, max_size=6000)
            
            # Determine provider
            provider_name = None if provider == 'auto' else provider
            
            # Run OCR based on version setting
            if ocr_version == "v2.0":
                # Use OCR v2.0 (PaddleOCR + LayoutLMv3)
                logger.info(f"🚀 Using OCR v2.0 for {filename}")
                try:
                    ocr_result = ocr_manager_v2.recognize(
                        image_data=ocr_input,
                        provider_name=provider_name,
                        use_layout=True,  # Enable LayoutLMv3 AI classification
                        filename=filename
                    )
                    
                    # Validate and auto-correct with ValidatorService
                    validator = ValidatorService(_db)
                    ocr_result = validator.validate_ocr_result(
                        ocr_result, 
                        auto_correct=True
                    )
                except Exception as v2_error:
                    logger.warning(f"⚠️ OCR v2.0 failed, falling back to v1.0: {v2_error}")
                    ocr_result = ocr_manager_v1.recognize(
                        ocr_input,
                        filename=filename,
                        preferred_provider=provider_name
                    )
            else:
                # Use OCR v1.0 (Tesseract)
                logger.info(f"🔧 Using OCR v1.0 for {filename}")
                ocr_result = ocr_manager_v1.recognize(
                    ocr_input,
                    filename=filename,
                    preferred_provider=provider_name
                )
            
            # Process OCR result (works for both v1.0 and v2.0)
            data = ocr_result['data']
            recognition_method = ocr_result['provider']
            
            # Add version info and LayoutLMv3 info if v2.0 was used
            if ocr_version == "v2.0" and ocr_result.get('layoutlm_used'):
                recognition_method += " v2.0 + LayoutLMv3"
            elif ocr_version == "v2.0":
                recognition_method += " v2.0"
            else:
                recognition_method += " v1.0"
            
            # Convert blocks to dict if they exist
            blocks_data = []
            if 'blocks' in ocr_result and ocr_result['blocks']:
                for block in ocr_result['blocks']:
                    if hasattr(block, 'to_dict'):
                        blocks_data.append(block.to_dict())
                    elif isinstance(block, dict):
                        blocks_data.append(block)
            
            # Get image dimensions for blocks
            image_size = ocr_result.get('image_size', (0, 0))
            
            raw_json = json.dumps({
                'method': f'ocr_{ocr_version}',
                'provider': ocr_result['provider'],
                'confidence': ocr_result.get('confidence', 0),
                'raw_text': ocr_result.get('text', ''),
                'block_count': ocr_result.get('block_count', 0),
                'layoutlm_used': ocr_result.get('layoutlm_used', False),
                'layoutlm_confidence': ocr_result.get('layoutlm_confidence'),
                'validation': ocr_result.get('validation', {}),
                'blocks': blocks_data,  # ✅ Add blocks for editor
                'image_width': image_size[0],
                'image_height': image_size[1],
            }, ensure_ascii=False)
            
            logger.info(
                f"✅ OCR {ocr_version} completed for {filename}: "
                f"{recognition_method}, confidence: {ocr_result.get('confidence', 0):.2f}"
            )
        
        # Validate results
        if not data or not any(data.values()):
            raise Exception("No data could be extracted from the image")
        
        # Enhance data
        data = enhance_ocr_result(data)
        
        # Attach metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        
        # Save to database
        contact = Contact(**data)
        _db.add(contact)
        _db.commit()
        _db.refresh(contact)
        
        logger.info(f"Contact created: {contact.id} ({filename})")
        
        return {
            'success': True,
            'contact_id': contact.id,
            'uid': contact.uid,
            'filename': filename,
            'recognition_method': recognition_method
        }
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")
        # Clean up file on error
        if 'save_path' in locals() and os.path.exists(save_path):
            os.remove(save_path)
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }
    finally:
        if db is None and _db:
            _db.close()


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.process_single_card')
def process_single_card(
    self,
    image_data: bytes,
    filename: str,
    provider: str = 'auto',
    user_id: int = None
) -> Dict[str, Any]:
    """
    Process a single business card image.
    
    Args:
        image_data: Binary image data
        filename: Original filename
        provider: OCR provider ('auto', 'tesseract', 'parsio', 'google')
        user_id: User ID for audit
        
    Returns:
        dict with contact data or error
    """
    try:
        logger.info(f"✅ CELERY TASK STARTED: process_single_card for {filename} (data size: {len(image_data)} bytes)")
        logger.info(f"Processing card: {filename}")
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Scanning image...'})
        
        # Save file
        file_ext = os.path.splitext(filename)[1].lower()
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join('/app/uploads', safe_name)
        
        with open(save_path, 'wb') as f:
            f.write(image_data)
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_path)
        
        # Try QR code first
        self.update_state(state='PROCESSING', meta={'status': 'Looking for QR code...'})
        qr_data = qr_utils.process_image_with_qr(image_data)
        
        data = None
        raw_json = None
        recognition_method = None
        
        if qr_data and any(qr_data.values()):
            # QR code found
            data = qr_data
            recognition_method = 'qr_code'
            raw_json = json.dumps({
                'method': 'qr_code',
                'data': qr_data
            }, ensure_ascii=False)
            logger.info(f"QR code extracted from {filename}")
        else:
            # Fallback to OCR
            self.update_state(state='PROCESSING', meta={'status': 'Running OCR...'})
            
            # Check OCR version setting
            from .core.utils import get_setting
            ocr_version = get_setting(_db, "ocr_version", "v2.0")
            
            # Increased limit for high-res business cards
            ocr_input = downscale_image_bytes(image_data, max_side=6000)
            preferred = None if provider == 'auto' else provider
            
            # Run OCR based on version setting
            if ocr_version == "v2.0":
                logger.info(f"🚀 Using OCR v2.0 for {filename}")
                try:
                    ocr_result = ocr_manager_v2.recognize(
                        image_data=ocr_input,
                        provider_name=preferred,
                        use_layout=True,
                        filename=filename
                    )
                    validator = ValidatorService(_db)
                    ocr_result = validator.validate_ocr_result(ocr_result, auto_correct=True)
                except Exception as v2_error:
                    logger.warning(f"⚠️ OCR v2.0 failed, falling back to v1.0: {v2_error}")
                    ocr_result = ocr_manager_v1.recognize(
                        ocr_input,
                        filename=filename,
                        preferred_provider=preferred
                    )
            else:
                logger.info(f"🔧 Using OCR v1.0 for {filename}")
                ocr_result = ocr_manager_v1.recognize(
                    ocr_input,
                    filename=filename,
                    preferred_provider=preferred
                )
            
            data = ocr_result['data']
            recognition_method = ocr_result['provider']
            
            # Add version info
            if ocr_version == "v2.0" and ocr_result.get('layoutlm_used'):
                recognition_method += " v2.0 + LayoutLMv3"
            elif ocr_version == "v2.0":
                recognition_method += " v2.0"
            else:
                recognition_method += " v1.0"
            
            # Convert blocks to dict if they exist
            blocks_data = []
            if 'blocks' in ocr_result and ocr_result['blocks']:
                for block in ocr_result['blocks']:
                    if hasattr(block, 'to_dict'):
                        blocks_data.append(block.to_dict())
                    elif isinstance(block, dict):
                        blocks_data.append(block)
            
            # Get image dimensions for blocks
            image_size = ocr_result.get('image_size', (0, 0))
            
            raw_json = json.dumps({
                'method': f'ocr_{ocr_version}',
                'provider': ocr_result['provider'],
                'confidence': ocr_result.get('confidence', 0),
                'raw_data': ocr_result.get('raw_data'),
                'raw_text': ocr_result.get('raw_text'),
                'layoutlm_used': ocr_result.get('layoutlm_used', False),
                'validation': ocr_result.get('validation', {}),
                'blocks': blocks_data,  # ✅ Add blocks for editor
                'image_width': image_size[0],
                'image_height': image_size[1],
            }, ensure_ascii=False)
            
            logger.info(f"✅ OCR {ocr_version} completed for {filename} with {recognition_method}")
        
        # Validate results
        if not data or not any(data.values()):
            raise Exception("No data could be extracted from the image")
        
        # Enhance data
        self.update_state(state='PROCESSING', meta={'status': 'Enhancing data...'})
        data = enhance_ocr_result(data)
        
        # Attach metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        
        # Save to database
        self.update_state(state='PROCESSING', meta={'status': 'Saving to database...'})
        contact = Contact(**data)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        logger.info(f"Contact created: {contact.id} ({filename})")
        
        # 🤖 Active Learning: Check if this card should be sent to Label Studio
        try:
            if label_studio_service.is_available() and recognition_method and 'ocr' in recognition_method:
                should_annotate = active_learning_service.should_send_for_annotation(
                    contact_id=contact.id,
                    confidence=ocr_result.get('confidence', 0) if 'ocr_result' in locals() else 0,
                    ocr_data=data
                )
                
                if should_annotate:
                    # Get image URL for Label Studio
                    image_url = f"http://backend:8000/uploads/{safe_name}"
                    
                    # Send to Label Studio
                    task_id = label_studio_service.upload_task(
                        image_url=image_url,
                        contact_id=contact.id,
                        ocr_predictions={
                            'blocks': blocks_data if 'blocks_data' in locals() else [],
                            'data': data
                        }
                    )
                    
                    if task_id:
                        logger.info(f"📝 Contact {contact.id} sent to Label Studio (task {task_id})")
        except Exception as e:
            # Non-critical error, don't fail the whole task
            logger.warning(f"⚠️ Failed to send to Label Studio: {e}")
        
        return {
            'success': True,
            'contact_id': contact.id,
            'uid': contact.uid,
            'filename': filename,
            'recognition_method': recognition_method
        }
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")
        # Clean up file on error
        if 'save_path' in locals() and os.path.exists(save_path):
            os.remove(save_path)
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }


@celery_app.task(bind=True, name='app.tasks.process_batch_upload')
def process_batch_upload(
    self,
    zip_path: str,
    provider: str = 'auto',
    user_id: int = None
) -> Dict[str, Any]:
    """
    Process a batch of business cards from a ZIP archive.
    
    Args:
        zip_path: Path to ZIP file
        provider: OCR provider
        user_id: User ID for audit
        
    Returns:
        dict with results summary
    """
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'contacts': [],
        'errors': []
    }
    
    try:
        logger.info(f"✅ CELERY TASK STARTED: process_batch_upload from {zip_path}")
        logger.info(f"Processing batch upload: {zip_path}")
        
        # Extract ZIP
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Extracting ZIP archive...',
                'progress': 0,
                'total': 0,
                'processed': 0
            }
        )
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Filter image files
            image_files = [
                f for f in file_list
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'))
                and not f.startswith('__MACOSX')
                and not f.startswith('.')
            ]
            
            results['total'] = len(image_files)
            
            if not image_files:
                raise Exception("No image files found in ZIP archive")
            
            logger.info(f"Found {len(image_files)} images in ZIP")
            
            # Process each image
            for idx, filename in enumerate(image_files):
                try:
                    # Update progress
                    progress = int((idx / len(image_files)) * 100)
                    self.update_state(
                        state='PROCESSING',
                        meta={
                            'status': f'Processing {filename}...',
                            'progress': progress,
                            'total': len(image_files),
                            'processed': idx,
                            'current_file': filename
                        }
                    )
                    
                    # Read image data
                    image_data = zip_ref.read(filename)
                    
                    # Process card synchronously (not as Celery task)
                    result = _process_card_sync(
                        image_data,
                        os.path.basename(filename),
                        provider,
                        user_id
                    )
                    
                    if result['success']:
                        results['success'] += 1
                        results['contacts'].append(result)
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'filename': filename,
                            'error': result.get('error', 'Unknown error')
                        })
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
                    results['failed'] += 1
                    results['errors'].append({
                        'filename': filename,
                        'error': str(e)
                    })
        
        # Clean up ZIP file
        if os.path.exists(zip_path):
            os.remove(zip_path)
        
        logger.info(
            f"Batch processing completed: {results['success']} success, "
            f"{results['failed']} failed, {results['total']} total"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        # Clean up ZIP file on error
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise


@celery_app.task(name='app.tasks.cleanup_old_results')
def cleanup_old_results():
    """
    Clean up old Celery results from Redis.
    Runs periodically via Celery Beat.
    """
    try:
        from celery.result import AsyncResult
        import redis
        
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/1'))
        
        # Get all keys matching celery task pattern
        keys = redis_client.keys('celery-task-meta-*')
        
        cleaned = 0
        # cutoff_time = datetime.now() - timedelta(hours=24)  # Reserved for future use
        
        for key in keys:
            try:
                # Check if result is older than 24 hours
                ttl = redis_client.ttl(key)
                if ttl == -1:  # No expiry set
                    redis_client.delete(key)
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Error cleaning up key {key}: {e}")
        
        logger.info(f"Cleaned up {cleaned} old Celery results")
        return {'cleaned': cleaned}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {'error': str(e)}


@celery_app.task(name='app.tasks.train_ocr_models')
def train_ocr_models():
    """
    Train OCR models using annotated data from Label Studio.
    Triggered manually or on schedule.
    """
    try:
        from .integrations.label_studio.training import ModelTrainer
        
        logger.info("🎓 Starting OCR model training...")
        
        trainer = ModelTrainer()
        
        # Export annotations from Label Studio
        annotations = label_studio_service.export_annotations()
        
        if not annotations:
            logger.warning("⚠️ No annotations found in Label Studio")
            return {
                'success': False,
                'error': 'No training data available'
            }
        
        # Convert to training format
        training_data = trainer.prepare_training_data(annotations)
        
        if len(training_data) < 10:
            logger.warning(f"⚠️ Insufficient training data: {len(training_data)} samples (need 10+)")
            return {
                'success': False,
                'error': f'Insufficient training data: {len(training_data)} samples'
            }
        
        # Train PaddleOCR (if enabled)
        paddle_result = trainer.finetune_paddleocr(training_data)
        
        # Train LayoutLMv3 (if enabled)
        layoutlm_result = trainer.finetune_layoutlm(training_data)
        
        logger.info("✅ OCR model training completed")
        
        return {
            'success': True,
            'paddle_result': paddle_result,
            'layoutlm_result': layoutlm_result,
            'training_samples': len(training_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Model training failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='app.tasks.sync_feedback_to_label_studio')
def sync_feedback_to_label_studio():
    """
    Sync user feedback from OCR editor to Label Studio.
    Runs periodically to collect corrections.
    """
    try:
        from .integrations.label_studio.training import ModelTrainer
        
        logger.info("🔄 Syncing feedback to Label Studio...")
        
        trainer = ModelTrainer()
        synced_count = trainer.sync_user_corrections()
        
        logger.info(f"✅ Synced {synced_count} corrections to Label Studio")
        
        return {
            'success': True,
            'synced_count': synced_count
        }
        
    except Exception as e:
        logger.error(f"❌ Feedback sync failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

