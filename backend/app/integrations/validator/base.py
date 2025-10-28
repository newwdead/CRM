"""
Base Validator class
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """Base class for all validators"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def validate(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """
        Validate and correct a field value
        
        Args:
            data: Full contact data dict
            field: Field name (e.g., "email", "phone")
            value: Field value to validate
        
        Returns:
            {
                "valid": bool,
                "corrected_value": Any,
                "confidence": float,
                "issues": List[str]
            }
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if validator is enabled"""
        return self.enabled
    
    def enable(self):
        """Enable validator"""
        self.enabled = True
        logger.info(f"✅ {self.name} validator enabled")
    
    def disable(self):
        """Disable validator"""
        self.enabled = False
        logger.info(f"⏸️ {self.name} validator disabled")

