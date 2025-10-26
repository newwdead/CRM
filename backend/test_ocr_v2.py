"""
Test OCR v2.0 PaddleOCR integration
"""
import sys
sys.path.insert(0, '/app')

from app.integrations.ocr.providers_v2 import OCRManagerV2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ocr_manager():
    """Test OCR Manager v2.0 initialization"""
    logger.info("=" * 60)
    logger.info("Testing OCR Manager v2.0")
    logger.info("=" * 60)
    
    try:
        # Initialize manager
        manager = OCRManagerV2()
        
        # Get available providers
        providers = manager.get_available_providers()
        
        logger.info(f"\n✅ OCR Manager initialized successfully")
        logger.info(f"📊 Available providers: {len(providers)}")
        
        for provider in providers:
            logger.info(f"\n  • {provider['name']}")
            logger.info(f"    Priority: {provider['priority']}")
            logger.info(f"    BBox support: {provider['supports_bbox']}")
            logger.info(f"    Layout support: {provider['supports_layout']}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_ocr_manager()
    sys.exit(0 if success else 1)

