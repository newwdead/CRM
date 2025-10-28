"""
Regex-based Validator
Validates emails, phones, websites using regex patterns
"""
import re
import logging
from typing import Dict, Any, Optional
from .base import BaseValidator

logger = logging.getLogger(__name__)


class RegexValidator(BaseValidator):
    """Regex-based validation for structured fields"""
    
    def __init__(self):
        super().__init__("Regex")
        
        # Patterns
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[1-9]\d{9,14}$',
            'website': r'^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$',
        }
        
        # Correction patterns
        self.corrections = {
            'email': [
                (r'(\w+)\s+@\s+(\w+)', r'\1@\2'),  # Space around @
                (r'@\s+', '@'),  # Space after @
                (r'\s+@', '@'),  # Space before @
            ],
            'phone': [
                (r'[^\d+]', ''),  # Remove non-digits except +
                (r'^8(\d{10})$', r'+7\1'),  # 8XXX → +7XXX
                (r'^7(\d{10})$', r'+7\1'),  # 7XXX → +7XXX
                (r'^(\d{10})$', r'+7\1'),  # XXX → +7XXX
            ],
            'website': [
                (r'^\s*(www\.)', r'https://\1'),  # www → https://www
                (r'^([a-z0-9-]+\.[a-z]+)', r'https://\1', re.I),  # domain → https://domain
            ]
        }
    
    def validate(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Validate field using regex"""
        if not value or not isinstance(value, str):
            return {
                "valid": False,
                "corrected_value": value,
                "confidence": 0.0,
                "issues": ["Empty or non-string value"]
            }
        
        value = value.strip()
        
        # Check if we have a pattern for this field
        if field not in self.patterns:
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 1.0,
                "issues": []
            }
        
        pattern = self.patterns[field]
        issues = []
        
        # Try direct match
        if re.match(pattern, value):
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 1.0,
                "issues": []
            }
        
        # Try corrections
        corrected = value
        if field in self.corrections:
            for regex, replacement, *flags in self.corrections[field]:
                flag = flags[0] if flags else 0
                corrected = re.sub(regex, replacement, corrected, flags=flag)
        
        # Check if correction worked
        if re.match(pattern, corrected):
            logger.debug(f"🔧 {field}: '{value}' → '{corrected}'")
            return {
                "valid": True,
                "corrected_value": corrected,
                "confidence": 0.8,
                "issues": [f"Corrected from: {value}"]
            }
        
        # Invalid
        issues.append(f"Does not match {field} pattern")
        return {
            "valid": False,
            "corrected_value": value,
            "confidence": 0.0,
            "issues": issues
        }
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Shortcut for email validation"""
        return self.validate({}, 'email', email)
    
    def validate_phone(self, phone: str) -> Dict[str, Any]:
        """Shortcut for phone validation"""
        return self.validate({}, 'phone', phone)
    
    def validate_website(self, website: str) -> Dict[str, Any]:
        """Shortcut for website validation"""
        return self.validate({}, 'website', website)

