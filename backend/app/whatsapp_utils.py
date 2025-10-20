"""
WhatsApp Business API integration utilities
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# WhatsApp Business API configuration
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', 'https://graph.facebook.com/v18.0')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID', '')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'ibbase_verify_token_2024')


def verify_webhook_token(token: str) -> bool:
    """
    Verify webhook verification token from WhatsApp.
    
    Args:
        token: Token provided by WhatsApp
        
    Returns:
        True if token matches
    """
    return token == WHATSAPP_VERIFY_TOKEN


def send_text_message(to: str, text: str) -> Dict[str, Any]:
    """
    Send a text message via WhatsApp Business API.
    
    Args:
        to: Recipient phone number (with country code, e.g. "79001234567")
        text: Message text
        
    Returns:
        API response dict
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp API not configured")
        return {"error": "WhatsApp API not configured"}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return {"error": str(e)}


def send_image_message(to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an image message via WhatsApp Business API.
    
    Args:
        to: Recipient phone number
        image_url: Public URL of the image
        caption: Optional image caption
        
    Returns:
        API response dict
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp API not configured")
        return {"error": "WhatsApp API not configured"}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url
        }
    }
    
    if caption:
        payload["image"]["caption"] = caption
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send WhatsApp image: {e}")
        return {"error": str(e)}


def download_media(media_id: str) -> Optional[bytes]:
    """
    Download media file from WhatsApp.
    
    Args:
        media_id: Media ID from WhatsApp webhook
        
    Returns:
        Media file bytes or None
    """
    if not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp API not configured")
        return None
    
    try:
        # Step 1: Get media URL
        url = f"{WHATSAPP_API_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        media_data = response.json()
        
        media_url = media_data.get('url')
        if not media_url:
            logger.error("No media URL in response")
            return None
        
        # Step 2: Download media
        media_response = requests.get(media_url, headers=headers, timeout=30)
        media_response.raise_for_status()
        
        return media_response.content
        
    except Exception as e:
        logger.error(f"Failed to download WhatsApp media: {e}")
        return None


def parse_webhook_message(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse incoming WhatsApp webhook message.
    
    Args:
        data: Webhook payload from WhatsApp
        
    Returns:
        Parsed message dict or None
    """
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        messages = value.get('messages', [])
        if not messages:
            return None
        
        message = messages[0]
        
        result = {
            'from': message.get('from'),
            'timestamp': message.get('timestamp'),
            'type': message.get('type'),
            'id': message.get('id')
        }
        
        # Parse different message types
        if message['type'] == 'text':
            result['text'] = message.get('text', {}).get('body')
            
        elif message['type'] == 'image':
            image_data = message.get('image', {})
            result['image'] = {
                'id': image_data.get('id'),
                'mime_type': image_data.get('mime_type'),
                'sha256': image_data.get('sha256'),
                'caption': image_data.get('caption')
            }
            
        elif message['type'] == 'document':
            doc_data = message.get('document', {})
            result['document'] = {
                'id': doc_data.get('id'),
                'filename': doc_data.get('filename'),
                'mime_type': doc_data.get('mime_type'),
                'sha256': doc_data.get('sha256'),
                'caption': doc_data.get('caption')
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to parse WhatsApp webhook: {e}")
        return None


def send_template_message(
    to: str,
    template_name: str,
    language_code: str = "ru",
    parameters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send a template message via WhatsApp Business API.
    
    Args:
        to: Recipient phone number
        template_name: Name of the approved message template
        language_code: Template language (e.g., "ru", "en")
        parameters: List of parameter values for the template
        
    Returns:
        API response dict
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp API not configured")
        return {"error": "WhatsApp API not configured"}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }
    
    if parameters:
        payload["template"]["components"] = [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            }
        ]
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template: {e}")
        return {"error": str(e)}

