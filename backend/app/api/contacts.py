"""
Contacts API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
import uuid
import logging
import os

from ..database import get_db
from ..models import Contact, User, DuplicateContact, Tag, Group
from ..core.utils import get_setting
from .. import schemas
from .. import auth_utils
from .. import duplicate_utils
from ..phone_utils import format_phone_number
from ..core.utils import create_audit_log, get_system_setting
from ..services.contact_service import ContactService

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Prometheus metrics
from ..core.metrics import (
    contacts_created_counter,
    contacts_updated_counter,
    contacts_deleted_counter,
    contacts_total
)


@router.get('/', response_model=schemas.PaginatedContactsResponse)
def list_contacts(
    q: str = Query(None, description="Search query (full-text search across all fields)"),
    company: str = Query(None, description="Filter by company"),
    position: str = Query(None, description="Filter by position"),
    tags: str = Query(None, description="Filter by tag names (comma-separated)"),
    groups: str = Query(None, description="Filter by group names (comma-separated)"),
    sort_by: str = Query('id', description="Sort field: id, full_name, company, position"),
    sort_order: str = Query('desc', description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get paginated list of contacts with advanced search and filtering.
    
    All business logic is delegated to ContactService.
    Роутер только валидирует параметры и вызывает сервис.
    """
    service = ContactService(db)
    return service.list_contacts(
        q=q, company=company, position=position,
        tags=tags, groups=groups,
        sort_by=sort_by, sort_order=sort_order,
        page=page, limit=limit
    )


