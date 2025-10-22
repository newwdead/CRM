"""
Duplicate Repository Layer
Handles all database operations for Duplicate models.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from ..models.duplicate import Duplicate
from ..models.contact import Contact


class DuplicateRepository:
    """Repository for Duplicate model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_duplicate_by_id(self, duplicate_id: int) -> Optional[Duplicate]:
        """
        Get duplicate by ID.
        
        Args:
            duplicate_id: Duplicate ID
        
        Returns:
            Duplicate instance or None
        """
        return self.db.query(Duplicate).filter(Duplicate.id == duplicate_id).first()
    
    def get_all_duplicates(self, skip: int = 0, limit: int = 100) -> List[Duplicate]:
        """
        Get all duplicates with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of Duplicate instances
        """
        return self.db.query(Duplicate).offset(skip).limit(limit).all()
    
    def get_duplicates_for_contact(self, contact_id: int) -> List[Duplicate]:
        """
        Get all duplicates for a specific contact.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            List of Duplicate instances
        """
        return self.db.query(Duplicate).filter(
            or_(
                Duplicate.contact_id_1 == contact_id,
                Duplicate.contact_id_2 == contact_id
            )
        ).all()
    
    def get_pending_duplicates(self) -> List[Duplicate]:
        """
        Get all pending (unresolved) duplicates.
        
        Returns:
            List of pending Duplicate instances
        """
        return self.db.query(Duplicate).filter(
            Duplicate.resolved == False
        ).all()
    
    def create_duplicate(self, duplicate_data: Dict[str, Any]) -> Duplicate:
        """
        Create a new duplicate record.
        
        Args:
            duplicate_data: Dictionary with duplicate data
        
        Returns:
            Created Duplicate instance
        """
        duplicate = Duplicate(**duplicate_data)
        self.db.add(duplicate)
        self.db.flush()
        return duplicate
    
    def update_duplicate(self, duplicate: Duplicate, update_data: Dict[str, Any]) -> Duplicate:
        """
        Update duplicate record.
        
        Args:
            duplicate: Duplicate instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated Duplicate instance
        """
        for key, value in update_data.items():
            if hasattr(duplicate, key):
                setattr(duplicate, key, value)
        self.db.add(duplicate)
        return duplicate
    
    def mark_as_resolved(self, duplicate_id: int) -> Duplicate:
        """
        Mark duplicate as resolved.
        
        Args:
            duplicate_id: Duplicate ID
        
        Returns:
            Updated Duplicate instance
        """
        duplicate = self.get_duplicate_by_id(duplicate_id)
        if duplicate:
            duplicate.resolved = True
            self.db.add(duplicate)
        return duplicate
    
    def delete_duplicate(self, duplicate: Duplicate) -> None:
        """
        Delete duplicate record.
        
        Args:
            duplicate: Duplicate instance to delete
        """
        self.db.delete(duplicate)
    
    def delete_duplicates_for_contact(self, contact_id: int) -> int:
        """
        Delete all duplicates for a specific contact.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            Number of deleted records
        """
        count = self.db.query(Duplicate).filter(
            or_(
                Duplicate.contact_id_1 == contact_id,
                Duplicate.contact_id_2 == contact_id
            )
        ).delete()
        return count
    
    def count_duplicates(self) -> int:
        """
        Count total number of duplicates.
        
        Returns:
            Total count
        """
        return self.db.query(Duplicate).count()
    
    def count_pending_duplicates(self) -> int:
        """
        Count pending duplicates.
        
        Returns:
            Count of pending duplicates
        """
        return self.db.query(Duplicate).filter(Duplicate.resolved == False).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

