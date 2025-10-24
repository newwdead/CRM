"""
Telegram integration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests
import os
import uuid
import logging

from ..database import get_db
from ..models import User, AppSetting
from ..core.auth import get_current_active_user, get_current_admin_user
from ..integrations.ocr import image_processing

router = APIRouter()
logger = logging.getLogger(__name__)


class TelegramSettings(BaseModel):
    enabled: bool
    token: str | None = None
    allowed_chats: str | None = None
    provider: str = 'auto'


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    """Get a setting value from database"""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value if setting else default


def set_setting(db: Session, key: str, value: str | None):
    """Set a setting value in database"""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
        db.add(setting)
    db.commit()


@router.get('/settings/telegram')
def get_telegram_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get Telegram integration settings"""
    return {
        'enabled': get_setting(db, 'tg.enabled', 'false') == 'true',
        'token': get_setting(db, 'tg.token', None),
        'allowed_chats': get_setting(db, 'tg.allowed_chats', ''),
        'provider': get_setting(db, 'tg.provider', 'auto') or 'auto',
    }


@router.put('/settings/telegram')
def update_telegram_settings(
    data: TelegramSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update Telegram integration settings (admin only)"""
    set_setting(db, 'tg.enabled', 'true' if data.enabled else 'false')
    set_setting(db, 'tg.token', (data.token or '').strip() or None)
    set_setting(db, 'tg.allowed_chats', (data.allowed_chats or '').strip())
    set_setting(db, 'tg.provider', (data.provider or 'auto'))
    return {'ok': True}


@router.post('/telegram/webhook')
def telegram_webhook(
    update: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Receive Telegram webhook updates.
    Automatically processes business card images sent via Telegram.
    """
    from ..models import Contact
    from ..utils import process_single_card, create_thumbnail
    
    try:
        # Check if Telegram is enabled
        if get_setting(db, 'tg.enabled', 'false') != 'true':
            return {'ignored': 'disabled'}
        
        token = get_setting(db, 'tg.token', None)
        if not token:
            raise HTTPException(status_code=400, detail='Telegram token not configured')
        
        # Extract message
        message = update.get('message') or update.get('edited_message')
        if not message:
            return {'ignored': 'no_message'}
        
        # Check if chat is allowed
        chat_id = str(message.get('chat', {}).get('id')) if message.get('chat') else None
        allowed = (get_setting(db, 'tg.allowed_chats', '') or '').strip()
        if allowed:
            allowed_set = {x.strip() for x in allowed.split(',') if x.strip()}
            if chat_id not in allowed_set:
                return {'ignored': 'chat_not_allowed'}
        
        # Check for photos
        photos = message.get('photo') or []
        if not photos:
            return {'ignored': 'no_photo'}
        
        # Choose largest photo
        best = max(photos, key=lambda p: (p.get('width', 0) or 0) * (p.get('height', 0) or 0))
        file_id = best.get('file_id')
        if not file_id:
            raise HTTPException(status_code=400, detail='No file_id in photo')
        
        # Get file path from Telegram API
        api = f'https://api.telegram.org/bot{token}'
        r = requests.get(f'{api}/getFile', params={'file_id': file_id}, timeout=15)
        r.raise_for_status()
        file_path = r.json().get('result', {}).get('file_path')
        if not file_path:
            raise HTTPException(status_code=400, detail='Cannot get file_path')
        
        # Download file
        file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'
        img_res = requests.get(file_url, timeout=30)
        img_res.raise_for_status()
        content = img_res.content
        
        # Process image - detect and split multiple cards
        logger.info("Telegram: Processing image with auto_crop=True, detect_multi=True")
        processed_cards = image_processing.process_business_card_image(
            content,
            auto_crop=True,
            detect_multi=True,
            enhance=False
        )
        
        logger.info(f"Telegram: {len(processed_cards)} card(s) detected")
        
        # Process each detected card
        created_contacts = []
        provider = get_setting(db, 'tg.provider', 'auto') or 'auto'
        
        for idx, card_bytes in enumerate(processed_cards[:5]):  # Limit to 5 cards
            logger.info(f"Telegram: Processing card {idx + 1}/{len(processed_cards)}")
            
            # Save card to uploads
            card_safe_name = f"{uuid.uuid4().hex}_tg_card{idx+1 if len(processed_cards) > 1 else ''}_{os.path.basename(file_path)}"
            card_save_path = os.path.join('uploads', card_safe_name)
            with open(card_save_path, 'wb') as f:
                f.write(card_bytes)
            
            # Create thumbnail
            card_thumbnail_path = create_thumbnail(card_save_path, size=(200, 200), quality=85)
            card_thumbnail_name = os.path.basename(card_thumbnail_path)
            
            # Process card using helper function
            card_data = process_single_card(
                card_bytes,
                card_safe_name,
                card_thumbnail_name,
                provider,
                os.path.basename(file_path),
                db
            )
            
            if card_data:
                created_contacts.append(card_data)
                logger.info(f"Telegram: Card {idx + 1} created, contact_id={card_data['id']}")
        
        # Return result
        if len(created_contacts) == 0:
            raise HTTPException(status_code=400, detail='No cards could be processed')
        elif len(created_contacts) == 1:
            return {'created_id': created_contacts[0]['id']}
        else:
            return {
                'created_ids': [c['id'] for c in created_contacts],
                'count': len(created_contacts),
                'message': f'{len(created_contacts)} business cards detected and processed'
            }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

