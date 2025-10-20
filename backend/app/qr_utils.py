"""
QR Code scanning and vCard/MeCard parsing utilities.
"""
import io
import re
import logging
from typing import Optional, Dict, Any
from PIL import Image
import cv2
import numpy as np
from pyzbar.pyzbar import decode

logger = logging.getLogger(__name__)


def scan_qr_code(image_bytes: bytes) -> Optional[str]:
    """
    Scan QR code from image bytes.
    Returns decoded string or None if no QR code found.
    """
    try:
        # Convert bytes to PIL Image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert PIL Image to numpy array for pyzbar
        img_array = np.array(img)
        
        # Decode QR codes
        decoded_objects = decode(img_array)
        
        if not decoded_objects:
            logger.info("No QR codes found in image")
            return None
        
        # Return first QR code data
        qr_data = decoded_objects[0].data.decode('utf-8', errors='ignore')
        logger.info(f"QR code found, length: {len(qr_data)} characters")
        
        return qr_data
        
    except Exception as e:
        logger.error(f"Error scanning QR code: {e}")
        return None


def parse_vcard(vcard_string: str) -> Dict[str, Any]:
    """
    Parse vCard format (BEGIN:VCARD ... END:VCARD).
    Returns dict with contact fields.
    """
    contact_data = {}
    
    try:
        import vobject
        
        # Parse vCard
        vcard = vobject.readOne(vcard_string)
        
        # Extract name
        if hasattr(vcard, 'fn'):
            contact_data['full_name'] = vcard.fn.value
        
        if hasattr(vcard, 'n'):
            n = vcard.n.value
            if hasattr(n, 'family'):
                contact_data['last_name'] = n.family
            if hasattr(n, 'given'):
                contact_data['first_name'] = n.given
            if hasattr(n, 'additional'):
                contact_data['middle_name'] = n.additional
        
        # Extract organization
        if hasattr(vcard, 'org'):
            org = vcard.org.value
            if isinstance(org, list) and org:
                contact_data['company'] = org[0]
            elif isinstance(org, str):
                contact_data['company'] = org
        
        # Extract title/position
        if hasattr(vcard, 'title'):
            contact_data['position'] = vcard.title.value
        
        # Extract email
        if hasattr(vcard, 'email_list'):
            emails = [email.value for email in vcard.email_list]
            if emails:
                contact_data['email'] = emails[0]
        
        # Extract phone
        if hasattr(vcard, 'tel_list'):
            phones = [tel.value for tel in vcard.tel_list]
            if phones:
                contact_data['phone'] = phones[0]
            if len(phones) > 1:
                contact_data['phone_mobile'] = phones[1]
        
        # Extract address
        if hasattr(vcard, 'adr_list'):
            adr = vcard.adr_list[0].value
            address_parts = []
            if hasattr(adr, 'street'):
                address_parts.append(adr.street)
            if hasattr(adr, 'city'):
                address_parts.append(adr.city)
            if hasattr(adr, 'region'):
                address_parts.append(adr.region)
            if hasattr(adr, 'code'):
                address_parts.append(adr.code)
            if address_parts:
                contact_data['address'] = ', '.join(filter(None, address_parts))
        
        # Extract URL
        if hasattr(vcard, 'url_list'):
            urls = [url.value for url in vcard.url_list]
            if urls:
                contact_data['website'] = urls[0]
        
        logger.info(f"vCard parsed successfully: {list(contact_data.keys())}")
        
    except Exception as e:
        logger.error(f"Error parsing vCard with vobject: {e}")
        # Fallback to regex parsing
        contact_data = parse_vcard_regex(vcard_string)
    
    return contact_data


