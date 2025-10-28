"""
Validator Service
High-level service for validating and correcting OCR results
Now uses the new validator system: Regex + spaCy + GPT
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .base import BaseService
from ..integrations.validator import ValidatorService as NewValidatorService

logger = logging.getLogger(__name__)


class ValidatorService(BaseService):
    """
    Validator service for OCR data quality assurance
    
    Features:
    - Validate OCR-extracted fields
    - Auto-correct common OCR errors
    - Confidence scoring
    - Validation reports
    """
    
    def __init__(self, db: Session, use_gpt: bool = False):
        """
        Initialize validator service
        
        Args:
            db: SQLAlchemy database session
            use_gpt: Enable GPT validator (requires OPENAI_API_KEY)
        """
        super().__init__(db)
        self.validator = NewValidatorService(use_gpt=use_gpt)
    
    def validate_ocr_result(
        self,
        ocr_data: Dict[str, Any],
        auto_correct: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and optionally correct OCR result using new validator system
        
        Args:
            ocr_data: OCR result dictionary with 'data' field
            auto_correct: Apply automatic corrections
        
        Returns:
            Enhanced OCR result with validation info
        """
        try:
            # Extract data fields
            data = ocr_data.get('data', {})
            
            if not data:
                logger.warning("⚠️ No data to validate in OCR result")
                return ocr_data
            
            # Validate using new validator service
            validation_result = self.validator.validate_all(data)
            
            # Apply corrections if requested
            if auto_correct:
                ocr_data['data'] = validation_result['validated']
                logger.info(
                    f"✅ Validated OCR data: {len(validation_result['corrections'])} corrections, "
                    f"confidence: {validation_result['overall_confidence']:.2f}"
                )
            
            # Add validation info to OCR result
            ocr_data['validation'] = {
                'corrections': validation_result['corrections'],
                'overall_confidence': validation_result['overall_confidence'],
                'auto_corrected': auto_correct,
            }
            
            # Update overall confidence based on validation
            if 'confidence' in ocr_data:
                # Combine OCR confidence with validation confidence
                ocr_confidence = ocr_data['confidence']
                validation_confidence = validation_result['overall_confidence']
                ocr_data['confidence'] = (ocr_confidence + validation_confidence) / 2
            else:
                ocr_data['confidence'] = validation_result['overall_confidence']
            
            return ocr_data
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}", exc_info=True)
            # Return original data if validation fails
            return ocr_data
    
    def validate_field(
        self,
        value: str,
        field_name: str
    ) -> Dict[str, Any]:
        """
        Validate a single field
        
        Args:
            value: Field value
            field_name: Field name
        
        Returns:
            Validation result dict
        """
        return self.validator.validate_field({}, field_name, value)
    
    def suggest_corrections(
        self,
        data: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get correction suggestions without applying them
        
        Args:
            data: Contact data
        
        Returns:
            Dictionary of field_name -> suggestions
        """
        validation_result = self.validator.validate_all(data)
        return validation_result.get('corrections', {})
    
    def get_data_quality_score(self, data: Dict[str, str]) -> float:
        """
        Calculate overall data quality score (0-1)
        
        Args:
            data: Contact data
        
        Returns:
            Quality score between 0 and 1
        """
        validation_result = self.validator.validate_all(data)
        return round(validation_result.get('overall_confidence', 0.5), 2)
