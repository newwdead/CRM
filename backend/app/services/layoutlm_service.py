"""
LayoutLMv3 Service - Field Classification using Layout-aware ML Model

This service uses Microsoft's LayoutLMv3 model to classify text blocks from OCR
into structured business card fields based on:
- Text content
- Spatial layout (bounding boxes)
- Visual features (image)

Model understands the context and layout of business cards to accurately
identify fields like name, position, company, email, phone, etc.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import torch

try:
    from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
    LAYOUTLM_AVAILABLE = True
except ImportError:
    LAYOUTLM_AVAILABLE = False
    logging.warning("LayoutLMv3 not available. Install with: pip install transformers torch")

logger = logging.getLogger(__name__)


class LayoutLMv3Service:
    """
    Service for field classification using LayoutLMv3
    
    Uses Microsoft's LayoutLMv3 model for:
    - Token classification (NER for business card fields)
    - Layout-aware understanding
    - Multi-modal learning (text + layout + vision)
    
    Model: microsoft/layoutlmv3-base (or fine-tuned version)
    Task: Token Classification
    Labels: NAME, POSITION, COMPANY, EMAIL, PHONE, ADDRESS, WEBSITE
    """
    
    # Label mapping for business card fields (BIO tagging scheme)
    LABEL2ID = {
        'O': 0,          # Other (not a field)
        'B-NAME': 1,     # Begin Name
        'I-NAME': 2,     # Inside Name
        'B-POSITION': 3, # Begin Position
        'I-POSITION': 4,
        'B-COMPANY': 5,
        'I-COMPANY': 6,
        'B-EMAIL': 7,
        'B-PHONE': 8,
        'I-PHONE': 9,
        'B-ADDRESS': 10,
        'I-ADDRESS': 11,
        'B-WEBSITE': 12,
        'I-WEBSITE': 13,
    }
    
    # Reverse mapping
    ID2LABEL = {v: k for k, v in LABEL2ID.items()}
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize LayoutLMv3 service
        
        Args:
            model_path: Path to fine-tuned model, or None for base model
        """
        if not LAYOUTLM_AVAILABLE:
            logger.error("LayoutLMv3 dependencies not installed")
            self.available = False
            return
        
        self.available = True
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Get model path from environment or use default
        model_name = model_path or os.getenv(
            'LAYOUTLMV3_MODEL_PATH',
            'microsoft/layoutlmv3-base'
        )
        
        try:
            logger.info(f"Loading LayoutLMv3 model: {model_name}")
            
            # Load processor and model
            self.processor = LayoutLMv3Processor.from_pretrained(
                model_name,
                apply_ocr=False  # We already have OCR from PaddleOCR
            )
            
            self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                model_name,
                num_labels=len(self.LABEL2ID),
                id2label=self.ID2LABEL,
                label2id=self.LABEL2ID
            )
            
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info(f"LayoutLMv3 loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load LayoutLMv3: {e}", exc_info=True)
            self.available = False
    
    def is_available(self) -> bool:
        """Check if LayoutLMv3 service is available"""
        return self.available and LAYOUTLM_AVAILABLE
    
    def classify_fields(
        self,
        image: Image.Image,
        ocr_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify OCR blocks into business card fields
        
        Args:
            image: PIL Image of the business card
            ocr_blocks: List of OCR blocks from PaddleOCR with 'text' and 'bbox'
        
        Returns:
            Dict with classified fields:
                - full_name: str
                - position: str
                - company: str
                - email: str
                - phone: str
                - address: str
                - website: str
                - confidence: float
                - predictions: List[Dict] (raw predictions)
        """
        if not self.is_available():
            logger.warning("LayoutLMv3 not available, returning empty result")
            return self._empty_result()
        
        if not ocr_blocks:
            logger.warning("No OCR blocks provided")
            return self._empty_result()
        
        try:
            # Extract words and bboxes from OCR blocks
            words = [block['text'] for block in ocr_blocks]
            boxes = [self._normalize_bbox(block['bbox'], image.size) for block in ocr_blocks]
            
            # Encode inputs
            encoding = self.processor(
                image,
                words,
                boxes=boxes,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512
            )
            
            # Move to device
            encoding = {k: v.to(self.device) for k, v in encoding.items()}
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**encoding)
                predictions = outputs.logits.argmax(-1).squeeze().tolist()
            
            # Handle single-token case (predictions is int, not list)
            if isinstance(predictions, int):
                predictions = [predictions]
            
            # Decode predictions
            result = self._decode_predictions(
                words,
                predictions,
                ocr_blocks
            )
            
            logger.info(f"LayoutLMv3 classified {len(words)} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"LayoutLMv3 classification failed: {e}", exc_info=True)
            return self._empty_result()
    
    def _normalize_bbox(self, bbox: List[List[int]], image_size: Tuple[int, int]) -> List[int]:
        """
        Normalize bbox coordinates to [0, 1000] scale
        
        LayoutLMv3 expects bboxes in format: [x_min, y_min, x_max, y_max]
        scaled to 1000x1000 coordinate space
        
        Args:
            bbox: PaddleOCR bbox [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            image_size: (width, height) of image
        
        Returns:
            Normalized bbox [x_min, y_min, x_max, y_max]
        """
        width, height = image_size
        
        # Extract coordinates from PaddleOCR format
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        
        # Normalize to 1000x1000 scale
        return [
            int(x_min / width * 1000),
            int(y_min / height * 1000),
            int(x_max / width * 1000),
            int(y_max / height * 1000)
        ]
    
    def _decode_predictions(
        self,
        words: List[str],
        predictions: List[int],
        ocr_blocks: List[Dict]
    ) -> Dict[str, Any]:
        """
        Decode model predictions into structured contact fields
        
        Uses BIO tagging scheme:
        - B-FIELD: Beginning of field
        - I-FIELD: Inside/continuation of field
        - O: Other (not a field)
        
        Args:
            words: List of words/tokens
            predictions: List of predicted label IDs
            ocr_blocks: Original OCR blocks with bbox
        
        Returns:
            Dict with extracted fields
        """
        # Initialize field map
        field_map = {
            'full_name': [],
            'position': [],
            'company': [],
            'email': [],
            'phone': [],
            'address': [],
            'website': []
        }
        
        current_field = None
        
        # Process predictions
        for i, (word, pred_id) in enumerate(zip(words, predictions)):
            # Get label
            label = self.ID2LABEL.get(pred_id, 'O')
            
            if label == 'O':
                current_field = None
                continue
            
            # Parse BIO tag
            if '-' in label:
                bio, field_type = label.split('-')
            else:
                continue
            
            # Map to field name
            field_name_map = {
                'NAME': 'full_name',
                'POSITION': 'position',
                'COMPANY': 'company',
                'EMAIL': 'email',
                'PHONE': 'phone',
                'ADDRESS': 'address',
                'WEBSITE': 'website'
            }
            
            field_name = field_name_map.get(field_type)
            if not field_name:
                continue
            
            # Handle BIO tags
            if bio == 'B':  # Beginning of field
                current_field = field_name
                field_map[field_name].append(word)
            elif bio == 'I' and current_field == field_name:  # Inside field
                field_map[field_name].append(word)
        
        # Join words into strings
        result = {
            field: ' '.join(words) if words else None
            for field, words in field_map.items()
        }
        
        # Calculate confidence (simplified: ratio of non-O predictions)
        non_other_count = sum(1 for p in predictions if p != 0)
        confidence = non_other_count / len(predictions) if predictions else 0.0
        
        result['confidence'] = float(confidence)
        
        # Store raw predictions for debugging
        result['predictions'] = [
            {
                'word': word,
                'label': self.ID2LABEL.get(pred_id, 'O'),
                'bbox': ocr_blocks[i]['bbox'] if i < len(ocr_blocks) else None
            }
            for i, (word, pred_id) in enumerate(zip(words, predictions))
        ]
        
        return result
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'full_name': None,
            'position': None,
            'company': None,
            'email': None,
            'phone': None,
            'address': None,
            'website': None,
            'confidence': 0.0,
            'predictions': []
        }


# Global singleton instance
_layoutlm_service = None


def get_layoutlm_service(model_path: Optional[str] = None) -> LayoutLMv3Service:
    """
    Get global LayoutLMv3 service instance (singleton pattern)
    
    Args:
        model_path: Optional custom model path
    
    Returns:
        LayoutLMv3Service instance
    """
    global _layoutlm_service
    
    if _layoutlm_service is None:
        _layoutlm_service = LayoutLMv3Service(model_path)
    
    return _layoutlm_service

