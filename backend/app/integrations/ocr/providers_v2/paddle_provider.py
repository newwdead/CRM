"""
PaddleOCR Provider v2.0
High-performance OCR with bounding boxes
"""
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import numpy as np

from .base import OCRProviderV2, TextBlock, BoundingBox

logger = logging.getLogger(__name__)


class PaddleOCRProvider(OCRProviderV2):
    """
    PaddleOCR Provider
    
    Features:
    - Fast and accurate OCR
    - Built-in text detection (bbox)
    - Multi-language support
    - No API keys needed
    - GPU support (if available)
    """
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self.priority = 1  # High priority (better than Tesseract)
        self.supports_bbox = True
        self.supports_layout = False  # True when LayoutLMv3 integrated
        
        self.ocr = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize PaddleOCR engine"""
        try:
            from paddleocr import PaddleOCR
            
            # Initialize with optimal settings for business cards
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification for rotated text
                lang='cyrillic',  # Cyrillic alphabet (Russian + other Cyrillic languages)
                use_gpu=False,  # Set to True if GPU available
                show_log=False,  # Reduce logging
                det_model_dir=None,  # Use default models
                rec_model_dir=None,
                cls_model_dir=None,
                # Text detection parameters for better block separation
                det_db_thresh=0.3,  # Lower threshold = more sensitive detection
                det_db_box_thresh=0.5,  # Box threshold for filtering
                det_db_unclip_ratio=1.6,  # Unclip ratio for text region expansion
                # Image size limits - prevent auto-resize for high-res business cards
                det_limit_side_len=6000,  # Max side length (default: 960)
                det_limit_type='max',  # Limit type: 'max' or 'min'
            )
            
            logger.info(f"✅ {self.name} initialized successfully")
            
        except ImportError as e:
            logger.error(f"❌ PaddleOCR not installed: {e}")
            self.ocr = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize PaddleOCR: {e}")
            self.ocr = None
    
    def is_available(self) -> bool:
        """Check if PaddleOCR is available"""
        return self.ocr is not None
    
    def recognize(
        self, 
        image_data: bytes, 
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize text using PaddleOCR
        
        Returns enhanced result with bounding boxes
        """
        if not self.is_available():
            raise RuntimeError(f"{self.name} is not available")
        
        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(img)
            image_size = (img.width, img.height)
            
            # Run OCR
            result = self.ocr.ocr(img_array, cls=True)
            
            # Parse results into TextBlocks
            blocks = []
            all_text = []
            total_confidence = 0
            block_count = 0
            
            if result and result[0]:
                for idx, line in enumerate(result[0]):
                    if line:
                        # line format: [bbox, (text, confidence)]
                        bbox_coords = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        text, confidence = line[1]
                        
                        # Convert bbox to our format
                        x_coords = [p[0] for p in bbox_coords]
                        y_coords = [p[1] for p in bbox_coords]
                        
                        x = min(x_coords)
                        y = min(y_coords)
                        width = max(x_coords) - x
                        height = max(y_coords) - y
                        
                        bbox = BoundingBox(x=x, y=y, width=width, height=height)
                        
                        block = TextBlock(
                            text=text,
                            bbox=bbox,
                            confidence=confidence,
                            block_id=idx
                        )
                        
                        blocks.append(block)
                        all_text.append(text)
                        total_confidence += confidence
                        block_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / block_count if block_count > 0 else 0.0
            
            # Combine text
            raw_text = "\n".join(all_text)
            
            # Normalize to structured fields
            data = self.normalize_result(blocks, image_size)
            
            logger.info(
                f"✅ {self.name} recognized {block_count} blocks, "
                f"avg confidence: {avg_confidence:.2f}"
            )
            
            return {
                "provider": self.name,
                "raw_text": raw_text,
                "blocks": blocks,  # TextBlock objects
                "data": data,
                "confidence": avg_confidence,
                "image_size": image_size,
                "block_count": block_count,
                "image_data": image_data,  # For LayoutLMv3 (Phase 2)
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name} recognition failed: {e}", exc_info=True)
            raise
    
    def recognize_with_layout(
        self,
        image_data: bytes,
        layoutlm_classifier=None
    ) -> Dict[str, Any]:
        """
        Enhanced recognition with LayoutLMv3 classification
        
        Args:
            image_data: Image bytes
            layoutlm_classifier: LayoutLMv3 model for field classification
        
        Returns:
            Enhanced result with field classifications
        """
        # First, get standard OCR results with bboxes
        result = self.recognize(image_data)
        
        if layoutlm_classifier and result.get('blocks'):
            # TODO: Integrate LayoutLMv3 classification
            # This will be implemented in Phase 2
            logger.info(f"📊 LayoutLMv3 classification will be added in Phase 2")
            pass
        
        return result

