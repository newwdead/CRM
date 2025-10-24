"""
OCR Service

Handles all business logic related to OCR processing:
- Image processing and OCR extraction
- Multi-card detection
- OCR corrections and training
- Provider management
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
import logging
from PIL import Image
import io

from .base import BaseService
from ..models import Contact, OCRCorrection
from ..integrations.ocr.providers import OCRManager
from ..integrations.ocr import utils as ocr_utils
from ..integrations.ocr import image_processing
from ..core import qr as qr_utils


class OCRService(BaseService):
    """
    Service for managing OCR operations.
    
    Provides methods for:
    - Processing business card images
    - Extracting text from images
    - Managing OCR corrections
    - Handling multi-card detection
    """
    
    def __init__(self, db: Session, ocr_manager: OCRManager):
        """
        Initialize OCR service with database session and OCR manager.
        
        Args:
            db: SQLAlchemy database session
            ocr_manager: OCR Manager instance
        """
        super().__init__(db)
        self.ocr_manager = ocr_manager
    
    def process_image(
        self,
        image_data: bytes,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a business card image with OCR.
        
        Args:
            image_data: Image bytes
            provider: Optional OCR provider override
        
        Returns:
            Dict with extracted contact data
        """
        # First try QR code scanning
        qr_data = self.scan_qr_code(image_data)
        if qr_data:
            self.logger.info("QR code found, using QR data")
            return qr_data
        
        # Fallback to OCR
        self.logger.info("No QR code found, using OCR")
        return self.extract_text(image_data, provider)
    
    def extract_text(
        self,
        image_data: bytes,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from image using OCR.
        
        Args:
            image_data: Image bytes
            provider: Optional OCR provider (tesseract, google_vision, paddleocr)
        
        Returns:
            Dict with extracted contact data
        """
        # Perform OCR
        ocr_result = self.ocr_manager.perform_ocr(image_data, provider=provider)
        
        if not ocr_result or 'text' not in ocr_result:
            return {
                'error': 'OCR failed',
                'provider': provider or self.ocr_manager.current_provider
            }
        
        extracted_text = ocr_result['text']
        
        # Parse OCR text to extract contact fields
        parsed_data = ocr_utils.parse_business_card(extracted_text)
        
        # Add OCR metadata
        parsed_data['ocr_provider'] = ocr_result.get('provider', provider or self.ocr_manager.current_provider)
        parsed_data['ocr_confidence'] = ocr_result.get('confidence')
        parsed_data['raw_text'] = extracted_text
        
        return parsed_data
    
    def scan_qr_code(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Scan QR code from image.
        
        Args:
            image_data: Image bytes
        
        Returns:
            Dict with QR code data or None if no QR code found
        """
        try:
            qr_data = qr_utils.scan_qr_code(image_data)
            if qr_data:
                self.logger.info("QR code detected and decoded")
                return qr_data
        except Exception as e:
            self.logger.error(f"QR code scanning error: {e}")
        
        return None
    
    def detect_multiple_cards(self, image_data: bytes) -> List[bytes]:
        """
        Detect and split multiple business cards in a single image.
        
        Args:
            image_data: Image bytes
        
        Returns:
            List of image bytes for each detected card
        """
        try:
            cards = image_processing.detect_and_split_cards(image_data)
            self.logger.info(f"Detected {len(cards)} cards in image")
            return cards
        except Exception as e:
            self.logger.error(f"Multi-card detection error: {e}")
            return [image_data]  # Return original image if detection fails
    
    def get_ocr_blocks(
        self,
        contact_id: int,
        image_data: bytes
    ) -> Dict[str, Any]:
        """
        Get OCR bounding boxes and text blocks for annotation.
        
        Args:
            contact_id: Contact ID
            image_data: Image bytes
        
        Returns:
            Dict with OCR blocks and bounding boxes
        """
        # Check if contact exists
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return {'error': 'Contact not found'}
        
        # Get OCR blocks using tesseract_boxes
        try:
            from ..tesseract_boxes import extract_boxes_from_image
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Extract bounding boxes
            boxes = extract_boxes_from_image(image)
            
            return {
                'contact_id': contact_id,
                'boxes': boxes,
                'total_blocks': len(boxes)
            }
        except Exception as e:
            self.logger.error(f"Error extracting OCR blocks: {e}")
            return {'error': str(e)}
    
    def save_ocr_correction(
        self,
        correction_data: Dict[str, Any]
    ) -> OCRCorrection:
        """
        Save OCR correction for training purposes.
        
        Args:
            correction_data: Dict with original_text, corrected_text, corrected_field,
                           confidence, provider, language
        
        Returns:
            OCRCorrection instance
        """
        correction = OCRCorrection(
            original_text=correction_data.get('original_text'),
            corrected_text=correction_data.get('corrected_text'),
            corrected_field=correction_data.get('corrected_field'),
            confidence_score=correction_data.get('confidence'),
            ocr_provider=correction_data.get('provider', 'tesseract'),
            language=correction_data.get('language', 'eng'),
        )
        
        self.add(correction)
        self.commit()
        self.refresh(correction)
        
        self.logger.info(
            f"OCR correction saved: {correction_data.get('original_text')} → "
            f"{correction_data.get('corrected_text')} (field: {correction_data.get('corrected_field')})"
        )
        
        return correction
    
    def get_ocr_corrections(
        self,
        limit: int = 100
    ) -> List[OCRCorrection]:
        """
        Get OCR corrections for training.
        
        Args:
            limit: Maximum number of corrections to return
        
        Returns:
            List of OCRCorrection instances
        """
        return self.db.query(OCRCorrection).order_by(
            OCRCorrection.created_at.desc()
        ).limit(limit).all()
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of available OCR providers.
        
        Returns:
            List of dicts with provider info
        """
        return self.ocr_manager.get_available_providers()
    
    def get_current_provider(self) -> str:
        """
        Get currently active OCR provider.
        
        Returns:
            Provider name
        """
        return self.ocr_manager.current_provider
    
    def set_provider(self, provider: str) -> bool:
        """
        Set OCR provider.
        
        Args:
            provider: Provider name (tesseract, google_vision, paddleocr)
        
        Returns:
            True if successful
        """
        try:
            self.ocr_manager.set_provider(provider)
            return True
        except Exception as e:
            self.logger.error(f"Error setting OCR provider: {e}")
            return False
    
    def preprocess_image(
        self,
        image_data: bytes,
        operations: Optional[List[str]] = None
    ) -> bytes:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_data: Image bytes
            operations: List of operations to apply (e.g., ['denoise', 'sharpen', 'contrast'])
        
        Returns:
            Processed image bytes
        """
        try:
            # Default preprocessing
            if operations is None:
                operations = ['denoise', 'sharpen', 'contrast']
            
            image = Image.open(io.BytesIO(image_data))
            
            # Apply preprocessing from image_processing module
            processed_image = image_processing.preprocess_image(image, operations)
            
            # Convert back to bytes
            output = io.BytesIO()
            processed_image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            return image_data  # Return original if preprocessing fails

