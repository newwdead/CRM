"""
Base Validator
Abstract base class for all validators
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation"""
    
    is_valid: bool
    original_value: str
    corrected_value: Optional[str] = None
    confidence: float = 1.0
    field_name: Optional[str] = None
    error_message: Optional[str] = None
    suggestions: list = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'original_value': self.original_value,
            'corrected_value': self.corrected_value,
            'confidence': self.confidence,
            'field_name': self.field_name,
            'error_message': self.error_message,
            'suggestions': self.suggestions,
        }


class BaseValidator(ABC):
    """
    Base class for all validators
    
    Validators check and correct OCR-extracted data
    """
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def validate(self, value: str, field_name: Optional[str] = None) -> ValidationResult:
        """
        Validate a value
        
        Args:
            value: Value to validate
            field_name: Optional field name for context
        
        Returns:
            ValidationResult
        """
        pass
    
    def is_available(self) -> bool:
        """Check if validator is available"""
        return self.enabled
    
    def __str__(self):
        return f"{self.name} Validator"

