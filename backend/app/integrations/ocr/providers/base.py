"""
Base OCR Provider class
All OCR providers must inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class OCRProvider(ABC):
    """Base class for all OCR providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.priority = 0  # Lower number = higher priority
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured
        
        Returns:
            bool: True if provider can be used
        """
        pass
    
    @abstractmethod
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Recognize text from image
        
        Args:
            image_data: Image as bytes
            filename: Optional filename for logging
        
        Returns:
            Dict containing:
                - provider: str - Provider name
                - raw_text: str - Extracted text
                - data: Dict - Parsed contact fields
                - confidence: float - Confidence score (0.0 to 1.0)
                - blocks: List[Dict] - Optional text blocks with bounding boxes
        """
        pass
    
    def normalize_result(self, raw_data: Any) -> Dict[str, Optional[str]]:
        """
        Normalize provider-specific result to standard format
        
        Returns:
            Dict with standard contact fields
        """
        return {
            "full_name": None,
            "company": None,
            "position": None,
            "email": None,
            "phone": None,
            "address": None,
            "website": None,
        }

