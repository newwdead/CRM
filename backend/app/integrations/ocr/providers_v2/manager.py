"""
OCR Manager v2.0
Orchestrates multiple OCR providers with fallback
"""
import logging
from typing import Dict, Any, List, Optional
from .base import OCRProviderV2, TextBlock
from .paddle_provider import PaddleOCRProvider

logger = logging.getLogger(__name__)


class OCRManagerV2:
    """
    OCR Manager v2.0
    
    Features:
    - Multiple provider support with priority
    - Automatic fallback
    - Bbox and layout support
    - LayoutLMv3 integration ready
    """
    
    def __init__(self):
        self.providers: List[OCRProviderV2] = []
        self.layoutlm_classifier = None  # Will be initialized in Phase 2
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available OCR providers"""
        # Create all providers
        all_providers = [
            PaddleOCRProvider(),
            # Add more providers here:
            # TesseractProviderV2(),
            # GoogleVisionProviderV2(),
        ]
        
        # Filter only available providers
        for provider in all_providers:
            if provider.is_available():
                self.providers.append(provider)
                logger.info(
                    f"✅ OCR Provider initialized: {provider.name} "
                    f"(priority: {provider.priority}, bbox: {provider.supports_bbox})"
                )
            else:
                logger.warning(f"⚠️ OCR Provider not available: {provider.name}")
        
        # Sort by priority (lower number = higher priority)
        self.providers.sort(key=lambda p: p.priority)
        
        if not self.providers:
            logger.error("❌ No OCR providers available!")
        else:
            logger.info(f"🚀 OCR Manager v2.0 initialized with {len(self.providers)} provider(s)")
    
    def recognize(
        self,
        image_data: bytes,
        provider_name: Optional[str] = None,
        use_layout: bool = False,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize text from image
        
        Args:
            image_data: Image bytes
            provider_name: Specific provider to use (optional)
            use_layout: Use LayoutLMv3 classification (Phase 2)
            filename: Optional filename for context
        
        Returns:
            OCR result with blocks and structured data
        """
        if not self.providers:
            raise RuntimeError("No OCR providers available")
        
        # Select providers to try
        if provider_name:
            # Use specific provider
            providers_to_try = [p for p in self.providers if p.name == provider_name]
            if not providers_to_try:
                raise ValueError(f"Provider '{provider_name}' not found")
        else:
            # Try all providers in priority order
            providers_to_try = self.providers
        
        last_error = None
        
        for provider in providers_to_try:
            try:
                logger.info(f"🔍 Attempting OCR with {provider.name}...")
                
                # Standard recognition
                result = provider.recognize(image_data, filename)
                
                # Add layout classification if requested (Phase 2)
                if use_layout and self.layoutlm_classifier and provider.supports_bbox:
                    logger.info(f"📊 Applying LayoutLMv3 classification...")
                    result = self._apply_layout_classification(result)
                
                logger.info(
                    f"✅ OCR successful with {provider.name}, "
                    f"confidence: {result.get('confidence', 0):.2f}"
                )
                
                return result
                
            except Exception as e:
                logger.error(f"❌ {provider.name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        error_msg = f"All OCR providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _apply_layout_classification(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply LayoutLMv3 classification to OCR blocks
        
        This will be fully implemented in Phase 2
        
        Args:
            ocr_result: Result from OCR provider with blocks
        
        Returns:
            Enhanced result with field classifications
        """
        if not self.layoutlm_classifier:
            logger.warning("LayoutLMv3 not initialized (Phase 2)")
            return ocr_result
        
        # TODO: Implement LayoutLMv3 classification
        # 1. Prepare input for LayoutLMv3 (text + bbox + image)
        # 2. Run classification
        # 3. Map blocks to fields (name, company, email, etc.)
        # 4. Update ocr_result['data'] with classifications
        
        return ocr_result
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with metadata"""
        return [provider.get_metadata() for provider in self.providers]
    
    def initialize_layoutlm(self, model_path: Optional[str] = None):
        """
        Initialize LayoutLMv3 classifier
        
        This will be implemented in Phase 2
        
        Args:
            model_path: Path to fine-tuned model (optional)
        """
        logger.info("📊 LayoutLMv3 initialization will be added in Phase 2")
        # TODO: Load LayoutLMv3 model
        # self.layoutlm_classifier = LayoutLMv3Classifier(model_path)
        pass

