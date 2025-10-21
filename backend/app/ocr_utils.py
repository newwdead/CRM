"""
Utility functions for OCR data processing and parsing.
"""
import re
from typing import Dict, Optional, List


def parse_russian_name(full_name: str) -> Dict[str, Optional[str]]:
    """
    Parse Russian full name into components (last_name, first_name, middle_name).
    
    Examples:
        "Иванов Иван Иванович" -> {last_name: "Иванов", first_name: "Иван", middle_name: "Иванович"}
        "Петров Петр" -> {last_name: "Петров", first_name: "Петр", middle_name: None}
    """
    if not full_name or not full_name.strip():
        return {"last_name": None, "first_name": None, "middle_name": None}
    
    # Remove extra whitespace
    name_parts = [part.strip() for part in full_name.split() if part.strip()]
    
    result = {"last_name": None, "first_name": None, "middle_name": None}
    
    if len(name_parts) >= 1:
        result["last_name"] = name_parts[0]
    if len(name_parts) >= 2:
        result["first_name"] = name_parts[1]
    if len(name_parts) >= 3:
        result["middle_name"] = name_parts[2]
    
    return result


def detect_company_and_position(text: str, current_company: Optional[str] = None, 
                                 current_position: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Improved detection of company and position from OCR text.
    Sometimes OCR confuses company with position and vice versa.
    
    Rules:
    1. Position keywords: директор, менеджер, специалист, инженер, руководитель, 
                          заместитель, начальник, координатор, аналитик, etc.
    2. Company indicators: ООО, ЗАО, ОАО, АО, ИП, Ltd, Inc, Corp, GmbH, etc.
    3. If both provided, check if they're swapped
    """
    
    # Position keywords (case-insensitive)
    position_keywords = [
        'директор', 'менеджер', 'специалист', 'инженер', 'руководитель',
        'заместитель', 'начальник', 'координатор', 'аналитик', 'консультант',
        'администратор', 'секретарь', 'бухгалтер', 'юрист', 'адвокат',
        'программист', 'разработчик', 'дизайнер', 'маркетолог', 'продавец',
        'manager', 'director', 'engineer', 'specialist', 'coordinator',
        'analyst', 'consultant', 'administrator', 'developer', 'designer',
        'ceo', 'cto', 'cfo', 'coo', 'head', 'chief', 'senior', 'junior',
        'ведущий', 'старший', 'младший', 'главный'
    ]
    
    # Company legal forms
    company_indicators = [
        'ооо', 'зао', 'оао', 'ао', 'ип', 'пао', 'нпо', 'нко',
        'ltd', 'inc', 'corp', 'corporation', 'gmbh', 'llc', 'sa',
        'limited', 'company', 'enterprises', 'group', 'холдинг'
    ]
    
    result = {
        "company": current_company,
        "position": current_position
    }
    
    # If both are empty, return as is
    if not current_company and not current_position:
        return result
    
    # Check if company actually looks like a position
    if current_company:
        company_lower = current_company.lower()
        if any(keyword in company_lower for keyword in position_keywords):
            # Company looks like a position
            if not current_position:
                # Swap them
                result["position"] = current_company
                result["company"] = None
            elif not any(indicator in company_lower for indicator in company_indicators):
                # Definitely swapped
                result["position"] = current_company
                result["company"] = current_position
    
    # Check if position actually looks like a company
    if current_position:
        position_lower = current_position.lower()
        if any(indicator in position_lower for indicator in company_indicators):
            # Position looks like a company
            if not current_company:
                # Swap them
                result["company"] = current_position
                result["position"] = None
            elif not any(keyword in position_lower for keyword in position_keywords):
                # Definitely swapped
                result["company"] = current_position
                result["position"] = current_company
    
    return result


def enhance_ocr_result(ocr_data: Dict, raw_text: str = "") -> Dict:
    """
    Enhance OCR result with improved parsing.
    
    This function:
    1. Parses full_name into components (first, last, middle names)
    2. Extracts and categorizes multiple phone numbers
    3. Extracts multiple addresses
    4. Detects and fixes swapped company/position
    5. Cleans and normalizes data
    """
    result = ocr_data.copy()
    
    # Parse full name into components
    if 'full_name' in result and result['full_name']:
        name_parts = parse_russian_name(result['full_name'])
        result.update(name_parts)
    
    # Parse multiple phone numbers from raw text
    if raw_text:
        phone_data = parse_phone_numbers(raw_text)
        # Only update if we found something better
        if phone_data.get('phone_mobile') and not result.get('phone_mobile'):
            result['phone_mobile'] = phone_data['phone_mobile']
        if phone_data.get('phone_work') and not result.get('phone_work'):
            result['phone_work'] = phone_data['phone_work']
        if phone_data.get('phone_additional') and not result.get('phone_additional'):
            result['phone_additional'] = phone_data['phone_additional']
        if phone_data.get('phone') and not result.get('phone'):
            result['phone'] = phone_data['phone']
    
    # Extract addresses from raw text
    if raw_text:
        address_data = extract_addresses(raw_text)
        if address_data.get('address') and not result.get('address'):
            result['address'] = address_data['address']
        if address_data.get('address_additional') and not result.get('address_additional'):
            result['address_additional'] = address_data['address_additional']
    
    # Detect and fix company/position swap
    if 'company' in result or 'position' in result:
        corrected = detect_company_and_position(
            raw_text,
            result.get('company'),
            result.get('position')
        )
        result['company'] = corrected['company']
        result['position'] = corrected['position']
    
    # Set source
    if 'source' not in result:
        result['source'] = 'ocr'
    
    # Set default status
    if 'status' not in result:
        result['status'] = 'active'
    
    return result


def is_mobile_phone(phone: str) -> bool:
    """
    Determine if a phone number is mobile (cellular) based on patterns.
    
    Rules:
    - Russian mobile: +7 9XX, 8 9XX
    - International mobile: typically longer (10+ digits)
    - Landline: shorter, often has area codes like (495), (812), etc.
    """
    # Clean phone number
    digits_only = re.sub(r'\D', '', phone)
    
    # Russian mobile patterns
    if digits_only.startswith('79') or digits_only.startswith('89'):
        return True
    
    # If starts with +7 and second digit is 9, it's mobile
    if phone.startswith('+7') and len(digits_only) > 1 and digits_only[1] == '9':
        return True
    
    # Landline indicators (Russian area codes)
    landline_codes = ['495', '499', '812', '843', '846', '383']  # Moscow, SPb, Kazan, etc.
    for code in landline_codes:
        if code in digits_only[:5]:
            return False
    
    # If 10+ digits and no landline indicators, likely mobile
    if len(digits_only) >= 10:
        return True
    
    return False


def parse_phone_numbers(text: str) -> Dict[str, Optional[str]]:
    """
    Extract and categorize multiple phone numbers from text.
    
    Returns:
        Dict with keys: phone, phone_mobile, phone_work, phone_additional
    """
    if not text:
        return {
            "phone": None,
            "phone_mobile": None,
            "phone_work": None,
            "phone_additional": None
        }
    
    # Regex patterns for phone numbers
    phone_patterns = [
        r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}',  # International
        r'\d{1}\s?\(\d{3,4}\)\s?\d{3}[\-\s]?\d{2}[\-\s]?\d{2}',  # 8 (XXX) XXX-XX-XX
        r'\+\d[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',  # +7 XXX XXX XX XX
        r'\d{10,15}'  # Simple 10-15 digit numbers
    ]
    
    phones = []
    for pattern in phone_patterns:
        found = re.findall(pattern, text)
        phones.extend(found)
    
    # Remove duplicates and clean
    phones = list(dict.fromkeys([p.strip() for p in phones if p.strip()]))
    
    result = {
        "phone": None,
        "phone_mobile": None,
        "phone_work": None,
        "phone_additional": None
    }
    
    mobile_phones = []
    work_phones = []
    
    for phone in phones:
        if is_mobile_phone(phone):
            mobile_phones.append(phone)
        else:
            work_phones.append(phone)
    
    # Assign phones to fields
    if mobile_phones:
        result["phone_mobile"] = mobile_phones[0]
        result["phone"] = mobile_phones[0]  # Main phone is mobile if available
        
        if len(mobile_phones) > 1:
            if not work_phones:  # Second mobile becomes work if no work phones
                result["phone_work"] = mobile_phones[1]
                            else:
                result["phone_additional"] = mobile_phones[1]
    
    if work_phones:
        result["phone_work"] = work_phones[0]
        if not result["phone"]:  # If no mobile, work becomes main
            result["phone"] = work_phones[0]
        
        if len(work_phones) > 1:
            result["phone_additional"] = work_phones[1]
    
    return result


def extract_addresses(text: str) -> Dict[str, Optional[str]]:
    """
    Extract addresses from text.
    
    Addresses often contain:
    - Street names (ул., улица, пр., проспект, etc.)
    - Building/house numbers (д., дом, строение, корп.)
    - City names (г., город, Москва, СПб, etc.)
    
    Returns:
        Dict with keys: address, address_additional
    """
    if not text:
        return {"address": None, "address_additional": None}
    
    # Address indicators
    address_keywords = [
        r'адрес[:\s]+',
        r'ул\.?\s+',
        r'улица\s+',
        r'пр\.?\s+',
        r'проспект\s+',
        r'пер\.?\s+',
        r'переулок\s+',
        r'наб\.?\s+',
        r'набережная\s+',
        r'г\.?\s+',
        r'город\s+',
        r'д\.?\s+\d+',
        r'дом\s+\d+',
        r'корп\.?\s+\d+',
        r'стр\.?\s+\d+',
        r'office\s+',
        r'офис\s+'
    ]
    
    addresses = []
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        # Check if line contains address keywords
        for keyword in address_keywords:
            if re.search(keyword, line_lower):
                # This line likely contains an address
                addresses.append(line.strip())
                                break
    
    # Remove duplicates
    addresses = list(dict.fromkeys(addresses))
    
    result = {"address": None, "address_additional": None}
    
    if len(addresses) > 0:
        result["address"] = addresses[0]
    if len(addresses) > 1:
        result["address_additional"] = addresses[1]
    
    return result
