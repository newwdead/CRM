"""
Validator Service
Coordinates all validators (Regex, GPT, spaCy)
"""
import logging
from typing import Dict, Any, List, Optional
from .regex_validator import RegexValidator
from .spacy_validator import SpacyValidator
from .gpt_validator import GPTValidator

logger = logging.getLogger(__name__)


class ValidatorService:
    """
    Validator Service - coordinates multiple validators
    
    Priority order:
    1. Regex (fast, deterministic)
    2. spaCy (medium, NER-based)
    3. GPT (slow, intelligent)
    """
    
    def __init__(self, use_gpt: bool = False):
        """
        Initialize validator service
        
        Args:
            use_gpt: Enable GPT validator (requires OPENAI_API_KEY)
        """
        # Initialize validators
        self.regex_validator = RegexValidator()
        self.spacy_validator = SpacyValidator()
        self.gpt_validator = GPTValidator() if use_gpt else None
        
        # Field priority map: which validators to use for each field
        self.field_validators = {
            'full_name': ['spacy', 'gpt'],
            'email': ['regex', 'gpt'],
            'phone': ['regex', 'gpt'],
            'phone_mobile': ['regex', 'gpt'],
            'phone_work': ['regex', 'gpt'],
            'website': ['regex', 'gpt'],
            'company': ['spacy', 'gpt'],
            'position': ['gpt'],
            'address': ['spacy', 'gpt'],
        }
        
        logger.info(f"✅ ValidatorService initialized (GPT: {use_gpt})")
    
    def validate_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all fields in contact data
        
        Args:
            data: Contact data dict
        
        Returns:
            {
                "original": original_data,
                "validated": corrected_data,
                "corrections": {field: {...}},
                "overall_confidence": float
            }
        """
        validated = {}
        corrections = {}
        confidences = []
        
        for field, value in data.items():
            if value and field in self.field_validators:
                result = self.validate_field(data, field, value)
                validated[field] = result['corrected_value']
                
                if result['corrected_value'] != value:
                    corrections[field] = {
                        'original': value,
                        'corrected': result['corrected_value'],
                        'confidence': result['confidence'],
                        'issues': result['issues']
                    }
                
                confidences.append(result['confidence'])
            else:
                # Pass through fields without validation
                validated[field] = value
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 1.0
        
        return {
            "original": data,
            "validated": validated,
            "corrections": corrections,
            "overall_confidence": overall_confidence
        }
    
    def validate_field(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """
        Validate single field using appropriate validators
        
        Args:
            data: Full contact data (for context)
            field: Field name
            value: Field value
        
        Returns:
            {
                "valid": bool,
                "corrected_value": Any,
                "confidence": float,
                "issues": List[str],
                "validator_used": str
            }
        """
        # Get validators for this field
        validator_names = self.field_validators.get(field, [])
        
        best_result = {
            "valid": True,
            "corrected_value": value,
            "confidence": 0.5,
            "issues": [],
            "validator_used": "none"
        }
        
        # Try each validator in order
        for validator_name in validator_names:
            validator = self._get_validator(validator_name)
            if not validator or not validator.is_enabled():
                continue
            
            try:
                result = validator.validate(data, field, value)
                result['validator_used'] = validator_name
                
                # Use result if confidence is higher
                if result['confidence'] > best_result['confidence']:
                    best_result = result
                
                # Stop if we have high confidence
                if result['confidence'] >= 0.9:
                    break
                    
            except Exception as e:
                logger.error(f"❌ {validator_name} validation error for {field}: {e}")
                continue
        
        return best_result
    
    def _get_validator(self, name: str):
        """Get validator by name"""
        validators = {
            'regex': self.regex_validator,
            'spacy': self.spacy_validator,
            'gpt': self.gpt_validator
        }
        return validators.get(name)
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Shortcut: validate email"""
        return self.validate_field({}, 'email', email)
    
    def validate_phone(self, phone: str) -> Dict[str, Any]:
        """Shortcut: validate phone"""
        return self.validate_field({}, 'phone', phone)
    
    def validate_name(self, name: str) -> Dict[str, Any]:
        """Shortcut: validate name"""
        return self.validate_field({}, 'full_name', name)
    
    def enable_gpt(self):
        """Enable GPT validator"""
        if not self.gpt_validator:
            self.gpt_validator = GPTValidator()
        if self.gpt_validator:
            self.gpt_validator.enable()
    
    def disable_gpt(self):
        """Disable GPT validator"""
        if self.gpt_validator:
            self.gpt_validator.disable()
    
    def get_status(self) -> Dict[str, Any]:
        """Get validator service status"""
        return {
            "regex": self.regex_validator.is_enabled(),
            "spacy": self.spacy_validator.is_enabled(),
            "gpt": self.gpt_validator.is_enabled() if self.gpt_validator else False
        }

