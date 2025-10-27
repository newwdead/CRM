"""
OCR Processing API endpoints (upload, batch upload, providers)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request, status
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import json
import time
import logging

from ..database import get_db
from ..models import Contact, User
from ..core import auth as auth_utils
from ..integrations.ocr.providers import OCRManager  # OCR v1.0 (fallback)
from ..integrations.ocr.providers_v2 import OCRManagerV2  # OCR v2.0 (primary)

# Initialize OCR Managers
ocr_manager_v1 = OCRManager()  # Fallback to Tesseract if v2 fails
ocr_manager_v2 = OCRManagerV2(enable_layoutlm=True)  # Primary: PaddleOCR + LayoutLMv3
ocr_manager = ocr_manager_v2  # Use v2.0 by default
from ..integrations.ocr import utils as ocr_utils
from ..core import qr as qr_utils
from ..integrations.ocr import image_processing
from ..integrations.ocr.image_utils import create_thumbnail, downscale_image_bytes
from ..core.file_security import validate_and_secure_file, sanitize_filename
from ..services.storage_service import StorageService
from ..services.validator_service import ValidatorService

# Prometheus metrics
from ..core.metrics import (
    contacts_created_counter,
    contacts_total,
    qr_scan_counter,
    ocr_processing_time,
    ocr_processing_counter
)

# Limiter (imported from main.py)
from slowapi import Limiter
from slowapi.util import get_remote_address

import os
limiter = Limiter(key_func=get_remote_address, enabled=os.getenv("TESTING") != "true")

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


@router.get('/providers')
def get_ocr_providers():
    """Получить информацию о доступных OCR провайдерах"""
    return {
        'available': ocr_manager.get_available_providers(),
        'details': ocr_manager.get_provider_info()
    }


def process_single_card(card_bytes: bytes, safe_name: str, thumbnail_name: str, 
                       provider: str, filename: str, db: Session, user_id: int = None) -> Optional[dict]:
    """
    Process a single business card image (QR + OCR).
    Returns contact data dict or None on failure.
    """
    try:
        # STEP 1: Try QR code scanning first
        data = None
        raw_json = None
        raw_text = ""
        recognition_method = None
        
        logger.info("Attempting QR code scan...")
        qr_data = qr_utils.process_image_with_qr(card_bytes)
        
        if qr_data and any(qr_data.values()):
            # QR code found
            data = qr_data
            recognition_method = 'qr_code'
            raw_json = json.dumps({
                'method': 'qr_code',
                'data': qr_data
            }, ensure_ascii=False)
            qr_scan_counter.labels(status='success').inc()
            logger.info("QR code extracted successfully")
        else:
            # No QR code - fallback to OCR
            qr_scan_counter.labels(status='not_found').inc()
            logger.info("No QR code found, falling back to OCR...")
            
            # Prepare for OCR
            ocr_input = downscale_image_bytes(card_bytes, max_side=2000)
            preferred = None if provider == 'auto' else provider
            
            try:
                start_time = time.time()
                
                # Check OCR version setting
                from ..core.utils import get_setting
                ocr_version = get_setting(db, "ocr_version", "v2.0")
                
                # OCR v2.0: PaddleOCR + LayoutLMv3 with fallback to v1.0
                if ocr_version == "v2.0":
                    try:
                        logger.info("🚀 Using OCR v2.0 (PaddleOCR + LayoutLMv3)...")
                        ocr_result = ocr_manager_v2.recognize(
                            image_data=ocr_input,
                            provider_name=preferred if preferred != 'auto' else None,
                            use_layout=True  # Enable LayoutLMv3 classification
                        )
                        logger.info(f"✅ OCR v2.0 successful: {ocr_result.get('provider', 'PaddleOCR')}")
                    except Exception as v2_error:
                        logger.warning(f"⚠️ OCR v2.0 failed: {v2_error}, falling back to v1.0...")
                        ocr_result = ocr_manager_v1.recognize(
                            ocr_input,
                            filename=filename,
                            preferred_provider=preferred
                        )
                        logger.info("✅ OCR v1.0 (Tesseract) fallback successful")
                else:
                    # Use v1.0 directly
                    logger.info("🔧 Using OCR v1.0 (Tesseract) by settings...")
                    ocr_result = ocr_manager_v1.recognize(
                        ocr_input,
                        filename=filename,
                        preferred_provider=preferred
                    )
                    logger.info(f"✅ OCR v1.0 successful: Tesseract")
                
                processing_time = time.time() - start_time
                
                # Update metrics
                used_provider = ocr_result.get('provider', 'unknown')
                ocr_processing_time.labels(provider=used_provider).observe(processing_time)
                ocr_processing_counter.labels(provider=used_provider, status='success').inc()
                
                data = ocr_result['data']
                recognition_method = ocr_result['provider']
                raw_text = ocr_result.get('raw_text', '')
                
                # OCR v2.0: Auto-validation and correction
                try:
                    logger.info("🔍 Applying Validator Service for auto-correction...")
                    validator = ValidatorService()
                    validated_data = validator.validate_and_correct(data)
                    if validated_data:
                        data = validated_data
                        logger.info("✅ Data validated and corrected")
                except Exception as val_error:
                    logger.warning(f"⚠️ Validator failed (non-critical): {val_error}")
                
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
                    'method': 'ocr',
                    'provider': ocr_result['provider'],
                    'confidence': ocr_result.get('confidence', 0),
                    'raw_data': ocr_result.get('raw_data'),
                    'raw_text': raw_text,
                    'layoutlm_used': ocr_result.get('layoutlm_used', False),
                    'layoutlm_confidence': ocr_result.get('layoutlm_confidence', 0),
                    'validation_applied': 'validated_data' in locals(),
                    'blocks': blocks_data,  # ✅ Add blocks for editor
                    'image_width': image_size[0],
                    'image_height': image_size[1],
                    'block_count': len(blocks_data),
                }, ensure_ascii=False)
                
                logger.info(f"OCR successful with {used_provider}, confidence: {ocr_result.get('confidence', 0)}")
                
            except Exception as e:
                ocr_processing_counter.labels(provider=preferred or 'auto', status='failed').inc()
                logger.error(f"OCR failed: {e}")
                return None
        
        # Validate results
        if not data or not any(data.values()):
            logger.warning("No data extracted from card")
            return None
        
        # Enhance data with improved parsing
        data = ocr_utils.enhance_ocr_result(data, raw_text=raw_text)
        
        # Attach metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        # Note: user_id is not a field in Contact model, skip it
        
        # Save to database using ContactRepository
        from ..repositories import ContactRepository
        contact_repo = ContactRepository(db)
        contact = contact_repo.create(data)
        contact_repo.commit()
        db.refresh(contact)
        
        # Save image to MinIO (OCR v2.0)
        try:
            storage_service = StorageService(db)
            minio_path = storage_service.save_business_card_image(
                contact_id=contact.id,
                image_data=card_bytes,
                filename=filename,
                metadata={
                    'original_filename': filename,
                    'safe_filename': safe_name,
                    'recognition_method': recognition_method,
                    'contact_uid': contact.uid
                }
            )
            if minio_path:
                logger.info(f"✅ Image saved to MinIO: {minio_path}")
            else:
                logger.warning("⚠️ MinIO image save failed (not critical)")
        except Exception as minio_error:
            logger.error(f"❌ MinIO image error: {minio_error}")
            # Continue - MinIO failure is not critical
        
        # Save OCR results to MinIO (OCR v2.0)
        try:
            storage_service = StorageService(db)
            ocr_result_path = storage_service.save_ocr_result(
                contact_id=contact.id,
                result_data=json.loads(raw_json)
            )
            if ocr_result_path:
                logger.info(f"✅ OCR result saved to MinIO: {ocr_result_path}")
        except Exception as ocr_minio_error:
            logger.error(f"❌ MinIO OCR result error: {ocr_minio_error}")
            # Continue - MinIO failure is not critical
        
        # Convert to dict for response
        contact_dict = {
            "id": contact.id,
            "uid": contact.uid,
            "name": contact.full_name,  # Contact model uses full_name, not name
            "company": contact.company,
            "position": contact.position,
            "email": contact.email,
            "phone": contact.phone,
            "website": contact.website,
            "address": contact.address,
            "notes": contact.comment,  # Contact model uses comment, not notes
            "photo_path": contact.photo_path,
            "thumbnail_path": contact.thumbnail_path,
            "recognition_method": recognition_method,
        }
        
        return contact_dict
        
    except Exception as e:
        logger.error(f"Failed to process card: {e}")
        return None


@router.post('/upload')
@limiter.limit("60/minute")
async def upload_card(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
    auto_crop: bool = Query(True, description="Automatically crop business card boundaries"),
    detect_multi: bool = Query(True, description="Detect multiple cards in single image"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Upload and process business card image(s)"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (20MB max)
        limit_size = 20 * 1024 * 1024
        head = file.file.read(limit_size + 1)
        if len(head) > limit_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 20MB")
        file.file.seek(0)
        
        # Read image content
        content = file.file.read()
        file.file.seek(0)
        
        # STEP 0: Image preprocessing - crop and detect multiple cards
        logger.info(f"Processing image with auto_crop={auto_crop}, detect_multi={detect_multi}")
        processed_cards = image_processing.process_business_card_image(
            content, 
            auto_crop=auto_crop,
            detect_multi=detect_multi,
            enhance=False
        )
        
        logger.info(f"Image processing complete: {len(processed_cards)} card(s) detected")
        
        # If multiple cards detected, handle each one
        if len(processed_cards) > 1:
            logger.info(f"Multiple cards detected ({len(processed_cards)}), processing each separately")
            created_contacts = []
            
            for idx, card_bytes in enumerate(processed_cards[:5]):  # Limit to 5 cards
                logger.info(f"Processing card {idx + 1}/{len(processed_cards)}")
                
                # Save card to disk
                card_safe_name = f"{uuid.uuid4().hex}_card{idx+1}_{os.path.basename(file.filename or 'upload')}"
                card_save_path = os.path.join('uploads', card_safe_name)
                with open(card_save_path, 'wb') as f:
                    f.write(card_bytes)
                
                # Create thumbnail
                card_thumbnail_path = create_thumbnail(card_save_path, size=(200, 200), quality=85)
                card_thumbnail_name = os.path.basename(card_thumbnail_path)
                
                # Process card (QR + OCR)
                try:
                    card_data = process_single_card(
                        card_bytes, 
                        card_safe_name, 
                        card_thumbnail_name,
                        provider, 
                        file.filename,
                        db,
                        user_id=current_user.id
                    )
                    
                    if card_data:
                        created_contacts.append(card_data)
                        logger.info(f"Successfully processed card {idx + 1}: Contact ID {card_data.get('id')}")
                    else:
                        logger.warning(f"Card {idx + 1} processing returned no data")
                except Exception as card_error:
                    logger.error(f"Error processing card {idx + 1}: {card_error}")
                    # Continue with other cards even if one fails
                    continue
            
            # Update metrics
            contacts_created_counter.inc(len(created_contacts))
            from ..repositories import ContactRepository
            contact_repo = ContactRepository(db)
            contacts_total.set(contact_repo.count())
            
            return {
                "message": f"{len(created_contacts)} business cards detected and processed",
                "contacts": created_contacts
            }
        
        # Single card - use processed image
        content = processed_cards[0]
        
        # Save processed file to disk
        safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload')}"
        save_path = os.path.join('uploads', safe_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # Create thumbnail (200x200, quality 85%)
        thumbnail_full_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_full_path)
        
        # Process single card (QR + OCR)
        contact_dict = process_single_card(
            content,
            safe_name,
            thumbnail_name,
            provider,
            file.filename,
            db,
            user_id=current_user.id
        )
        
        if not contact_dict:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Update metrics
        contacts_created_counter.inc()
        from ..repositories import ContactRepository
        contact_repo = ContactRepository(db)
        contacts_total.set(contact_repo.count())
        
        return contact_dict
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post('/batch-upload')
@limiter.limit("10/hour")
async def batch_upload(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Upload a ZIP archive containing multiple business card images.
    Returns a task ID for tracking progress.
    """
    try:
        # Validate file type
        if not file.content_type or 'zip' not in file.content_type.lower():
            if not file.filename or not file.filename.lower().endswith('.zip'):
                raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Check file size (100MB max for ZIP)
        limit_size = 100 * 1024 * 1024
        content = file.file.read(limit_size + 1)
        if len(content) > limit_size:
            raise HTTPException(status_code=400, detail="ZIP file too large. Maximum size is 100MB")
        
        # Save ZIP file
        zip_name = f"{uuid.uuid4().hex}_batch.zip"
        zip_path = os.path.join('uploads', zip_name)
        with open(zip_path, 'wb') as f:
            f.write(content)
        
        # Import Celery task
        from ..tasks import process_batch_upload
        
        # Queue batch processing task
        task = process_batch_upload.delay(
            zip_path=zip_path,
            provider=provider,
            user_id=current_user.id
        )
        
        logger.info(f"Batch upload queued: {task.id} by user {current_user.username}")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Batch processing started. Use /ocr/batch-status/{task_id} to track progress."
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get('/batch-status/{task_id}')
def get_batch_status(
    task_id: str,
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get status of a batch processing task.
    """
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Waiting in queue...',
                'progress': 0
            }
        elif task.state == 'PROCESSING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': task.info.get('status', 'Processing...'),
                'progress': task.info.get('progress', 0),
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Completed',
                'progress': 100,
                'result': task.info
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': str(task.info),
                'progress': 0,
                'error': str(task.info)
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': str(task.info),
                'progress': 0
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

