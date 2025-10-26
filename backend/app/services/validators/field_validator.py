"""
Field Validator
Validates all business card fields
"""
import logging
from typing import Dict, List, Optional

from .base import BaseValidator, ValidationResult
from .regex_validator import RegexValidator

logger = logging.getLogger(__name__)


class FieldValidator(BaseValidator):
    """
    Comprehensive field validator for business card data
    
    Orchestrates multiple validators:
    - Regex validation for structured fields
    - Length checks
    - Required fields validation
    """
    
    # Required fields for business card
    REQUIRED_FIELDS = {'full_name'}
    
    # Field constraints
    MAX_LENGTHS = {
        'full_name': 100,
        'company': 150,
        'position': 100,
        'email': 150,
        'phone': 30,
        'phone_mobile': 30,
        'phone_work': 30,
        'website': 200,
        'address': 300,
        'notes': 1000,
    }
    
    def __init__(self):
        super().__init__("Field")
        self.regex_validator = RegexValidator()
    
    def validate(self, value: str, field_name: Optional[str] = None) -> ValidationResult:
        """
        Validate a single field
        
        Args:
            value: Field value
            field_name: Field name
        
        Returns:
            ValidationResult
        """
        if not field_name:
            return ValidationResult(
                is_valid=False,
                original_value=value,
                error_message="Field name required",
                confidence=0.0
            )
        
        # Check if empty
        if not value or not value.strip():
            is_required = field_name in self.REQUIRED_FIELDS
            return ValidationResult(
                is_valid=not is_required,
                original_value=value,
                field_name=field_name,
                error_message="Required field is empty" if is_required else None,
                confidence=0.0 if is_required else 1.0
            )
        
        value = value.strip()
        
        # Check length
        max_length = self.MAX_LENGTHS.get(field_name, 500)
        if len(value) > max_length:
            return ValidationResult(
                is_valid=False,
                original_value=value,
                corrected_value=value[:max_length],
                field_name=field_name,
                error_message=f"Value too long (max {max_length} chars)",
                confidence=0.5
            )
        
        # Specific field validation
        if field_name in ['email', 'phone', 'phone_mobile', 'phone_work', 'website', 'postal_code']:
            return self.regex_validator.validate(value, field_name)
        
        # Generic text validation
        return ValidationResult(
            is_valid=True,
            original_value=value,
            field_name=field_name,
            confidence=0.8
        )
    
    def validate_all(self, data: Dict[str, str]) -> Dict[str, ValidationResult]:
        """
        Validate all fields in contact data
        
        Args:
            data: Dictionary of field_name -> value
        
        Returns:
            Dictionary of field_name -> ValidationResult
        """
        results = {}
        
        for field_name, value in data.items():
            results[field_name] = self.validate(value, field_name)
        
        # Check for missing required fields
        for required_field in self.REQUIRED_FIELDS:
            if required_field not in data or not data[required_field]:
                results[required_field] = ValidationResult(
                    is_valid=False,
                    original_value="",
                    field_name=required_field,
                    error_message="Required field missing",
                    confidence=0.0
                )
        
        return results
    
    def get_corrected_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Get corrected version of data
        
        Args:
            data: Original data
        
        Returns:
            Corrected data with fixes applied
        """
        validation_results = self.validate_all(data)
        corrected = {}
        
        for field_name, result in validation_results.items():
            if result.corrected_value:
                corrected[field_name] = result.corrected_value
            elif field_name in data:
                corrected[field_name] = data[field_name]
        
        return corrected
    
    def get_validation_summary(self, data: Dict[str, str]) -> Dict[str, any]:
        """
        Get validation summary with statistics
        
        Args:
            data: Data to validate
        
        Returns:
            Summary dictionary
        """
        results = self.validate_all(data)
        
        total_fields = len(results)
        valid_fields = sum(1 for r in results.values() if r.is_valid)
        corrected_fields = sum(1 for r in results.values() if r.corrected_value)
        avg_confidence = sum(r.confidence for r in results.values()) / total_fields if total_fields > 0 else 0
        
        errors = [
            {
                'field': r.field_name,
                'error': r.error_message,
                'original': r.original_value,
                'corrected': r.corrected_value
            }
            for r in results.values()
            if not r.is_valid or r.corrected_value
        ]
        
        return {
            'total_fields': total_fields,
            'valid_fields': valid_fields,
            'corrected_fields': corrected_fields,
            'avg_confidence': round(avg_confidence, 2),
            'errors': errors,
            'is_valid': valid_fields == total_fields,
        }

