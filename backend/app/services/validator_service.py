"""
Validator Service
High-level service for validating and correcting OCR results
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .base import BaseService
from .validators import FieldValidator, ValidationResult

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
    
    def __init__(self, db: Session):
        """
        Initialize validator service
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db)
        self.field_validator = FieldValidator()
    
    def validate_ocr_result(
        self,
        ocr_data: Dict[str, Any],
        auto_correct: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and optionally correct OCR result
        
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
            
            # Validate all fields
            validation_results = self.field_validator.validate_all(data)
            
            # Get summary
            summary = self.field_validator.get_validation_summary(data)
            
            # Apply corrections if requested
            if auto_correct:
                corrected_data = self.field_validator.get_corrected_data(data)
                ocr_data['data'] = corrected_data
                logger.info(
                    f"✅ Validated OCR data: {summary['valid_fields']}/{summary['total_fields']} valid, "
                    f"{summary['corrected_fields']} corrected, "
                    f"confidence: {summary['avg_confidence']:.2f}"
                )
            else:
                logger.info(
                    f"✅ Validated OCR data: {summary['valid_fields']}/{summary['total_fields']} valid, "
                    f"confidence: {summary['avg_confidence']:.2f}"
                )
            
            # Add validation info to OCR result
            ocr_data['validation'] = {
                'summary': summary,
                'results': {
                    field: result.to_dict()
                    for field, result in validation_results.items()
                },
                'auto_corrected': auto_correct,
            }
            
            # Update overall confidence based on validation
            if 'confidence' in ocr_data:
                # Combine OCR confidence with validation confidence
                ocr_confidence = ocr_data['confidence']
                validation_confidence = summary['avg_confidence']
                ocr_data['confidence'] = (ocr_confidence + validation_confidence) / 2
            else:
                ocr_data['confidence'] = summary['avg_confidence']
            
            return ocr_data
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}", exc_info=True)
            # Return original data if validation fails
            return ocr_data
    
    def validate_field(
        self,
        value: str,
        field_name: str
    ) -> ValidationResult:
        """
        Validate a single field
        
        Args:
            value: Field value
            field_name: Field name
        
        Returns:
            ValidationResult
        """
        return self.field_validator.validate(value, field_name)
    
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
        validation_results = self.field_validator.validate_all(data)
        
        suggestions = {}
        for field_name, result in validation_results.items():
            if not result.is_valid or result.corrected_value:
                suggestions[field_name] = {
                    'original': result.original_value,
                    'corrected': result.corrected_value,
                    'confidence': result.confidence,
                    'error': result.error_message,
                    'suggestions': result.suggestions,
                }
        
        return suggestions
    
    def get_data_quality_score(self, data: Dict[str, str]) -> float:
        """
        Calculate overall data quality score (0-1)
        
        Args:
            data: Contact data
        
        Returns:
            Quality score between 0 and 1
        """
        summary = self.field_validator.get_validation_summary(data)
        
        # Weighted score calculation
        validity_score = summary['valid_fields'] / summary['total_fields'] if summary['total_fields'] > 0 else 0
        confidence_score = summary['avg_confidence']
        
        # Penalty for corrections needed
        correction_penalty = summary['corrected_fields'] * 0.05
        
        quality_score = (validity_score * 0.6 + confidence_score * 0.4) - correction_penalty
        quality_score = max(0.0, min(1.0, quality_score))  # Clamp to [0, 1]
        
        return round(quality_score, 2)
