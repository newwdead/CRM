"""
DuplicateContact Repository Layer
Handles all database operations for DuplicateContact models.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from ..models.duplicate import DuplicateContactContact
from ..models.contact import Contact


class DuplicateContactRepository:
    """Repository for DuplicateContactContact model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_duplicate_by_id(self, duplicate_id: int) -> Optional[DuplicateContactContact]:
        """
        Get duplicate by ID.
        
        Args:
            duplicate_id: DuplicateContact ID
        
        Returns:
            DuplicateContactContact instance or None
        """
        return self.db.query(DuplicateContactContact).filter(DuplicateContactContact.id == duplicate_id).first()
    
    def get_all_duplicates(self, skip: int = 0, limit: int = 100) -> List[DuplicateContactContact]:
        """
        Get all duplicates with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of DuplicateContactContact instances
        """
        return self.db.query(DuplicateContactContact).offset(skip).limit(limit).all()
    
    def get_duplicates_for_contact(self, contact_id: int) -> List[DuplicateContact]:
        """
        Get all duplicates for a specific contact.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            List of DuplicateContact instances
        """
        return self.db.query(DuplicateContact).filter(
            or_(
                DuplicateContact.contact_id_1 == contact_id,
                DuplicateContact.contact_id_2 == contact_id
            )
        ).all()
    
    def get_pending_duplicates(self) -> List[DuplicateContact]:
        """
        Get all pending (unresolved) duplicates.
        
        Returns:
            List of pending DuplicateContact instances
        """
        return self.db.query(DuplicateContact).filter(
            DuplicateContact.resolved == False
        ).all()
    
    def create_duplicate(self, duplicate_data: Dict[str, Any]) -> DuplicateContact:
        """
        Create a new duplicate record.
        
        Args:
            duplicate_data: Dictionary with duplicate data
        
        Returns:
            Created DuplicateContact instance
        """
        duplicate = DuplicateContact(**duplicate_data)
        self.db.add(duplicate)
        self.db.flush()
        return duplicate
    
    def update_duplicate(self, duplicate: DuplicateContact, update_data: Dict[str, Any]) -> DuplicateContact:
        """
        Update duplicate record.
        
        Args:
            duplicate: DuplicateContact instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated DuplicateContact instance
        """
        for key, value in update_data.items():
            if hasattr(duplicate, key):
                setattr(duplicate, key, value)
        self.db.add(duplicate)
        return duplicate
    
    def mark_as_resolved(self, duplicate_id: int) -> DuplicateContact:
        """
        Mark duplicate as resolved.
        
        Args:
            duplicate_id: DuplicateContact ID
        
        Returns:
            Updated DuplicateContact instance
        """
        duplicate = self.get_duplicate_by_id(duplicate_id)
        if duplicate:
            duplicate.resolved = True
            self.db.add(duplicate)
        return duplicate
    
    def delete_duplicate(self, duplicate: DuplicateContact) -> None:
        """
        Delete duplicate record.
        
        Args:
            duplicate: DuplicateContact instance to delete
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
        count = self.db.query(DuplicateContact).filter(
            or_(
                DuplicateContact.contact_id_1 == contact_id,
                DuplicateContact.contact_id_2 == contact_id
            )
        ).delete()
        return count
    
    def count_duplicates(self) -> int:
        """
        Count total number of duplicates.
        
        Returns:
            Total count
        """
        return self.db.query(DuplicateContact).count()
    
    def count_pending_duplicates(self) -> int:
        """
        Count pending duplicates.
        
        Returns:
            Count of pending duplicates
        """
        return self.db.query(DuplicateContact).filter(DuplicateContact.resolved == False).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

