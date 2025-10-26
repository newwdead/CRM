"""
Regex Validator
Pattern-based validation for emails, phones, websites
"""
import re
import logging
from typing import Optional

from .base import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class RegexValidator(BaseValidator):
    """
    Regex-based validator for common OCR fields
    
    Validates:
    - Email addresses
    - Phone numbers
    - Websites/URLs
    - Postal codes
    """
    
    # Regex patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?[\d\s\-\(\)]{7,20}$'
    WEBSITE_PATTERN = r'^(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    POSTAL_CODE_PATTERN = r'^\d{5,6}$'  # Simple postal code
    
    def __init__(self):
        super().__init__("Regex")
    
    def validate(self, value: str, field_name: Optional[str] = None) -> ValidationResult:
        """
        Validate value using regex patterns
        
        Args:
            value: Value to validate
            field_name: Field name (email, phone, website, etc.)
        
        Returns:
            ValidationResult
        """
        if not value or not value.strip():
            return ValidationResult(
                is_valid=False,
                original_value=value,
                field_name=field_name,
                error_message="Empty value",
                confidence=0.0
            )
        
        value = value.strip()
        
        # Auto-detect field type if not provided
        if not field_name:
            field_name = self._detect_field_type(value)
        
        # Validate based on field type
        if field_name == 'email':
            return self._validate_email(value)
        elif field_name in ['phone', 'phone_mobile', 'phone_work']:
            return self._validate_phone(value)
        elif field_name == 'website':
            return self._validate_website(value)
        elif field_name == 'postal_code':
            return self._validate_postal_code(value)
        else:
            # Generic validation - just check it's not empty
            return ValidationResult(
                is_valid=True,
                original_value=value,
                field_name=field_name,
                confidence=0.8
            )
    
    def _detect_field_type(self, value: str) -> Optional[str]:
        """Auto-detect field type from value"""
        if '@' in value:
            return 'email'
        elif re.search(r'\d{7,}', value):
            return 'phone'
        elif value.startswith(('http://', 'https://', 'www.')):
            return 'website'
        return None
    
    def _validate_email(self, value: str) -> ValidationResult:
        """Validate email address"""
        # Clean common OCR errors
        corrected = value.replace(' ', '')  # Remove spaces
        corrected = corrected.replace(',', '.')  # Common OCR error
        corrected = corrected.lower()
        
        # Common OCR character errors
        corrections = {
            '0': 'o',  # Zero vs O
            '1': 'l',  # One vs l (in some contexts)
        }
        
        is_valid = bool(re.match(self.EMAIL_PATTERN, corrected))
        
        return ValidationResult(
            is_valid=is_valid,
            original_value=value,
            corrected_value=corrected if corrected != value else None,
            field_name='email',
            confidence=0.95 if is_valid else 0.3,
            error_message=None if is_valid else "Invalid email format"
        )
    
    def _validate_phone(self, value: str) -> ValidationResult:
        """Validate phone number"""
        # Extract digits
        digits_only = re.sub(r'\D', '', value)
        
        # Normalize phone format
        if len(digits_only) >= 10:
            # Format: +X (XXX) XXX-XXXX
            if len(digits_only) == 10:
                corrected = f"+1 ({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
            elif len(digits_only) == 11:
                corrected = f"+{digits_only[0]} ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
            else:
                corrected = f"+{digits_only[:2]} {digits_only[2:]}"
            
            is_valid = True
            confidence = 0.9
        else:
            corrected = value
            is_valid = False
            confidence = 0.3
        
        return ValidationResult(
            is_valid=is_valid,
            original_value=value,
            corrected_value=corrected if corrected != value else None,
            field_name='phone',
            confidence=confidence,
            error_message=None if is_valid else "Phone number too short"
        )
    
    def _validate_website(self, value: str) -> ValidationResult:
        """Validate website/URL"""
        corrected = value.lower().strip()
        
        # Add https:// if missing
        if not corrected.startswith(('http://', 'https://')):
            if corrected.startswith('www.'):
                corrected = 'https://' + corrected
            else:
                corrected = 'https://www.' + corrected
        
        is_valid = bool(re.match(self.WEBSITE_PATTERN, corrected))
        
        return ValidationResult(
            is_valid=is_valid,
            original_value=value,
            corrected_value=corrected if corrected != value else None,
            field_name='website',
            confidence=0.9 if is_valid else 0.4,
            error_message=None if is_valid else "Invalid website format"
        )
    
    def _validate_postal_code(self, value: str) -> ValidationResult:
        """Validate postal code"""
        # Extract digits
        digits_only = re.sub(r'\D', '', value)
        
        is_valid = bool(re.match(self.POSTAL_CODE_PATTERN, digits_only))
        
        return ValidationResult(
            is_valid=is_valid,
            original_value=value,
            corrected_value=digits_only if digits_only != value else None,
            field_name='postal_code',
            confidence=0.85 if is_valid else 0.4,
            error_message=None if is_valid else "Invalid postal code format"
        )

