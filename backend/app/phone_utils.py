"""
Phone number formatting utilities.
"""
import re


def format_phone_number(phone: str) -> str:
    """
    Format phone number to a standardized format.
    
    Supports:
    - Russian numbers: +7 (XXX) XXX-XX-XX
    - International numbers: +XX (XXX) XXX-XXXX
    
    Examples:
        89991234567 -> +7 (999) 123-45-67
        +79991234567 -> +7 (999) 123-45-67
        79991234567 -> +7 (999) 123-45-67
        9991234567 -> +7 (999) 123-45-67
        +1234567890 -> +1 (234) 567-890
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters except '+'
    clean = re.sub(r'[^\d+]', '', phone)
    
    # If empty after cleaning, return original
    if not clean or clean == '+':
        return phone
    
    # Remove leading '+' for processing
    has_plus = clean.startswith('+')
    digits = clean.lstrip('+')
    
    # Handle Russian numbers
    if digits.startswith('8') and len(digits) == 11:
        # 8XXXXXXXXXX -> +7 (XXX) XXX-XX-XX
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif digits.startswith('7') and len(digits) == 11:
        # 7XXXXXXXXXX -> +7 (XXX) XXX-XX-XX
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif not has_plus and len(digits) == 10:
        # XXXXXXXXXX (assume Russian, no country code) -> +7 (XXX) XXX-XX-XX
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    
    # Handle international numbers
    elif len(digits) >= 10:
        if len(digits) == 11 and digits[0] == '1':
            # US/Canada: 1XXXXXXXXXX -> +1 (XXX) XXX-XXXX
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        elif len(digits) >= 11:
            # International: +CCXXXXXXXXXX -> +CC (XXX) XXX-XXXX
            country_code = digits[:-10]
            rest = digits[-10:]
            return f"+{country_code} ({rest[0:3]}) {rest[3:6]}-{rest[6:10]}"
        else:
            # Short international
            return f"+{digits}"
    
    # If nothing matched, return with + if it was present
    return ('+' + digits) if has_plus else digits


def normalize_phone_for_search(phone: str) -> str:
    """
    Normalize phone number for searching/comparison.
    Removes all non-digit characters except leading '+'.
    
    Examples:
        +7 (999) 123-45-67 -> +79991234567
        8 999 123-45-67 -> +79991234567
    """
    if not phone:
        return ''
    
    # Remove all non-digit characters except '+'
    clean = re.sub(r'[^\d+]', '', phone)
    
    # Convert 8XXXXXXXXXX to +7XXXXXXXXXX for Russian numbers
    if clean.startswith('8') and len(clean) == 11:
        return '+7' + clean[1:]
    elif clean.startswith('7') and len(clean) == 11 and not clean.startswith('+'):
        return '+' + clean
    
    return clean

