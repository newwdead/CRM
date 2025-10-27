"""
OCR Manager v2.0
Orchestrates multiple OCR providers with fallback
"""
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from .base import OCRProviderV2, TextBlock
from .paddle_provider import PaddleOCRProvider
from ...layoutlm.classifier import LayoutLMv3Classifier
from ...layoutlm.config import LayoutLMConfig

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
    
    def __init__(self, enable_layoutlm: bool = True):
        """
        Initialize OCR Manager v2.0
        
        Args:
            enable_layoutlm: Enable LayoutLMv3 for field classification (Phase 2)
        """
        self.providers: List[OCRProviderV2] = []
        self.layoutlm_classifier = None
        self._initialize_providers()
        
        # Initialize LayoutLMv3 if enabled (Phase 2)
        if enable_layoutlm:
            self.initialize_layoutlm()
    
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
            # Use specific provider (case-insensitive)
            providers_to_try = [p for p in self.providers if p.name.lower() == provider_name.lower()]
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
        
        Args:
            ocr_result: Result from OCR provider with blocks
        
        Returns:
            Enhanced result with field classifications
        """
        if not self.layoutlm_classifier or not self.layoutlm_classifier.is_available():
            logger.warning("⚠️ LayoutLMv3 not available, using fallback")
            return ocr_result
        
        try:
            # Extract blocks and image from OCR result
            blocks = ocr_result.get('blocks', [])
            image_data = ocr_result.get('image_data')
            
            if not blocks or not image_data:
                logger.warning("⚠️ Missing blocks or image data for LayoutLMv3")
                return ocr_result
            
            # Convert image bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert dict blocks to TextBlock objects if needed
            text_blocks = []
            for block in blocks:
                if isinstance(block, TextBlock):
                    text_blocks.append(block)
                elif isinstance(block, dict):
                    # Convert dict to TextBlock
                    from .base import BoundingBox
                    bbox_data = block.get('bbox', {})
                    # Handle both formats: x/y/width/height and x1/y1/x2/y2
                    if 'width' in bbox_data:
                        bbox = BoundingBox(
                            x=bbox_data.get('x', 0),
                            y=bbox_data.get('y', 0),
                            width=bbox_data.get('width', 0),
                            height=bbox_data.get('height', 0)
                        )
                    else:
                        # Convert x1/y1/x2/y2 to x/y/width/height
                        x = bbox_data.get('x', bbox_data.get('x1', 0))
                        y = bbox_data.get('y', bbox_data.get('y1', 0))
                        x2 = bbox_data.get('x2', x)
                        y2 = bbox_data.get('y2', y)
                        bbox = BoundingBox(
                            x=x,
                            y=y,
                            width=x2 - x,
                            height=y2 - y
                        )
                    text_block = TextBlock(
                        text=block.get('text', ''),
                        bbox=bbox,
                        confidence=block.get('confidence', 0.0),
                        block_id=block.get('block_id'),
                        field_type=block.get('field_type')
                    )
                    text_blocks.append(text_block)
            
            # Run LayoutLMv3 classification
            logger.info(f"📊 Running LayoutLMv3 classification on {len(text_blocks)} blocks...")
            classified_result = self.layoutlm_classifier.classify_blocks(text_blocks, image)
            
            # Merge classified fields into OCR result
            if classified_result and classified_result.get('fields'):
                logger.info(f"✅ LayoutLMv3 classified {classified_result.get('classified_blocks', 0)} blocks")
                
                # Update blocks with field types
                fields_map = classified_result['fields']
                for field_name, field_data in fields_map.items():
                    field_text = field_data.get('text', '')
                    if field_text:
                        ocr_result['data'][field_name] = field_text
                
                # Add metadata
                ocr_result['layoutlm_used'] = True
                ocr_result['layoutlm_confidence'] = sum(
                    f.get('confidence', 0) for f in fields_map.values()
                ) / len(fields_map) if fields_map else 0.0
            else:
                logger.warning("⚠️ LayoutLMv3 returned no classified fields")
            
            return ocr_result
            
        except Exception as e:
            logger.error(f"❌ LayoutLMv3 classification failed: {e}", exc_info=True)
            return ocr_result
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [provider.name for provider in self.providers]
    
    def get_provider_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about all providers"""
        return [
            {
                "name": provider.name,
                "priority": provider.priority,
                "available": provider.is_available(),
                "supports_bbox": provider.supports_bbox,
                "supports_layout": provider.supports_layout,
            }
            for provider in sorted(self.providers, key=lambda x: x.priority)
        ]
    
    def initialize_layoutlm(self, model_path: Optional[str] = None):
        """
        Initialize LayoutLMv3 classifier (Phase 2 - COMPLETED)
        
        Args:
            model_path: Path to fine-tuned model (optional)
        """
        try:
            logger.info("📊 Initializing LayoutLMv3 classifier...")
            
            # Create config
            config = LayoutLMConfig()
            if model_path:
                config.fine_tuned_path = model_path
            
            # Initialize classifier
            self.layoutlm_classifier = LayoutLMv3Classifier(config)
            
            if self.layoutlm_classifier.is_available():
                logger.info("✅ LayoutLMv3 classifier initialized successfully")
            else:
                logger.warning("⚠️ LayoutLMv3 model not available, will use fallback heuristics")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LayoutLMv3: {e}", exc_info=True)
            self.layoutlm_classifier = None

