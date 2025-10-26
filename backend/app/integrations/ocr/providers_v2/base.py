"""
Base OCR Provider v2.0
Enhanced with bounding box support and layout understanding
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box for text region"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def x2(self) -> float:
        return self.x + self.width
    
    @property
    def y2(self) -> float:
        return self.y + self.height
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'x2': self.x2,
            'y2': self.y2,
        }


@dataclass
class TextBlock:
    """Text block with position and confidence"""
    text: str
    bbox: BoundingBox
    confidence: float
    block_id: Optional[int] = None
    field_type: Optional[str] = None  # For LayoutLMv3 classification


class OCRProviderV2(ABC):
    """
    Base class for OCR providers v2.0
    
    Enhanced with:
    - Bounding box detection
    - Layout understanding
    - Confidence scores per block
    - Support for LayoutLMv3 integration
    """
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.priority = 0  # Lower number = higher priority
        self.supports_bbox = False  # Override in subclasses
        self.supports_layout = False  # Override for LayoutLM-capable providers
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured"""
        pass
    
    @abstractmethod
    def recognize(
        self, 
        image_data: bytes, 
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize text from image
        
        Args:
            image_data: Image bytes
            filename: Optional filename for context
        
        Returns:
            {
                'provider': str,
                'raw_text': str,
                'blocks': List[TextBlock],  # NEW in v2.0
                'data': Dict[str, str],
                'confidence': float,
                'image_size': Tuple[int, int],  # NEW in v2.0
            }
        """
        pass
    
    def normalize_result(
        self, 
        blocks: List[TextBlock],
        image_size: Tuple[int, int]
    ) -> Dict[str, Optional[str]]:
        """
        Normalize OCR blocks into structured fields
        
        This is a fallback regex-based method.
        Override for ML-based classification (LayoutLMv3)
        
        Args:
            blocks: List of text blocks with positions
            image_size: (width, height) of original image
        
        Returns:
            Dictionary with extracted fields
        """
        import re
        
        # Combine all text for regex extraction
        combined_text = "\n".join([block.text for block in blocks])
        
        data = {
            "full_name": None,
            "company": None,
            "position": None,
            "email": None,
            "phone": None,
            "phone_mobile": None,
            "phone_work": None,
            "address": None,
            "website": None,
        }
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', combined_text)
        if email_match:
            data["email"] = email_match.group(0)
        
        # Phone (multiple formats)
        phone_patterns = [
            r'\+?\d[\d\s\-\(\)]{6,}\d',
            r'\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}',
            r'\(\d{3}\)\s?\d{3}[-\.\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, combined_text)
            if phone_match:
                data["phone"] = phone_match.group(0).strip()
                break
        
        # Website
        website_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9][a-zA-Z0-9-]+\.(com|net|org|ru|co\.uk|de|fr|io|ai)'
        ]
        for pattern in website_patterns:
            website_match = re.search(pattern, combined_text, re.IGNORECASE)
            if website_match:
                data["website"] = website_match.group(0)
                break
        
        # Name heuristic (usually at top of card)
        if blocks:
            # Get blocks from top 30% of image
            top_blocks = [b for b in blocks if b.bbox.y < image_size[1] * 0.3]
            if top_blocks:
                # Longest text in top area is likely the name
                top_blocks.sort(key=lambda b: len(b.text), reverse=True)
                potential_name = top_blocks[0].text.strip()
                if len(potential_name) > 2 and not any(c in potential_name for c in ['@', 'http', '+', '(']):
                    data["full_name"] = potential_name
        
        return data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get provider metadata"""
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "available": self.is_available(),
            "supports_bbox": self.supports_bbox,
            "supports_layout": self.supports_layout,
        }

