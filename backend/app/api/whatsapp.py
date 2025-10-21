"""
WhatsApp integration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from sqlalchemy.orm import Session
import logging
import json

from ..database import get_db
from ..models import User, Contact
from ..auth_utils import get_current_admin_user
from ..core.metrics import telegram_messages_counter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/webhook')
def whatsapp_webhook_verify(
    request: Request,
    hub_mode: str = Query(None, alias='hub.mode'),
    hub_challenge: str = Query(None, alias='hub.challenge'),
    hub_verify_token: str = Query(None, alias='hub.verify_token')
):
    """
    Verify WhatsApp webhook.
    This endpoint is called by Meta/Facebook to verify webhook configuration.
    """
    from .. import whatsapp_utils
    
    logger.info(f"WhatsApp webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == 'subscribe':
        if whatsapp_utils.verify_webhook_token(hub_verify_token):
            logger.info("WhatsApp webhook verified successfully")
            return int(hub_challenge)
        else:
            logger.warning("WhatsApp webhook verification failed: invalid token")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Invalid request")


@router.post('/webhook')
async def whatsapp_webhook_receive(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive WhatsApp webhook messages.
    Automatically processes business card images sent via WhatsApp.
    """
    from .. import whatsapp_utils
    from ..tasks import process_single_card
    
    try:
        body = await request.json()
        logger.info(f"WhatsApp webhook received: {json.dumps(body, indent=2)[:500]}")
        
        # Parse incoming message
        message_data = whatsapp_utils.parse_webhook_message(body)
        
        if not message_data:
            # Respond with 200 to acknowledge receipt
            return {"status": "ok", "message": "No processable message"}
        
        # Check message type
        if message_data['type'] == 'image':
            # Download image
            media_id = message_data['image']['id']
            image_data = whatsapp_utils.download_media(media_id)
            
            if image_data:
                # Queue processing task
                task = process_single_card.delay(
                    image_data=image_data,
                    filename=f"whatsapp_{message_data['id']}.jpg",
                    provider='auto',
                    user_id=None  # WhatsApp messages don't have associated user
                )
                
                logger.info(f"WhatsApp image queued for processing: task_id={task.id}")
                
                # Send confirmation message back
                from_number = message_data['from']
                confirmation_text = (
                    "✅ Визитка получена! Обрабатываем...\n"
                    "Контакт будет добавлен автоматически."
                )
                whatsapp_utils.send_text_message(from_number, confirmation_text)
                
                # Update Prometheus metrics
                telegram_messages_counter.labels(status='success').inc()
            else:
                logger.error("Failed to download WhatsApp media")
                telegram_messages_counter.labels(status='failed').inc()
        
        elif message_data['type'] == 'text':
            # Handle text commands
            text = message_data['text'].lower().strip()
            from_number = message_data['from']
            
            if text in ['/start', 'привет', 'hello', 'help']:
                help_text = (
                    "👋 Добро пожаловать в ibbase!\n\n"
                    "📤 Отправьте фото визитки, и я автоматически создам контакт.\n\n"
                    "Команды:\n"
                    "/start - Это сообщение\n"
                    "/help - Помощь\n"
                    "/status - Статус системы"
                )
                whatsapp_utils.send_text_message(from_number, help_text)
            
            elif text == '/status':
                # Get system status
                contacts_count = db.query(Contact).count()
                status_text = (
                    f"📊 Статус системы:\n\n"
                    f"✅ Система работает\n"
                    f"📇 Контактов в базе: {contacts_count}\n"
                    f"🤖 Готов обрабатывать визитки!"
                )
                whatsapp_utils.send_text_message(from_number, status_text)
            
            else:
                whatsapp_utils.send_text_message(
                    from_number,
                    "Отправьте фото визитки для автоматического создания контакта."
                )
        
        # Acknowledge receipt
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        telegram_messages_counter.labels(status='failed').inc()
        # Still return 200 to avoid webhook retry storms
        return {"status": "error", "message": str(e)}


@router.post('/send')
def whatsapp_send_message(
    to: str = Body(..., description="Recipient phone number"),
    message: str = Body(..., description="Message text"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Send a WhatsApp message.
    Admin only.
    """
    from .. import whatsapp_utils
    
    result = whatsapp_utils.send_text_message(to, message)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {"status": "sent", "result": result}

