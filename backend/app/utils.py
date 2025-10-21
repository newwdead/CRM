"""
Utility functions for backend application
"""
import io
import json
import logging
import uuid
import time
from pathlib import Path
from typing import Optional
from PIL import Image
from sqlalchemy.orm import Session

from .models import Contact, AuditLog, User
from . import ocr_utils, qr_utils
from .ocr_providers import OCRManager
from .core.metrics import (
    qr_scan_counter,
    ocr_processing_counter,
    ocr_processing_time
)

logger = logging.getLogger(__name__)
ocr_manager = OCRManager()


def create_audit_log(
    db: Session,
    contact_id: Optional[int],
    user: User,
    action: str,
    entity_type: str = 'contact',
    changes: Optional[dict] = None
):
    """Create an audit log entry."""
    audit_entry = AuditLog(
        contact_id=contact_id,
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        entity_type=entity_type,
        changes=json.dumps(changes, ensure_ascii=False) if changes else None
    )
    db.add(audit_entry)
    # Note: Commit should be done by the caller


def downscale_image_bytes(data: bytes, max_side: int = 2000) -> bytes:
    """Downscale image bytes while maintaining aspect ratio."""
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert('RGB')
            # downscale in-place keeping aspect ratio
            im.thumbnail((max_side, max_side))
            out = io.BytesIO()
            im.save(out, format='JPEG', quality=90)
            return out.getvalue()
    except Exception:
        # if Pillow cannot open, return original
        return data


def create_thumbnail(image_path: str, size: tuple = (200, 200), quality: int = 85) -> str:
    """
    Create a thumbnail for the given image.
    
    Args:
        image_path: Path to the original image
        size: Thumbnail size (width, height), default (200, 200)
        quality: JPEG quality (1-100), default 85
    
    Returns:
        Path to the created thumbnail
    """
    try:
        # Generate thumbnail filename
        path_obj = Path(image_path)
        thumb_name = f"{path_obj.stem}_thumb{path_obj.suffix}"
        thumb_path = path_obj.parent / thumb_name
        
        # Open image and create thumbnail
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode:
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(str(thumb_path), 'JPEG', quality=quality, optimize=True)
            
        logger.info(f"Thumbnail created: {thumb_path}")
        return str(thumb_path)
    
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        # Return original path if thumbnail creation fails
        return image_path


def process_single_card(
    card_bytes: bytes,
    safe_name: str,
    thumbnail_name: str,
    provider: str,
    filename: str,
    db: Session
) -> Optional[dict]:
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
                raw_text = ocr_result.get('raw_text', '')  # Get raw text for enhanced parsing
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
        
        # Enhance data with improved parsing (pass raw_text for phone/address extraction)
        data = ocr_utils.enhance_ocr_result(data, raw_text=raw_text)
        
        # Attach metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        
        # Save to database
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        logger.info(f"Contact created: {contact.id} ({filename})")
        
        # Return contact data
        return {
            "id": contact.id,
            "uid": contact.uid,
            "full_name": contact.full_name,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "middle_name": contact.middle_name,
            "company": contact.company,
            "position": contact.position,
            "email": contact.email,
            "phone": contact.phone,
            "phone_mobile": contact.phone_mobile,
            "phone_work": contact.phone_work,
            "phone_additional": contact.phone_additional,
            "address": contact.address,
            "address_additional": contact.address_additional,
            "website": contact.website,
            "photo_path": contact.photo_path,
            "thumbnail_path": contact.thumbnail_path,
            "recognition_method": recognition_method,
        }
        
    except Exception as e:
        logger.error(f"Error processing card: {e}")
        return None

