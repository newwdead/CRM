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
from .. import auth_utils
from ..ocr_providers import OCRManager

# Initialize OCR Manager
ocr_manager = OCRManager()
from .. import ocr_utils
from .. import qr_utils
from .. import image_processing
from ..image_utils import create_thumbnail, downscale_image_bytes

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
                       provider: str, filename: str, db: Session) -> Optional[dict]:
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
                ocr_result = ocr_manager.recognize(
                    ocr_input,
                    filename=filename,
                    preferred_provider=preferred
                )
                processing_time = time.time() - start_time
                
                # Update metrics
                used_provider = ocr_result['provider']
                ocr_processing_time.labels(provider=used_provider).observe(processing_time)
                ocr_processing_counter.labels(provider=used_provider, status='success').inc()
                
                data = ocr_result['data']
                recognition_method = ocr_result['provider']
                raw_text = ocr_result.get('raw_text', '')
                raw_json = json.dumps({
                    'method': 'ocr',
                    'provider': ocr_result['provider'],
                    'confidence': ocr_result.get('confidence', 0),
                    'raw_data': ocr_result.get('raw_data'),
                    'raw_text': raw_text,
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
        data['recognition_method'] = recognition_method
        
        # Save to database
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        # Convert to dict for response
        contact_dict = {
            "id": contact.id,
            "uid": contact.uid,
            "name": contact.name,
            "company": contact.company,
            "position": contact.position,
            "email": contact.email,
            "phone": contact.phone,
            "website": contact.website,
            "address": contact.address,
            "notes": contact.notes,
            "photo_path": contact.photo_path,
            "thumbnail_path": contact.thumbnail_path,
            "recognition_method": contact.recognition_method,
        }
        
        return contact_dict
        
    except Exception as e:
        logger.error(f"Failed to process card: {e}")
        return None


@router.post('/upload/')
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
                card_data = process_single_card(
                    card_bytes, 
                    card_safe_name, 
                    card_thumbnail_name,
                    provider, 
                    file.filename,
                    db
                )
                
                if card_data:
                    created_contacts.append(card_data)
            
            # Update metrics
            contacts_created_counter.inc(len(created_contacts))
            contacts_total.set(db.query(Contact).count())
            
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
            db
        )
        
        if not contact_dict:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Update metrics
        contacts_created_counter.inc()
        contacts_total.set(db.query(Contact).count())
        
        return contact_dict
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post('/batch-upload/')
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

