"""
OCR Repository Layer
Handles all database operations for OCR-related models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ..models.ocr import OCRCorrection


class OCRRepository:
    """Repository for OCR model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_training_data_by_id(self, training_id: int) -> Optional[OCRCorrection]:
        """
        Get OCR training data by ID.
        
        Args:
            training_id: Training data ID
        
        Returns:
            OCRCorrection instance or None
        """
        return self.db.query(OCRCorrection).filter(OCRCorrection.id == training_id).first()
    
    def get_all_training_data(self, skip: int = 0, limit: int = 100) -> List[OCRCorrection]:
        """
        Get all training data with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of OCRCorrection instances
        """
        return self.db.query(OCRCorrection).offset(skip).limit(limit).all()
    
    def get_training_data_by_contact(self, contact_id: int) -> List[OCRCorrection]:
        """
        Get training data for a specific contact.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            List of OCRCorrection instances
        """
        return self.db.query(OCRCorrection).filter(
            OCRCorrection.contact_id == contact_id
        ).all()
    
    def get_validated_training_data(self) -> List[OCRCorrection]:
        """
        Get all validated training data.
        
        Returns:
            List of validated OCRCorrection instances
        """
        return self.db.query(OCRCorrection).filter(
            OCRCorrection.validated == True
        ).all()
    
    def create_training_data(self, training_data: Dict[str, Any]) -> OCRCorrection:
        """
        Create new OCR training data.
        
        Args:
            training_data: Dictionary with training data
        
        Returns:
            Created OCRCorrection instance
        """
        ocr_data = OCRCorrection(**training_data)
        self.db.add(ocr_data)
        self.db.flush()
        return ocr_data
    
    def update_training_data(
        self, 
        training_data: OCRCorrection, 
        update_data: Dict[str, Any]
    ) -> OCRCorrection:
        """
        Update OCR training data.
        
        Args:
            training_data: OCRCorrection instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated OCRCorrection instance
        """
        for key, value in update_data.items():
            if hasattr(training_data, key):
                setattr(training_data, key, value)
        self.db.add(training_data)
        return training_data
    
    def mark_as_validated(self, training_id: int) -> OCRCorrection:
        """
        Mark training data as validated.
        
        Args:
            training_id: Training data ID
        
        Returns:
            Updated OCRCorrection instance
        """
        training_data = self.get_training_data_by_id(training_id)
        if training_data:
            training_data.validated = True
            self.db.add(training_data)
        return training_data
    
    def delete_training_data(self, training_data: OCRCorrection) -> None:
        """
        Delete OCR training data.
        
        Args:
            training_data: OCRCorrection instance to delete
        """
        self.db.delete(training_data)
    
    def delete_training_data_for_contact(self, contact_id: int) -> int:
        """
        Delete all training data for a specific contact.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            Number of deleted records
        """
        count = self.db.query(OCRCorrection).filter(
            OCRCorrection.contact_id == contact_id
        ).delete()
        return count
    
    def count_training_data(self) -> int:
        """
        Count total number of training data records.
        
        Returns:
            Total count
        """
        return self.db.query(OCRCorrection).count()
    
    def count_validated_training_data(self) -> int:
        """
        Count validated training data.
        
        Returns:
            Count of validated training data
        """
        return self.db.query(OCRCorrection).filter(
            OCRCorrection.validated == True
        ).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

