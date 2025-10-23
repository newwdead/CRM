"""
OCR Blocks Management API
Handles OCR block editing, field mapping, and re-recognition
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import io
import json

from ..database import get_db
from ..models.contact import Contact
from .. import auth_utils, tesseract_boxes
from ..models.user import User

router = APIRouter()


@router.post('/{contact_id}/ocr-rerecognize-block')
def rerecognize_block(
    contact_id: int,
    block_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Re-recognize OCR for a specific block area.
    Used when user modifies block boundaries.
    
    Params:
        block_data: {
            "box": {"x": 10, "y": 20, "width": 100, "height": 30},
            "block_index": 0
        }
    
    Returns:
        New recognized text for this block
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.photo_path:
        raise HTTPException(status_code=400, detail='Contact has no image')
    
    box = block_data.get('box', {})
    block_index = block_data.get('block_index', 0)
    
    # Validate box
    if not all(k in box for k in ['x', 'y', 'width', 'height']):
        raise HTTPException(status_code=400, detail='Invalid box format')
    
    # Load image
    from ..settings import UPLOAD_DIR
    import os
    from PIL import Image
    
    image_path = os.path.join(UPLOAD_DIR, contact.photo_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail='Image not found')
    
    try:
        # Crop image to block area
        img = Image.open(image_path)
        crop_box = (
            int(box['x']),
            int(box['y']),
            int(box['x'] + box['width']),
            int(box['y'] + box['height'])
        )
        cropped_img = img.crop(crop_box)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Run OCR on cropped region
        from ..settings import get_setting
        tesseract_langs = get_setting(db, 'TESSERACT_LANGS', 'rus+eng')
        result = tesseract_boxes.get_text_blocks(img_bytes, lang=tesseract_langs)
        
        # Combine all text from blocks
        text = ' '.join([block.get('text', '') for block in result.get('blocks', [])])
        
        return {
            'block_index': block_index,
            'text': text.strip(),
            'box': box,
            'confidence': sum([b.get('confidence', 0) for b in result.get('blocks', [])]) / max(len(result.get('blocks', [])), 1)
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error re-recognizing block: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to re-recognize block: {str(e)}')


@router.post('/{contact_id}/save-field-mappings')
def save_field_mappings(
    contact_id: int,
    mappings_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Save field mappings for OCR blocks.
    
    Params:
        mappings_data: {
            "blocks": [
                {
                    "text": "Иванов",
                    "box": {...},
                    "field": "last_name",  # Mapped field
                    "confidence": 0.95
                },
                ...
            ]
        }
    
    This saves both the blocks AND applies the field mappings to the contact.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    blocks = mappings_data.get('blocks', [])
    
    # Apply field mappings to contact
    for block in blocks:
        field_name = block.get('field')
        text = block.get('text', '').strip()
        
        if field_name and text and hasattr(contact, field_name):
            # Map block text directly to field
            setattr(contact, field_name, text)
    
    # Save blocks to ocr_raw for future reference
    ocr_data = {
        'blocks': blocks,
        'timestamp': str(contact.updated_at or '')
    }
    contact.ocr_raw = json.dumps(ocr_data, ensure_ascii=False)
    
    db.commit()
    db.refresh(contact)
    
    return {
        'status': 'success',
        'message': 'Field mappings saved',
        'updated_fields': [block.get('field') for block in blocks if block.get('field')]
    }


@router.get('/{contact_id}/available-fields')
def get_available_fields(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get list of available contact fields for mapping.
    Returns fields with their current values and labels.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Define mappable fields
    fields = [
        {'name': 'first_name', 'label': 'Имя', 'label_en': 'First Name', 'type': 'text'},
        {'name': 'last_name', 'label': 'Фамилия', 'label_en': 'Last Name', 'type': 'text'},
        {'name': 'middle_name', 'label': 'Отчество', 'label_en': 'Middle Name', 'type': 'text'},
        {'name': 'company', 'label': 'Компания', 'label_en': 'Company', 'type': 'text'},
        {'name': 'position', 'label': 'Должность', 'label_en': 'Position', 'type': 'text'},
        {'name': 'email', 'label': 'Email', 'label_en': 'Email', 'type': 'email'},
        {'name': 'phone', 'label': 'Телефон', 'label_en': 'Phone', 'type': 'phone'},
        {'name': 'phone_mobile', 'label': 'Мобильный', 'label_en': 'Mobile', 'type': 'phone'},
        {'name': 'phone_work', 'label': 'Рабочий тел.', 'label_en': 'Work Phone', 'type': 'phone'},
        {'name': 'phone_additional', 'label': 'Доп. телефон', 'label_en': 'Additional Phone', 'type': 'phone'},
        {'name': 'address', 'label': 'Адрес', 'label_en': 'Address', 'type': 'text'},
        {'name': 'address_additional', 'label': 'Доп. адрес', 'label_en': 'Additional Address', 'type': 'text'},
        {'name': 'website', 'label': 'Веб-сайт', 'label_en': 'Website', 'type': 'url'},
        {'name': 'comment', 'label': 'Комментарий', 'label_en': 'Comment', 'type': 'text'}
    ]
    
    # Add current values
    for field in fields:
        field['current_value'] = getattr(contact, field['name'], '')
    
    return {
        'fields': fields,
        'contact_id': contact_id
    }

