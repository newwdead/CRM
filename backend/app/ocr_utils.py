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


def enhance_ocr_result(ocr_data: Dict) -> Dict:
    """
    Enhance OCR result with improved name parsing and company/position detection.
    
    This function:
    1. Parses full_name into components
    2. Detects and fixes swapped company/position
    3. Cleans and normalizes data
    """
    result = ocr_data.copy()
    
    # Parse full name
    if 'full_name' in result and result['full_name']:
        name_parts = parse_russian_name(result['full_name'])
        result.update(name_parts)
    
    # Detect and fix company/position swap
    if 'company' in result or 'position' in result:
        corrected = detect_company_and_position(
            "",  # We don't have full text here
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


def parse_phone_numbers(phone: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Parse multiple phone numbers and categorize them.
    
    Returns:
        Dict with keys: phone (main), phone_mobile, phone_work
    """
    if not phone:
        return {"phone": None, "phone_mobile": None, "phone_work": None}
    
    # Split by common separators
    phones = re.split(r'[,;/|]', phone)
    phones = [p.strip() for p in phones if p.strip()]
    
    result = {"phone": None, "phone_mobile": None, "phone_work": None}
    
    if len(phones) > 0:
        result["phone"] = phones[0]
    if len(phones) > 1:
        result["phone_mobile"] = phones[1]
    if len(phones) > 2:
        result["phone_work"] = phones[2]
    
    return result
