"""
PaddleOCR Provider - High accuracy OCR with bounding boxes
Supports multiple languages and provides spatial layout information
"""
import io
import os
import re
import logging
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional
from abc import ABC

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not installed. Install with: pip install paddleocr paddlepaddle")

from .base import OCRProvider

logger = logging.getLogger(__name__)


class PaddleOCRProvider(OCRProvider):
    """
    PaddleOCR Provider - Local, high-accuracy OCR with layout detection
    
    Features:
    - Text recognition with bounding boxes
    - Multi-language support (English, Russian, Chinese, etc.)
    - Automatic text orientation detection
    - Layout analysis
    - Confidence scores per text block
    - Fast local processing (no API calls)
    
    Priority: 0 (Highest - will be tried first)
    """
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self.priority = 0  # Highest priority
        
        if not PADDLEOCR_AVAILABLE:
            self.enabled = False
            logger.error("PaddleOCR not available - provider disabled")
            return
        
        # Get configuration from environment
        use_gpu = os.getenv("PADDLEOCR_USE_GPU", "false").lower() == "true"
        lang = os.getenv("PADDLEOCR_LANG", "en")  # en, ru, ch, etc.
        use_angle_cls = os.getenv("PADDLEOCR_USE_ANGLE_CLS", "true").lower() == "true"
        det_model = os.getenv("PADDLEOCR_DET_MODEL", "en_PP-OCRv3_det")
        rec_model = os.getenv("PADDLEOCR_REC_MODEL", "en_PP-OCRv3_rec")
        
        try:
            # Initialize PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,  # Enable text rotation detection
                lang=lang,
                use_gpu=use_gpu,
                show_log=False,
                det_model_dir=det_model if det_model != "en_PP-OCRv3_det" else None,
                rec_model_dir=rec_model if rec_model != "en_PP-OCRv3_rec" else None,
            )
            logger.info(f"PaddleOCR initialized: lang={lang}, gpu={use_gpu}, angle_cls={use_angle_cls}")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.enabled = False
            self.ocr = None
    
    def is_available(self) -> bool:
        """Check if PaddleOCR is available"""
        return PADDLEOCR_AVAILABLE and self.enabled and self.ocr is not None
    
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Recognize text from image using PaddleOCR
        
        Args:
            image_data: Image bytes
            filename: Optional filename for logging
        
        Returns:
            Dict with:
                - provider: "PaddleOCR"
                - raw_text: Combined text from all blocks
                - blocks: List of detected text blocks with bbox and confidence
                - data: Parsed contact fields
                - confidence: Average confidence score
                - bbox_count: Number of detected bounding boxes
        """
        if not self.is_available():
            raise RuntimeError("PaddleOCR provider is not available")
        
        try:
            # Convert bytes to PIL Image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array for PaddleOCR
            img_np = np.array(img)
            
            # Run OCR
            logger.info(f"Running PaddleOCR on {filename or 'image'}")
            result = self.ocr.ocr(img_np, cls=True)
            
            if not result or not result[0]:
                logger.warning(f"PaddleOCR returned empty result for {filename}")
                return {
                    'provider': self.name,
                    'raw_text': '',
                    'blocks': [],
                    'data': self._empty_data(),
                    'confidence': 0.0,
                    'bbox_count': 0
                }
            
            # Extract blocks with bounding boxes
            blocks = []
            all_text = []
            confidences = []
            
            for line in result[0]:
                if not line or len(line) < 2:
                    continue
                
                bbox, (text, confidence) = line
                
                # Store structured block data
                blocks.append({
                    'text': text,
                    'bbox': bbox,  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    'confidence': float(confidence)
                })
                
                all_text.append(text)
                confidences.append(confidence)
            
            # Combine all text
            combined_text = '\n'.join(all_text)
            avg_confidence = float(np.mean(confidences)) if confidences else 0.0
            
            # Parse contact fields from text
            parsed_data = self._parse_text(combined_text, blocks)
            
            logger.info(
                f"PaddleOCR completed: {len(blocks)} blocks, "
                f"avg confidence: {avg_confidence:.2f}"
            )
            
            return {
                'provider': self.name,
                'raw_text': combined_text,
                'blocks': blocks,  # NEW: Structured blocks with coordinates
                'data': parsed_data,
                'confidence': avg_confidence,
                'bbox_count': len(blocks)
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR recognition failed: {e}", exc_info=True)
            raise
    
    def _parse_text(self, text: str, blocks: List[Dict] = None) -> Dict[str, Optional[str]]:
        """
        Parse text and extract contact fields
        
        Args:
            text: Combined text from all blocks
            blocks: Optional list of blocks for layout-aware parsing
        
        Returns:
            Dict with contact fields
        """
        data = self._empty_data()
        
        # Email extraction
        email_pattern = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, text, re.IGNORECASE)
        if email_match:
            data['email'] = email_match.group(0).lower()
        
        # Phone extraction (international format support)
        phone_patterns = [
            r'\+?\d[\d\s\-\(\)]{7,}\d',  # General international
            r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}',  # Detailed international
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',  # US format
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                data['phone'] = phone_match.group(0).strip()
                break
        
        # Website/URL extraction
        website_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9\-]+\.(com|net|org|io|ru|de|fr|uk)[^\s]*'
        ]
        
        for pattern in website_patterns:
            website_match = re.search(pattern, text, re.IGNORECASE)
            if website_match:
                website = website_match.group(0)
                # Clean up trailing punctuation
                website = re.sub(r'[,;.]+$', '', website)
                if not website.startswith(('http://', 'https://')):
                    website = 'https://' + website
                data['website'] = website
                break
        
        # Split into lines for field extraction
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # Remove lines that contain email, phone, or website
        candidate_lines = []
        for line in lines:
            if data['email'] and data['email'] in line.lower():
                continue
            if data['phone'] and data['phone'] in line:
                continue
            if data['website'] and data['website'] in line.lower():
                continue
            candidate_lines.append(line)
        
        # Extract name, company, position from remaining lines
        if candidate_lines:
            # First line is usually the name
            data['full_name'] = candidate_lines[0]
        
        if len(candidate_lines) > 1:
            # Second line could be position or company
            # Use heuristic: if it contains common position keywords, it's a position
            position_keywords = ['CEO', 'CTO', 'CFO', 'Manager', 'Director', 'Engineer', 
                                'Developer', 'Designer', 'Consultant', 'Specialist',
                                'President', 'Vice', 'Head', 'Lead', 'Senior', 'Junior']
            
            second_line = candidate_lines[1]
            is_position = any(keyword.lower() in second_line.lower() for keyword in position_keywords)
            
            if is_position:
                data['position'] = second_line
                if len(candidate_lines) > 2:
                    data['company'] = candidate_lines[2]
            else:
                data['company'] = second_line
                if len(candidate_lines) > 2:
                    data['position'] = candidate_lines[2]
        
        # Address extraction (look for keywords)
        address_keywords = [
            'Street', 'St.', 'Ave', 'Avenue', 'Road', 'Rd.', 'Boulevard', 'Blvd',
            'ул.', 'улица', 'просп', 'проспект', 'пер.', 'переулок',
            'straße', 'str.', 'бул.', 'бульвар'
        ]
        
        for line in lines:
            # Check if line contains address keywords or has numbers followed by street name
            if any(keyword.lower() in line.lower() for keyword in address_keywords):
                data['address'] = line
                break
            # Check for pattern: number followed by text
            if re.search(r'\d+\s+[A-Za-z]', line):
                data['address'] = line
                break
        
        return data
    
    def _empty_data(self) -> Dict[str, Optional[str]]:
        """Return empty data structure"""
        return {
            'full_name': None,
            'company': None,
            'position': None,
            'email': None,
            'phone': None,
            'address': None,
            'website': None,
        }

