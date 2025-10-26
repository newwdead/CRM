"""
OCR Service v2.0
Enhanced with PaddleOCR and LayoutLMv3 support
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from PIL import Image
import io

from .base import BaseService
from ..models import Contact, OCRCorrection
from ..integrations.ocr.providers_v2 import OCRManagerV2, TextBlock, BoundingBox
from ..integrations.ocr import utils as ocr_utils
from ..integrations.ocr import image_processing
from ..core import qr as qr_utils


logger = logging.getLogger(__name__)


class OCRServiceV2(BaseService):
    """
    OCR Service v2.0
    
    Features:
    - PaddleOCR with bounding boxes
    - LayoutLMv3 integration (Phase 2)
    - MinIO storage (Phase 3)
    - Advanced validation (Phase 4)
    """
    
    def __init__(self, db: Session, ocr_manager: OCRManagerV2):
        """
        Initialize OCR service v2.0
        
        Args:
            db: SQLAlchemy database session
            ocr_manager: OCR Manager v2.0 instance
        """
        super().__init__(db)
        self.ocr_manager = ocr_manager
    
    def process_image(
        self,
        image_data: bytes,
        provider: Optional[str] = None,
        use_layout: bool = True,  # Use LayoutLMv3 when available
    ) -> Dict[str, Any]:
        """
        Process business card image with OCR v2.0
        
        Args:
            image_data: Image bytes
            provider: Specific OCR provider (optional)
            use_layout: Use LayoutLMv3 classification
        
        Returns:
            {
                'text': str,
                'blocks': List[Dict],  # NEW: Text blocks with positions
                'qr_data': Optional[Dict],
                'data': Dict,  # Extracted fields
                'confidence': float,
                'provider': str,
            }
        """
        try:
            # Check for QR code first
            qr_result = self._scan_qr_code(image_data)
            
            # Run OCR with new manager
            ocr_result = self.ocr_manager.recognize(
                image_data=image_data,
                provider_name=provider,
                use_layout=use_layout
            )
            
            # Convert TextBlock objects to dicts for API response
            blocks_data = []
            if ocr_result.get('blocks'):
                for block in ocr_result['blocks']:
                    if isinstance(block, TextBlock):
                        blocks_data.append({
                            'text': block.text,
                            'bbox': block.bbox.to_dict(),
                            'confidence': block.confidence,
                            'block_id': block.block_id,
                            'field_type': block.field_type,
                        })
                    else:
                        # Fallback for dict format
                        blocks_data.append(block)
            
            # Merge QR data with OCR data if available
            final_data = ocr_result.get('data', {})
            if qr_result and qr_result.get('data'):
                # QR data takes precedence
                for key, value in qr_result['data'].items():
                    if value:
                        final_data[key] = value
            
            result = {
                'text': ocr_result.get('raw_text', ''),
                'blocks': blocks_data,  # NEW in v2.0
                'qr_data': qr_result,
                'data': final_data,
                'confidence': ocr_result.get('confidence', 0.0),
                'provider': ocr_result.get('provider', 'unknown'),
                'image_size': ocr_result.get('image_size'),  # NEW in v2.0
                'block_count': ocr_result.get('block_count', 0),  # NEW in v2.0
            }
            
            logger.info(
                f"✅ OCR v2.0 processed image: {result['block_count']} blocks, "
                f"confidence: {result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ OCR v2.0 processing failed: {e}", exc_info=True)
            raise
    
    def _scan_qr_code(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """Scan image for QR code"""
        try:
            qr_data = qr_utils.scan_qr_code(image_data)
            if qr_data:
                logger.info(f"📱 QR code detected: {qr_data.get('type', 'unknown')}")
                return qr_data
        except Exception as e:
            logger.warning(f"⚠️ QR code scan failed: {e}")
        
        return None
    
    def save_ocr_correction(
        self,
        contact_id: int,
        original_text: str,
        corrected_data: Dict[str, str],
        blocks: Optional[List[Dict]] = None,
    ) -> OCRCorrection:
        """
        Save OCR correction for training
        
        Args:
            contact_id: Contact ID
            original_text: Original OCR text
            corrected_data: User-corrected fields
            blocks: Text blocks with positions (NEW in v2.0)
        
        Returns:
            OCRCorrection object
        """
        try:
            correction = OCRCorrection(
                contact_id=contact_id,
                original_text=original_text,
                corrected_data=corrected_data,
                metadata={
                    'blocks': blocks,  # Save blocks for LayoutLMv3 training
                    'version': 'v2.0'
                }
            )
            
            self.db.add(correction)
            self.db.commit()
            self.db.refresh(correction)
            
            logger.info(f"💾 Saved OCR correction for contact {contact_id}")
            
            return correction
            
        except Exception as e:
            logger.error(f"❌ Failed to save OCR correction: {e}")
            self.db.rollback()
            raise
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available OCR providers"""
        return self.ocr_manager.get_available_providers()

