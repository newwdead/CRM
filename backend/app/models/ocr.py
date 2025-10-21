"""
OCR correction model for training and improvement.
"""
from .base import Base, Column, Integer, String, DateTime, ForeignKey, func


class OCRCorrection(Base):
    """
    Store OCR corrections for training and improving recognition accuracy.
    Each record represents a manual correction of OCR text block.
    """
    __tablename__ = "ocr_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Original OCR data
    original_text = Column(String, nullable=False)  # What OCR recognized
    original_box = Column(String, nullable=False)  # JSON: {x, y, width, height}
    original_confidence = Column(Integer, nullable=True)  # Confidence score (0-100)
    
    # Corrected data
    corrected_text = Column(String, nullable=False)  # What user corrected it to
    corrected_field = Column(String, nullable=False)  # Which field: 'first_name', 'company', etc.
    
    # Metadata for training
    image_path = Column(String, nullable=True)  # Path to original image
    ocr_provider = Column(String, nullable=True)  # 'tesseract', 'parsio', 'google'
    language = Column(String, nullable=True)  # 'rus', 'eng', 'rus+eng'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)




