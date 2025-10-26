"""
OCR Providers Package
Export all OCR providers for easy imports
"""
from .base import OCRProvider
from .paddle_provider import PaddleOCRProvider

__all__ = [
    'OCRProvider',
    'PaddleOCRProvider',
]