@router.get('/search/')
def search_contacts(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results (1-50)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Fast global search for SearchOverlay (Ctrl+K).
    Searches across names, company, position, email, phone.
    Returns minimal data for quick results.
    """
    search_term = f"%{q}%"
    
    # Search with relevance ranking
    contacts = db.query(Contact).filter(
        (Contact.full_name.ilike(search_term)) |
        (Contact.company.ilike(search_term)) |
        (Contact.position.ilike(search_term)) |
        (Contact.email.ilike(search_term)) |
        (Contact.phone.ilike(search_term))
    ).limit(limit).all()
    
    # Return simplified data
    return [{
        'id': c.id,
        'full_name': c.full_name,
        'company': c.company,
        'position': c.position,
        'email': c.email,
        'phone': c.phone
    } for c in contacts]


@router.get('/{contact_id}')
def get_contact_by_id(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get a single contact by ID.
    Requires valid JWT token.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return contact


@router.get('/uid/{uid}')
def get_contact_by_uid(
    uid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get a single contact by UID.
    Requires valid JWT token.
    """
    contact = db.query(Contact).filter(Contact.uid == uid).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return contact


@router.post('/')
def create_contact(
    data: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Create a new contact.
    
    All business logic is delegated to ContactService.
    Роутер только валидирует данные и вызывает сервис.
    """
    service = ContactService(db)
    return service.create_contact(
        data=data.dict(),
        current_user=current_user,
        auto_detect_duplicates=True
    )


@router.put('/{contact_id}')
def update_contact(
    contact_id: int,
    data: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Update an existing contact.
    
    All business logic is delegated to ContactService.
    """
    service = ContactService(db)
    return service.update_contact(
        contact_id=contact_id,
        data=data.dict(exclude_unset=True),
        current_user=current_user
    )


@router.delete('/{contact_id}')
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Delete a contact.
    
    All business logic is delegated to ContactService.
    """
    service = ContactService(db)
    service.delete_contact(contact_id=contact_id, current_user=current_user)
    return {'deleted': contact_id}


@router.get('/{contact_id}/history', response_model=List[schemas.AuditLogResponse])
def get_contact_history(
    contact_id: int,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get audit history for a specific contact."""
    from ..models import AuditLog
    
    # Check if contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Get audit logs for this contact
    logs = db.query(AuditLog).filter(
        AuditLog.contact_id == contact_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return logs


@router.get('/{contact_id}/ocr-blocks')
def get_contact_ocr_blocks(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get OCR bounding boxes and text blocks for a contact's image.
    Returns coordinates and text for visual editing.
    """
    from .. import tesseract_boxes
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.photo_path:
        raise HTTPException(status_code=400, detail='Contact has no image')
    
    # Read image file
    image_path = os.path.join('uploads', contact.photo_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail='Image file not found')
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Get Tesseract language from settings
        tesseract_langs = get_setting(db, 'TESSERACT_LANGS', 'rus+eng')
        
        # Extract blocks
        result = tesseract_boxes.get_text_blocks(image_bytes, lang=tesseract_langs)
        
        # Group into lines for easier visualization
        lines = tesseract_boxes.group_blocks_by_line(result['blocks'])
        
        return {
            'contact_id': contact_id,
            'image_width': result['image_width'],
            'image_height': result['image_height'],
            'blocks': result['blocks'],  # Word-level blocks
            'lines': lines,  # Line-level grouped blocks
            'current_data': {
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'middle_name': contact.middle_name,
                'company': contact.company,
                'position': contact.position,
                'email': contact.email,
                'phone': contact.phone,
                'phone_mobile': contact.phone_mobile,
                'phone_work': contact.phone_work,
                'phone_additional': contact.phone_additional,
                'address': contact.address,
                'address_additional': contact.address_additional,
                'website': contact.website
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting OCR blocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract OCR blocks: {str(e)}")


@router.post('/{contact_id}/ocr-corrections')
def save_ocr_correction(
    contact_id: int,
    correction_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Save OCR correction for training purposes.
    Stores original OCR text, corrected text, and field assignment.
    """
    from ..models import OCRCorrection
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    correction = OCRCorrection(
        contact_id=contact_id,
        original_text=correction_data.get('original_text'),
        original_box=correction_data.get('original_box', '{}'),
        original_confidence=correction_data.get('original_confidence'),
        corrected_text=correction_data.get('corrected_text'),
        corrected_field=correction_data.get('field_name'),
        image_path=contact.photo_path,
        ocr_provider=correction_data.get('ocr_provider'),
        language=correction_data.get('language'),
        user_id=current_user.id
    )
    
    db.add(correction)
    db.commit()
    
    return {'status': 'success', 'message': 'Correction saved for training'}


@router.post('/{contact_id}/reprocess-ocr')
def reprocess_contact_ocr(
    contact_id: int,
    blocks_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Reprocess OCR for a contact with updated block information.
    Takes modified block positions/sizes and re-extracts contact fields.
    """
    from ..ocr_providers import OCRManager
    import json
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.photo_path:
        raise HTTPException(status_code=400, detail='Contact has no image')
    
    # Get blocks from request
    blocks = blocks_data.get('blocks', [])
    
    # Combine all block texts
    all_text = '\n'.join([block.get('text', '') for block in blocks])
    
    # Use OCR Manager to re-extract fields from combined text
    ocr_manager = OCRManager()
    
    try:
        # Extract structured data from the combined OCR text
        extracted_data = ocr_manager.extract_contact_fields(all_text)
        
        # Update contact with new data (only non-empty fields)
        for field, value in extracted_data.items():
            if value and hasattr(contact, field):
                setattr(contact, field, value)
        
        # Update OCR raw text
        contact.ocr_raw = all_text
        
        db.commit()
        db.refresh(contact)
        
        # Return updated contact data
        return {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'middle_name': contact.middle_name,
            'company': contact.company,
            'position': contact.position,
            'email': contact.email,
            'phone': contact.phone,
            'phone_mobile': contact.phone_mobile,
            'phone_work': contact.phone_work,
            'phone_additional': contact.phone_additional,
            'address': contact.address,
            'address_additional': contact.address_additional,
            'website': contact.website
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing OCR for contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to reprocess OCR: {str(e)}')

