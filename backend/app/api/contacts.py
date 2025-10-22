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
    
    Parameters:
    - q: Full-text search across all fields (name, company, position, email, phone)
    - company: Filter by company (case-insensitive partial match)
    - position: Filter by position (case-insensitive partial match)
    - tags: Filter by tag names (comma-separated, e.g., "vip,client")
    - groups: Filter by group names (comma-separated, e.g., "partners,customers")
    - sort_by: Field to sort by (id, full_name, company, position)
    - sort_order: Sort direction (asc, desc)
    - page: Page number (starts from 1)
    - limit: Items per page (1-100, default 20)
    """
    # Optimize N+1 queries with eager loading
    query = db.query(Contact).options(
        joinedload(Contact.tags),
        joinedload(Contact.groups)
    )
    
    # Full-text search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Contact.full_name.ilike(search_term)) |
            (Contact.company.ilike(search_term)) |
            (Contact.position.ilike(search_term)) |
            (Contact.email.ilike(search_term)) |
            (Contact.phone.ilike(search_term)) |
            (Contact.website.ilike(search_term)) |
            (Contact.address.ilike(search_term))
        )
    
    # Filter by company
    if company:
        query = query.filter(Contact.company.ilike(f"%{company}%"))
    
    # Filter by position
    if position:
        query = query.filter(Contact.position.ilike(f"%{position}%"))
    
    # Filter by tags
    if tags:
        tag_names = [name.strip() for name in tags.split(',') if name.strip()]
        if tag_names:
            # Get tag IDs for the given names
            tag_records = db.query(Tag).filter(Tag.name.in_(tag_names)).all()
            tag_ids = [tag.id for tag in tag_records]
            
            if tag_ids:
                # Filter contacts that have ANY of the specified tags
                query = query.filter(Contact.tags.any(Tag.id.in_(tag_ids)))
    
    # Filter by groups
    if groups:
        group_names = [name.strip() for name in groups.split(',') if name.strip()]
        if group_names:
            # Get group IDs for the given names
            group_records = db.query(Group).filter(Group.name.in_(group_names)).all()
            group_ids = [group.id for group in group_records]
            
            if group_ids:
                # Filter contacts that have ANY of the specified groups
                query = query.filter(Contact.groups.any(Group.id.in_(group_ids)))
    
    # Sorting
    sort_field = getattr(Contact, sort_by, Contact.id)
    if sort_order.lower() == 'asc':
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Get total count before pagination
    total = query.count()
    
    # Calculate pagination
    pages = (total + limit - 1) // limit  # Ceiling division
    offset = (page - 1) * limit
    
    # Apply pagination
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


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
    Automatically formats phone numbers and detects duplicates if enabled.
    """
    payload = data.dict()
    if not payload.get('uid'):
        payload['uid'] = uuid.uuid4().hex
    
    # Format phone numbers
    if payload.get('phone'):
        payload['phone'] = format_phone_number(payload['phone'])
    if payload.get('phone_mobile'):
        payload['phone_mobile'] = format_phone_number(payload['phone_mobile'])
    if payload.get('phone_work'):
        payload['phone_work'] = format_phone_number(payload['phone_work'])
    if payload.get('phone_additional'):
        payload['phone_additional'] = format_phone_number(payload['phone_additional'])
    
    contact = Contact(**payload)
    db.add(contact)
    db.flush()  # Get ID without committing
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='created',
        entity_type='contact',
        changes=payload
    )
    
    db.commit()
    db.refresh(contact)
    
    # Update contact metrics
    contacts_created_counter.inc()
    contacts_total.set(db.query(Contact).count())
    
    # Auto-detect duplicates if enabled
    try:
        duplicate_enabled = get_system_setting(db, 'duplicate_detection_enabled', 'true')
        if duplicate_enabled.lower() == 'true':
            threshold = float(get_system_setting(db, 'duplicate_similarity_threshold', '0.75'))
            
            # Get existing contacts for comparison
            existing_contacts = db.query(Contact).filter(Contact.id != contact.id).all()
            
            # Convert to dict for comparison
            contact_dict = {
                'id': contact.id,
                'full_name': contact.full_name,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'middle_name': contact.middle_name,
                'email': contact.email,
                'phone': contact.phone,
                'phone_mobile': contact.phone_mobile,
                'phone_work': contact.phone_work,
                'company': contact.company,
                'position': contact.position,
            }
            
            existing_dicts = [{
                'id': c.id,
                'full_name': c.full_name,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'middle_name': c.middle_name,
                'email': c.email,
                'phone': c.phone,
                'phone_mobile': c.phone_mobile,
                'phone_work': c.phone_work,
                'company': c.company,
                'position': c.position,
            } for c in existing_contacts]
            
            # Find duplicates
            duplicates = duplicate_utils.find_duplicates_for_new_contact(contact_dict, existing_dicts, threshold)
            
            # Save duplicates to database
            for existing_contact_dict, score, field_scores in duplicates:
                existing_id = existing_contact_dict['id']
                id1, id2 = sorted([contact.id, existing_id])
                
                # Check if already exists
                existing_dup = db.query(DuplicateContact).filter(
                    (DuplicateContact.contact_id_1 == id1) & (DuplicateContact.contact_id_2 == id2)
                ).first()
                
                if not existing_dup:
                    new_dup = DuplicateContact(
                        contact_id_1=id1,
                        contact_id_2=id2,
                        similarity_score=score,
                        match_fields=field_scores,
                        status='pending',
                        auto_detected=True
                    )
                    db.add(new_dup)
            
            db.commit()
    except Exception as e:
        # Don't fail contact creation if duplicate detection fails
        logger.error(f"Duplicate detection error: {e}")
    
    return contact


@router.put('/{contact_id}')
def update_contact(
    contact_id: int,
    data: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Update an existing contact.
    Automatically formats phone numbers.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    update_data = data.dict(exclude_unset=True)
    
    # Format phone numbers
    if 'phone' in update_data and update_data['phone']:
        update_data['phone'] = format_phone_number(update_data['phone'])
    if 'phone_mobile' in update_data and update_data['phone_mobile']:
        update_data['phone_mobile'] = format_phone_number(update_data['phone_mobile'])
    if 'phone_work' in update_data and update_data['phone_work']:
        update_data['phone_work'] = format_phone_number(update_data['phone_work'])
    if 'phone_additional' in update_data and update_data['phone_additional']:
        update_data['phone_additional'] = format_phone_number(update_data['phone_additional'])
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='updated',
        entity_type='contact',
        changes=update_data
    )
    
    for k, v in update_data.items():
        if hasattr(contact, k):
            setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    
    # Update metrics
    contacts_updated_counter.inc()
    
    return contact


@router.delete('/{contact_id}')
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Delete a contact.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Audit log (before deletion)
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='deleted',
        entity_type='contact',
        changes={'full_name': contact.full_name, 'company': contact.company}
    )
    
    db.delete(contact)
    db.commit()
    
    # Update metrics
    contacts_deleted_counter.inc()
    contacts_total.set(db.query(Contact).count())
    
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

