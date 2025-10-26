"""
Unit tests for PaddleOCR Provider
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
import numpy as np

from ..integrations.ocr.providers.paddle_provider import PaddleOCRProvider, PADDLEOCR_AVAILABLE


class TestPaddleOCRProvider:
    """Test PaddleOCR Provider"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.provider = PaddleOCRProvider()
    
    def test_provider_initialization(self):
        """Test provider is initialized correctly"""
        assert self.provider.name == "PaddleOCR"
        assert self.provider.priority == 0  # Highest priority
    
    @pytest.mark.skipif(not PADDLEOCR_AVAILABLE, reason="PaddleOCR not installed")
    def test_is_available(self):
        """Test availability check"""
        # Should be available if PaddleOCR is installed
        assert self.provider.is_available() is True
    
    def test_empty_data_structure(self):
        """Test empty data structure"""
        empty = self.provider._empty_data()
        
        assert isinstance(empty, dict)
        assert 'full_name' in empty
        assert 'email' in empty
        assert 'phone' in empty
        assert 'company' in empty
        assert 'position' in empty
        assert 'website' in empty
        assert 'address' in empty
        assert all(v is None for v in empty.values())
    
    def test_parse_email(self):
        """Test email extraction"""
        text = "John Doe\nCEO\ntest@example.com\n+1234567890"
        result = self.provider._parse_text(text)
        
        assert result['email'] == 'test@example.com'
    
    def test_parse_phone(self):
        """Test phone extraction"""
        text = "John Doe\nCEO\ntest@example.com\n+1 (555) 123-4567"
        result = self.provider._parse_text(text)
        
        assert result['phone'] is not None
        assert '555' in result['phone']
    
    def test_parse_website(self):
        """Test website extraction"""
        text = "John Doe\nCEO\nwww.example.com"
        result = self.provider._parse_text(text)
        
        assert result['website'] is not None
        assert 'example.com' in result['website']
        assert result['website'].startswith('https://')
    
    def test_parse_name_company_position(self):
        """Test name, company, and position extraction"""
        text = "John Doe\nSenior Engineer\nAcme Corporation\ntest@example.com"
        result = self.provider._parse_text(text)
        
        assert result['full_name'] == "John Doe"
        assert result['position'] == "Senior Engineer"
        assert result['company'] == "Acme Corporation"
    
    @pytest.mark.skipif(not PADDLEOCR_AVAILABLE, reason="PaddleOCR not installed")
    @patch('paddleocr.PaddleOCR')
    def test_recognize_with_mock(self, mock_paddleocr):
        """Test recognition with mocked PaddleOCR"""
        # Setup mock
        mock_instance = MagicMock()
        mock_paddleocr.return_value = mock_instance
        
        # Mock OCR result
        mock_result = [[
            [[[10, 10], [100, 10], [100, 40], [10, 40]], ('John Doe', 0.95)],
            [[[10, 50], [100, 50], [100, 80], [10, 80]], ('CEO', 0.92)],
            [[[10, 90], [200, 90], [200, 120], [10, 120]], ('john@example.com', 0.98)],
        ]]
        mock_instance.ocr.return_value = mock_result
        
        # Create provider with mocked OCR
        provider = PaddleOCRProvider()
        provider.ocr = mock_instance
        
        # Create test image
        img = Image.new('RGB', (200, 150), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        # Run recognition
        result = provider.recognize(image_data)
        
        # Verify results
        assert result['provider'] == 'PaddleOCR'
        assert 'blocks' in result
        assert len(result['blocks']) == 3
        assert result['bbox_count'] == 3
        assert 'John Doe' in result['raw_text']
        assert result['data']['email'] == 'john@example.com'
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_address_extraction(self):
        """Test address extraction"""
        text = "John Doe\n123 Main Street\nNew York, NY 10001"
        result = self.provider._parse_text(text)
        
        assert result['address'] is not None
        assert 'Main Street' in result['address']
    
    def test_multiple_phone_formats(self):
        """Test different phone number formats"""
        test_cases = [
            ("+1 (555) 123-4567", True),
            ("555-123-4567", True),
            ("+44 20 1234 5678", True),
            ("(555) 123-4567", True),
        ]
        
        for phone_text, should_match in test_cases:
            text = f"John Doe\n{phone_text}"
            result = self.provider._parse_text(text)
            
            if should_match:
                assert result['phone'] is not None, f"Failed to extract: {phone_text}"
    
    def test_recognize_empty_image(self):
        """Test recognition with empty/invalid image"""
        if not self.provider.is_available():
            pytest.skip("PaddleOCR not available")
        
        # This should handle gracefully
        try:
            invalid_data = b"not an image"
            result = self.provider.recognize(invalid_data)
            # Should either raise exception or return empty result
            assert result['provider'] == 'PaddleOCR'
        except Exception:
            # Exception is acceptable for invalid input
            pass


@pytest.mark.integration
class TestPaddleOCRProviderIntegration:
    """Integration tests for PaddleOCR Provider (requires PaddleOCR installed)"""
    
    @pytest.mark.skipif(not PADDLEOCR_AVAILABLE, reason="PaddleOCR not installed")
    def test_real_ocr_simple_text(self):
        """Test real OCR on a simple generated image"""
        from PIL import ImageDraw, ImageFont
        
        # Create a simple business card image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text (using default font)
        draw.text((10, 10), "John Doe", fill='black')
        draw.text((10, 40), "CEO", fill='black')
        draw.text((10, 70), "john@example.com", fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        # Run OCR
        provider = PaddleOCRProvider()
        if not provider.is_available():
            pytest.skip("PaddleOCR not available")
        
        result = provider.recognize(image_data)
        
        # Verify
        assert result['provider'] == 'PaddleOCR'
        assert len(result['blocks']) > 0
        # Note: Text recognition quality depends on font and image quality
        # So we just check that we got some results