def parse_vcard_regex(vcard_string: str) -> Dict[str, Any]:
    """
    Parse vCard using regex as fallback.
    More robust for non-standard vCards.
    """
    contact_data = {}
    
    try:
        # Full name
        fn_match = re.search(r'FN[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if fn_match:
            contact_data['full_name'] = fn_match.group(1).strip()
        
        # Name components (N:Family;Given;Additional;Prefix;Suffix)
        n_match = re.search(r'N[;:]([^;\n\r]*);([^;\n\r]*);?([^;\n\r]*)', vcard_string, re.IGNORECASE)
        if n_match:
            last_name, first_name, middle_name = n_match.groups()
            if last_name:
                contact_data['last_name'] = last_name.strip()
            if first_name:
                contact_data['first_name'] = first_name.strip()
            if middle_name:
                contact_data['middle_name'] = middle_name.strip()
        
        # Organization
        org_match = re.search(r'ORG[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if org_match:
            contact_data['company'] = org_match.group(1).strip().split(';')[0]
        
        # Title
        title_match = re.search(r'TITLE[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if title_match:
            contact_data['position'] = title_match.group(1).strip()
        
        # Email
        email_match = re.search(r'EMAIL[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if email_match:
            contact_data['email'] = email_match.group(1).strip()
        
        # Phone (multiple possible)
        tel_matches = re.findall(r'TEL[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if tel_matches:
            contact_data['phone'] = tel_matches[0].strip()
            if len(tel_matches) > 1:
                contact_data['phone_mobile'] = tel_matches[1].strip()
        
        # Address
        adr_match = re.search(r'ADR[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if adr_match:
            adr_parts = adr_match.group(1).split(';')
            adr_clean = ', '.join(filter(None, [part.strip() for part in adr_parts]))
            if adr_clean:
                contact_data['address'] = adr_clean
        
        # URL
        url_match = re.search(r'URL[;:]([^\n\r]+)', vcard_string, re.IGNORECASE)
        if url_match:
            contact_data['website'] = url_match.group(1).strip()
        
        logger.info(f"vCard parsed with regex: {list(contact_data.keys())}")
        
    except Exception as e:
        logger.error(f"Error parsing vCard with regex: {e}")
    
    return contact_data


def parse_mecard(mecard_string: str) -> Dict[str, Any]:
    """
    Parse MeCard format (MECARD:N:Name;TEL:123;...).
    Popular in Japan, simpler than vCard.
    """
    contact_data = {}
    
    try:
        # Remove MECARD: prefix
        data = mecard_string.replace('MECARD:', '', 1)
        
        # Parse fields
        fields = re.findall(r'([A-Z]+):([^;]+)', data)
        
        for field_name, field_value in fields:
            field_value = field_value.strip()
            
            if field_name == 'N':  # Name
                # Format: Last,First or just Full Name
                if ',' in field_value:
                    parts = field_value.split(',', 1)
                    contact_data['last_name'] = parts[0].strip()
                    if len(parts) > 1:
                        contact_data['first_name'] = parts[1].strip()
                else:
                    contact_data['full_name'] = field_value
            
            elif field_name == 'TEL':  # Phone
                if 'phone' not in contact_data:
                    contact_data['phone'] = field_value
                else:
                    contact_data['phone_mobile'] = field_value
            
            elif field_name == 'EMAIL':
                contact_data['email'] = field_value
            
            elif field_name == 'ORG':
                contact_data['company'] = field_value
            
            elif field_name == 'ADR':
                contact_data['address'] = field_value
            
            elif field_name == 'URL':
                contact_data['website'] = field_value
            
            elif field_name == 'NOTE':
                contact_data['comment'] = field_value
        
        logger.info(f"MeCard parsed successfully: {list(contact_data.keys())}")
        
    except Exception as e:
        logger.error(f"Error parsing MeCard: {e}")
    
    return contact_data


def extract_contact_from_qr(qr_data: str) -> Optional[Dict[str, Any]]:
    """
    Extract contact data from QR code string.
    Supports vCard and MeCard formats.
    Returns dict with contact fields or None.
    """
    if not qr_data:
        return None
    
    try:
        # Check if it's vCard
        if 'BEGIN:VCARD' in qr_data.upper():
            logger.info("Detected vCard format")
            return parse_vcard(qr_data)
        
        # Check if it's MeCard
        elif qr_data.upper().startswith('MECARD:'):
            logger.info("Detected MeCard format")
            return parse_mecard(qr_data)
        
        # Unknown format
        else:
            logger.warning(f"Unknown QR format: {qr_data[:50]}...")
            return None
    
    except Exception as e:
        logger.error(f"Error extracting contact from QR: {e}")
        return None


def process_image_with_qr(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Main function: scan QR code and extract contact data.
    Returns dict with contact fields or None if no valid QR found.
    """
    try:
        # Scan QR code
        qr_data = scan_qr_code(image_bytes)
        
        if not qr_data:
            return None
        
        # Extract contact data
        contact_data = extract_contact_from_qr(qr_data)
        
        if contact_data:
            logger.info(f"Successfully extracted contact from QR: {contact_data.get('full_name') or contact_data.get('first_name')}")
        
        return contact_data
        
    except Exception as e:
        logger.error(f"Error processing image with QR: {e}")
        return None

