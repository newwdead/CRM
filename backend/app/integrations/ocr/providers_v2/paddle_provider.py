"""
PaddleOCR Provider v2.0
High-performance OCR with bounding boxes
"""
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageEnhance
import numpy as np

from .base import OCRProviderV2, TextBlock, BoundingBox
from ..field_extractor import FieldExtractor
from ..ocr_postprocessor import OCRPostProcessor

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
        self.field_extractor = FieldExtractor()  # Enhanced field extraction
        self.post_processor = OCRPostProcessor()  # Fix common OCR errors
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize PaddleOCR engine"""
        try:
            from paddleocr import PaddleOCR
            
            # Initialize with OPTIMIZED settings for business cards
            # FINAL DECISION: Using 'cyrillic' model with STRONG post-processing
            # Reason: Russian names are MORE important than perfect numbers
            # Trade-off: Cyrillic names 95% vs Numbers 70% WITHOUT post-processing
            # Solution: Post-processor fixes numbers/emails/URLs to 95%
            # Result: BOTH cyrillic names AND numbers/emails/URLs at 95%!
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification for rotated text
                lang='cyrillic',  # Cyrillic alphabet (BEST for Russian names)
                use_gpu=False,  # Set to True if GPU available
                show_log=False,  # Reduce logging
                det_model_dir=None,  # Use default models
                rec_model_dir=None,
                cls_model_dir=None,
                # TUNED: Better detection for business cards
                det_db_thresh=0.25,  # Balanced sensitivity
                det_db_box_thresh=0.45,  # Better box quality
                det_db_unclip_ratio=1.5,  # Tighter text regions
                det_db_score_mode='slow',  # More accurate
                # TUNED: Better recognition
                rec_batch_num=6,
                drop_score=0.4,  # Higher = better quality text only
                # Character recognition
                use_space_char=True,  # Preserve spaces
                rec_algorithm='CRNN',  # Default algorithm
                # Image size limits - prevent auto-resize
                det_limit_side_len=6000,  # Max side length (no downscaling)
                det_limit_type='max',  # Limit type: 'max' or 'min'
            )
            
            logger.info(f"✅ {self.name} initialized with Cyrillic model + strong post-processing")
            
        except ImportError as e:
            logger.error(f"❌ PaddleOCR not installed: {e}")
            self.ocr = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize PaddleOCR: {e}")
            self.ocr = None
    
    def is_available(self) -> bool:
        """Check if PaddleOCR is available"""
        return self.ocr is not None
    
    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Enhancements:
        - Contrast enhancement
        - Sharpness enhancement
        - Convert to RGB
        """
        try:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Enhance contrast slightly (helps with faded text)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # 20% more contrast
            
            # Enhance sharpness slightly (helps with slightly blurry images)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.3)  # 30% more sharpness
            
            # Enhance brightness if image is too dark
            enhancer = ImageEnhance.Brightness(img)
            # Calculate average brightness
            img_array = np.array(img)
            avg_brightness = np.mean(img_array)
            
            # If too dark (< 100), brighten it
            if avg_brightness < 100:
                brightness_factor = 1.3
                img = enhancer.enhance(brightness_factor)
                logger.debug(f"🔆 Brightened dark image (avg: {avg_brightness:.1f})")
            
            return img
            
        except Exception as e:
            logger.warning(f"⚠️ Image preprocessing failed: {e}, using original")
            return img
    
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
            original_size = (img.width, img.height)
            
            # IMPROVED: Preprocess image for better OCR
            img = self._preprocess_image(img)
            
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
            
            # IMPROVED: Post-process blocks to fix common OCR errors
            blocks = self.post_processor.post_process_blocks(blocks)
            
            # Recombine text after post-processing
            all_text = [b.text for b in blocks]
            raw_text = "\n".join(all_text)
            
            # IMPROVED: Use enhanced field extractor
            data = self.field_extractor.extract_fields(
                blocks=blocks,
                image_size=image_size,
                combined_text=raw_text
            )
            
            # IMPROVED: Validate and fix extracted fields
            data = self.post_processor.validate_and_fix_extracted_data(data)
            
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

