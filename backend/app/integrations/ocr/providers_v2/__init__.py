"""
OCR Providers v2.0 Package
Enhanced OCR providers with bbox support and layout understanding
"""
from .base import OCRProviderV2, TextBlock, BoundingBox
from .paddle_provider import PaddleOCRProvider
from .manager import OCRManagerV2

__all__ = [
    'OCRProviderV2',
    'TextBlock',
    'BoundingBox',
    'PaddleOCRProvider',
    'OCRManagerV2',
]

