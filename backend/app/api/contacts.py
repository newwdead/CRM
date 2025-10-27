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
from ..models import Contact, User, Tag, Group
from ..core.utils import get_setting
from .. import schemas
from ..core import auth as auth_utils
from ..core.phone import format_phone_number
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
        current_user=current_user
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
    from ..integrations.ocr import tesseract_boxes
    
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
        
        # Check if contact has saved OCR blocks (user-modified or from OCR v2.0)
        import json
        saved_blocks = None
        image_width = 0
        image_height = 0
        
        if contact.ocr_raw:
            try:
                ocr_data = json.loads(contact.ocr_raw)
                if isinstance(ocr_data, dict) and 'blocks' in ocr_data:
                    saved_blocks = ocr_data['blocks']
                    image_width = ocr_data.get('image_width', 0)
                    image_height = ocr_data.get('image_height', 0)
                    logger.info(f"📦 Using saved blocks: {len(saved_blocks)} blocks")
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse saved blocks: {e}")
                pass
        
        # If we have saved blocks, use them; otherwise extract from image
        if saved_blocks:
            # Use saved blocks from previous edit/reprocess or OCR v2.0
            lines = saved_blocks
        else:
            # Extract blocks from image using Tesseract as fallback
            logger.info("🔍 No saved blocks found, extracting with Tesseract...")
            tesseract_langs = get_setting(db, 'TESSERACT_LANGS', 'rus+eng')
            result = tesseract_boxes.get_text_blocks(image_bytes, lang=tesseract_langs)
            lines = tesseract_boxes.group_blocks_by_line(result['blocks'])
            image_width = result['image_width']
            image_height = result['image_height']
        
        return {
            'contact_id': contact_id,
            'image_url': f'/files/{contact.photo_path}',  # Image URL for frontend
            'image_width': image_width,
            'image_height': image_height,
            'blocks': lines if not saved_blocks else [],  # Word-level blocks (legacy)
            'lines': lines,  # Line-level grouped blocks or saved blocks
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


@router.post('/{contact_id}/save-ocr-blocks')
def save_ocr_blocks(
    contact_id: int,
    blocks_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Save OCR blocks without reprocessing.
    Stores user-modified blocks for future reference.
    """
    import json
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    blocks = blocks_data.get('blocks', [])
    
    # Save blocks to ocr_raw
    ocr_data = {
        'blocks': blocks,
        'timestamp': str(contact.updated_at or '')
    }
    contact.ocr_raw = json.dumps(ocr_data, ensure_ascii=False)
    
    db.commit()
    
    return {'status': 'success', 'message': 'Blocks saved'}


@router.get('/{contact_id}/scan-qr')
def scan_qr_code_from_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Сканировать QR код из изображения контакта
    """
    from ..core import qr as qr_utils
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.photo_path:
        raise HTTPException(status_code=400, detail='Contact has no image')
    
    # Read image
    image_path = f'./uploads/{contact.photo_path}'
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Image file not found')
    
    # Scan QR code
    qr_data = qr_utils.scan_qr_code(image_bytes)
    
    if not qr_data:
        return {
            'has_qr': False,
            'qr_data': None,
            'contact_data': None,
            'message': 'QR код не найден на изображении'
        }
    
    # Parse QR data if it's a contact format (vCard or MeCard)
    contact_data = qr_utils.extract_contact_from_qr(qr_data)
    
    # Save QR data to contact
    contact.has_qr_code = 1
    contact.qr_data = qr_data
    db.commit()
    
    return {
        'has_qr': True,
        'qr_data': qr_data,
        'contact_data': contact_data,
        'qr_type': 'vCard' if 'BEGIN:VCARD' in qr_data.upper() else ('MeCard' if qr_data.upper().startswith('MECARD:') else 'Other'),
        'message': 'QR код успешно распознан'
    }


@router.post('/{contact_id}/apply-qr-data')
def apply_qr_data_to_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Применить данные из QR кода к контакту
    """
    from ..core import qr as qr_utils
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.qr_data:
        raise HTTPException(status_code=400, detail='No QR data found for this contact')
    
    # Extract contact data from QR
    contact_data = qr_utils.extract_contact_from_qr(contact.qr_data)
    
    if not contact_data:
        raise HTTPException(status_code=400, detail='Could not parse contact data from QR code')
    
    # Apply data to contact (only non-empty fields)
    updated_fields = []
    for field, value in contact_data.items():
        if value and hasattr(contact, field):
            setattr(contact, field, value)
            updated_fields.append(field)
    
    db.commit()
    db.refresh(contact)
    
    return {
        'status': 'success',
        'updated_fields': updated_fields,
        'message': f'Обновлено полей: {len(updated_fields)}'
    }


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
    
    # Use OCR utils to extract fields from combined text
    from ..integrations.ocr import utils as ocr_utils
    import re
    
    try:
        # Start with empty data dict
        extracted_data = {}
        
        # Use enhance_ocr_result to parse the text
        # It extracts emails, phones, addresses, names, etc from raw text
        extracted_data = ocr_utils.enhance_ocr_result({}, raw_text=all_text)
        
        # Update contact with new data (only non-empty fields)
        for field, value in extracted_data.items():
            if value and hasattr(contact, field):
                setattr(contact, field, value)
        
        # Update OCR raw text and save blocks for future reference
        import json
        ocr_data = {
            'text': all_text,
            'blocks': blocks,  # Save user-modified blocks
            'timestamp': str(db.query(Contact).filter(Contact.id == contact_id).first().updated_at or '')
        }
        contact.ocr_raw = json.dumps(ocr_data, ensure_ascii=False)
        
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


@router.post('/merge')
def merge_contacts(
    payload: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Merge multiple contacts into one master contact.
    
    Request body:
    {
        "master_id": int,  # ID контакта-мастера (основного)
        "slave_ids": [int, ...]  # IDs контактов для объединения
    }
    """
    master_id = payload.get('master_id')
    slave_ids = payload.get('slave_ids', [])
    
    # Log merge request for debugging
    logger.info(f"Merge request: master_id={master_id}, slave_ids={slave_ids} (count: {len(slave_ids)})")
    
    if not master_id or not slave_ids:
        raise HTTPException(status_code=400, detail='master_id and slave_ids are required')
    
    # CRITICAL VALIDATION: Master ID must NOT be in slave_ids!
    if master_id in slave_ids:
        logger.error(f"CRITICAL ERROR: master_id={master_id} is in slave_ids! This would delete the master contact!")
        raise HTTPException(
            status_code=400, 
            detail=f'Master contact (ID: {master_id}) cannot be in the list of contacts to delete! This is a critical error.'
        )
    
    # Get master contact
    master = db.query(Contact).filter(Contact.id == master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail='Master contact not found')
    
    # Get slave contacts
    slaves = db.query(Contact).filter(Contact.id.in_(slave_ids)).all()
    if len(slaves) != len(slave_ids):
        raise HTTPException(status_code=404, detail='Some slave contacts not found')
    
    try:
        # Merge data from slaves to master - ALL fields
        for slave in slaves:
            # Merge fields if master field is empty
            # Name fields
            if not master.full_name and slave.full_name:
                master.full_name = slave.full_name
            if not master.first_name and slave.first_name:
                master.first_name = slave.first_name
            if not master.last_name and slave.last_name:
                master.last_name = slave.last_name
            if not master.middle_name and slave.middle_name:
                master.middle_name = slave.middle_name
            
            # Company fields
            if not master.company and slave.company:
                master.company = slave.company
            if not master.position and slave.position:
                master.position = slave.position
            if not master.department and slave.department:
                master.department = slave.department
            
            # Contact fields
            if not master.email and slave.email:
                master.email = slave.email
            if not master.phone and slave.phone:
                master.phone = slave.phone
            if not master.phone_mobile and slave.phone_mobile:
                master.phone_mobile = slave.phone_mobile
            if not master.phone_work and slave.phone_work:
                master.phone_work = slave.phone_work
            if not master.phone_additional and slave.phone_additional:
                master.phone_additional = slave.phone_additional
            if not master.fax and slave.fax:
                master.fax = slave.fax
            
            # Address fields
            if not master.address and slave.address:
                master.address = slave.address
            if not master.address_additional and slave.address_additional:
                master.address_additional = slave.address_additional
            
            # Other fields
            if not master.website and slave.website:
                master.website = slave.website
            if not master.birthday and slave.birthday:
                master.birthday = slave.birthday
            if not master.source and slave.source:
                master.source = slave.source
            if not master.status and slave.status:
                master.status = slave.status
            if not master.priority and slave.priority:
                master.priority = slave.priority
            if not master.comment and slave.comment:
                master.comment = slave.comment
            if not master.qr_data and slave.qr_data:
                master.qr_data = slave.qr_data
                master.has_qr_code = slave.has_qr_code
            
            # Merge tags (add unique tags from slaves)
            if slave.tags:
                master_tag_names = {tag.name for tag in master.tags}
                for tag in slave.tags:
                    if tag.name not in master_tag_names:
                        master.tags.append(tag)
            
            # Merge groups (add unique groups from slaves)
            if slave.groups:
                master_group_names = {group.name for group in master.groups}
                for group in slave.groups:
                    if group.name not in master_group_names:
                        master.groups.append(group)
            
            # Use photo from slave if master has none
            if not master.photo_path and slave.photo_path:
                master.photo_path = slave.photo_path
                master.thumbnail_path = slave.thumbnail_path
        
        # Delete slave contacts
        for slave in slaves:
            db.delete(slave)
        
        # Commit changes
        db.commit()
        db.refresh(master)
        
        # Update contact counter
        contacts_deleted_counter.inc(len(slave_ids))
        
        # Log the merge
        create_audit_log(
            db,
            contact_id=master_id,
            user=current_user,
            action='merge_contacts',
            entity_type='contact',
            changes={'merged_contacts': slave_ids, 'master_id': master_id}
        )
        
        logger.info(f"Merged contacts {slave_ids} into {master_id}")
        
        return {
            'success': True,
            'master_id': master_id,
            'merged_count': len(slave_ids),
            'message': f'Successfully merged {len(slave_ids)} contacts into master contact'
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error merging contacts: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to merge contacts: {str(e)}')

