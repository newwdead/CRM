"""
LayoutLMv3 Classifier
Classifies OCR text blocks into business card fields using layout understanding
"""
import logging
from typing import Dict, List, Any, Optional
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForTokenClassification
import numpy as np

from .config import LayoutLMConfig, BUSINESS_CARD_LABELS, LABEL_TO_NAME, FIELD_AGGREGATION
from ..ocr.providers_v2.base import TextBlock, BoundingBox

logger = logging.getLogger(__name__)


class LayoutLMv3Classifier:
    """
    LayoutLMv3-based classifier for business card field extraction.
    
    Uses Microsoft's LayoutLMv3 model to classify OCR text blocks into
    structured contact fields, leveraging both textual and spatial information.
    """
    
    def __init__(self, config: Optional[LayoutLMConfig] = None):
        """
        Initialize LayoutLMv3 classifier.
        
        Args:
            config: Configuration for LayoutLMv3 model
        """
        self.config = config or LayoutLMConfig()
        self.model = None
        self.processor = None
        self.device = "cuda" if self.config.use_gpu and torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Loads the LayoutLMv3 model and processor."""
        try:
            model_path = self.config.fine_tuned_path or self.config.model_name
            
            logger.info(f"Loading LayoutLMv3 model from: {model_path}")
            self.processor = AutoProcessor.from_pretrained(
                self.config.model_name,  # Always use base model for processor
                apply_ocr=False  # We already have OCR results
            )
            
            self.model = AutoModelForTokenClassification.from_pretrained(
                model_path,
                num_labels=self.config.num_labels
            )
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"LayoutLMv3 model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load LayoutLMv3 model: {e}")
            # For now, set model to None - will use fallback logic
            self.model = None
            self.processor = None
    
    def is_available(self) -> bool:
        """Check if LayoutLMv3 model is loaded and ready."""
        return self.model is not None and self.processor is not None
    
    def classify_blocks(
        self,
        text_blocks: List[TextBlock],
        image: Image.Image
    ) -> Dict[str, Any]:
        """
        Classifies text blocks into business card fields.
        
        Args:
            text_blocks: List of OCR text blocks with bounding boxes
            image: Original PIL Image of the business card
        
        Returns:
            Dictionary with classified fields and confidence scores
        """
        if not self.is_available():
            logger.warning("LayoutLMv3 model not available, using fallback classification")
            return self._fallback_classification(text_blocks)
        
        try:
            # Prepare input for LayoutLMv3
            words = [block.text for block in text_blocks]
            boxes = [
                [block.bbox.x, block.bbox.y, block.bbox.x2, block.bbox.y2]
                for block in text_blocks
            ]
            
            # Normalize boxes to [0, 1000] range as required by LayoutLMv3
            img_width, img_height = image.size
            normalized_boxes = self._normalize_boxes(boxes, img_width, img_height)
            
            # Prepare encoding
            encoding = self.processor(
                image,
                words,
                boxes=normalized_boxes,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=self.config.max_length
            )
            
            # Move to device
            encoding = {k: v.to(self.device) for k, v in encoding.items()}
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**encoding)
                predictions = outputs.logits.argmax(-1).squeeze().tolist()
                
                # Get confidence scores
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidences = probabilities.max(-1).values.squeeze().tolist()
            
            # Convert predictions to field names
            classified_fields = self._aggregate_predictions(
                words, predictions, confidences, text_blocks
            )
            
            logger.info(f"LayoutLMv3 classification completed for {len(text_blocks)} blocks")
            return classified_fields
            
        except Exception as e:
            logger.error(f"LayoutLMv3 classification failed: {e}", exc_info=True)
            return self._fallback_classification(text_blocks)
    
    def _normalize_boxes(
        self,
        boxes: List[List[int]],
        width: int,
        height: int
    ) -> List[List[int]]:
        """
        Normalizes bounding boxes to [0, 1000] range.
        
        Args:
            boxes: List of [x1, y1, x2, y2] boxes
            width: Image width
            height: Image height
        
        Returns:
            Normalized boxes in [0, 1000] range
        """
        normalized = []
        for box in boxes:
            normalized.append([
                int(1000 * box[0] / width),
                int(1000 * box[1] / height),
                int(1000 * box[2] / width),
                int(1000 * box[3] / height)
            ])
        return normalized
    
    def _aggregate_predictions(
        self,
        words: List[str],
        predictions: List[int],
        confidences: List[float],
        text_blocks: List[TextBlock]
    ) -> Dict[str, Any]:
        """
        Aggregates BIO predictions into final fields.
        
        Args:
            words: List of words/text blocks
            predictions: List of predicted label IDs
            confidences: List of confidence scores
            text_blocks: Original text blocks with bounding boxes
        
        Returns:
            Dictionary with aggregated fields and metadata
        """
        fields = {}
        current_field = None
        current_text = []
        current_confidences = []
        current_bboxes = []
        
        # Ensure predictions and confidences are lists
        if not isinstance(predictions, list):
            predictions = [predictions]
        if not isinstance(confidences, list):
            confidences = [confidences]
        
        for i, (word, pred_id, conf) in enumerate(zip(words, predictions, confidences)):
            label_name = LABEL_TO_NAME.get(pred_id, 'O')
            
            if label_name == 'O':
                # Save current field if exists
                if current_field:
                    field_key = FIELD_AGGREGATION.get(current_field)
                    if field_key:
                        fields[field_key] = {
                            'text': ' '.join(current_text),
                            'confidence': sum(current_confidences) / len(current_confidences),
                            'bboxes': current_bboxes
                        }
                current_field = None
                current_text = []
                current_confidences = []
                current_bboxes = []
                continue
            
            # Extract field type (remove B- or I- prefix)
            field_type = label_name.split('-')[1] if '-' in label_name else label_name
            
            if label_name.startswith('B-'):
                # Beginning of new field
                if current_field:
                    # Save previous field
                    field_key = FIELD_AGGREGATION.get(current_field)
                    if field_key:
                        fields[field_key] = {
                            'text': ' '.join(current_text),
                            'confidence': sum(current_confidences) / len(current_confidences),
                            'bboxes': current_bboxes
                        }
                current_field = field_type
                current_text = [word]
                current_confidences = [conf]
                current_bboxes = [text_blocks[i].bbox.to_dict()] if i < len(text_blocks) else []
            
            elif label_name.startswith('I-') and current_field == field_type:
                # Inside current field
                current_text.append(word)
                current_confidences.append(conf)
                if i < len(text_blocks):
                    current_bboxes.append(text_blocks[i].bbox.to_dict())
        
        # Save last field
        if current_field:
            field_key = FIELD_AGGREGATION.get(current_field)
            if field_key:
                fields[field_key] = {
                    'text': ' '.join(current_text),
                    'confidence': sum(current_confidences) / len(current_confidences),
                    'bboxes': current_bboxes
                }
        
        return {
            'fields': fields,
            'total_blocks': len(words),
            'classified_blocks': sum(1 for p in predictions if LABEL_TO_NAME.get(p, 'O') != 'O')
        }
    
    def _fallback_classification(self, text_blocks: List[TextBlock]) -> Dict[str, Any]:
        """
        Fallback classification using simple heuristics when LayoutLMv3 is not available.
        
        This is a simple rule-based approach for basic field detection.
        """
        logger.info("Using fallback heuristic classification")
        
        import re
        fields = {}
        
        for block in text_blocks:
            text = block.text.strip()
            
            # Email detection
            if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text):
                if 'email' not in fields:
                    fields['email'] = {
                        'text': text,
                        'confidence': 0.9,
                        'bboxes': [block.bbox.to_dict()]
                    }
            
            # Phone detection
            elif re.match(r'^[\d\s\+\-\(\)]+$', text) and len(re.sub(r'\D', '', text)) >= 7:
                if 'phone' not in fields:
                    fields['phone'] = {
                        'text': text,
                        'confidence': 0.85,
                        'bboxes': [block.bbox.to_dict()]
                    }
            
            # Website detection
            elif re.match(r'^(www\.|https?://)', text, re.IGNORECASE):
                if 'website' not in fields:
                    fields['website'] = {
                        'text': text,
                        'confidence': 0.9,
                        'bboxes': [block.bbox.to_dict()]
                    }
            
            # Name heuristic (first block with letters and possibly spaces)
            elif re.match(r'^[A-Za-zА-Яа-яЁё\s]+$', text) and 'full_name' not in fields:
                fields['full_name'] = {
                    'text': text,
                    'confidence': 0.6,
                    'bboxes': [block.bbox.to_dict()]
                }
        
        return {
            'fields': fields,
            'total_blocks': len(text_blocks),
            'classified_blocks': len(fields),
            'fallback': True
        }

