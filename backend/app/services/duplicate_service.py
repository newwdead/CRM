"""
Duplicate Detection Service
Business logic for duplicate contact management
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models import DuplicateContact, Contact
from ..repositories import DuplicateRepository, ContactRepository


class DuplicateService:
    """
    Service for duplicate contact detection and management.
    
    Handles:
    - Finding duplicate contacts
    - Managing duplicate status
    - Merging contacts
    """
    
    def __init__(self, db: Session):
        """
        Initialize DuplicateService.
        
        Args:
            db: Database session
        """
        self.db = db
        self.duplicate_repo = DuplicateRepository(db)
        self.contact_repo = ContactRepository(db)
    
    def get_duplicates(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DuplicateContact], int]:
        """
        Get list of duplicates with optional filtering.
        
        Args:
            status: Filter by status (pending, reviewed, merged)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (duplicates list, total count)
        """
        if status:
            duplicates = self.duplicate_repo.get_by_status(status)
            total = len(duplicates)
            return duplicates[skip:skip + limit], total
        else:
            duplicates = self.duplicate_repo.get_all()
            total = len(duplicates)
            return duplicates[skip:skip + limit], total
    
    def get_pending_duplicates(self) -> List[DuplicateContact]:
        """
        Get all pending (unreviewed) duplicates.
        
        Returns:
            List of pending duplicates
        """
        return self.duplicate_repo.get_pending_duplicates()
    
    def get_duplicates_for_contact(self, contact_id: int) -> List[DuplicateContact]:
        """
        Get all duplicates for a specific contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            List of duplicates involving this contact
        """
        return self.duplicate_repo.get_duplicates_for_contact(contact_id)
    
    def update_duplicate_status(
        self,
        duplicate_id: int,
        status: str,
        reviewed_by: Optional[int] = None
    ) -> Optional[DuplicateContact]:
        """
        Update duplicate status.
        
        Args:
            duplicate_id: Duplicate record ID
            status: New status (pending, reviewed, merged, ignored)
            reviewed_by: User ID who reviewed
            
        Returns:
            Updated duplicate or None if not found
        """
        duplicate = self.duplicate_repo.get_by_id(duplicate_id)
        if not duplicate:
            return None
        
        update_data = {'status': status}
        if reviewed_by:
            update_data['reviewed_by'] = reviewed_by
        
        updated = self.duplicate_repo.update(duplicate, update_data)
        self.duplicate_repo.commit()
        
        return updated
    
    def mark_as_reviewed(
        self,
        duplicate_id: int,
        user_id: Optional[int] = None
    ) -> Optional[DuplicateContact]:
        """
        Mark duplicate as reviewed.
        
        Args:
            duplicate_id: Duplicate record ID
            user_id: User ID who reviewed
            
        Returns:
            Updated duplicate or None if not found
        """
        return self.update_duplicate_status(duplicate_id, 'reviewed', user_id)
    
    def mark_as_ignored(
        self,
        duplicate_id: int,
        user_id: Optional[int] = None
    ) -> Optional[DuplicateContact]:
        """
        Mark duplicate as ignored (not a real duplicate).
        
        Args:
            duplicate_id: Duplicate record ID
            user_id: User ID who ignored
            
        Returns:
            Updated duplicate or None if not found
        """
        return self.update_duplicate_status(duplicate_id, 'ignored', user_id)
    
    def merge_contacts(
        self,
        primary_id: int,
        duplicate_ids: List[int],
        user_id: Optional[int] = None
    ) -> Optional[Contact]:
        """
        Merge duplicate contacts into primary contact.
        
        Args:
            primary_id: ID of contact to keep
            duplicate_ids: List of contact IDs to merge
            user_id: User performing the merge
            
        Returns:
            Merged primary contact or None on failure
        """
        # Get primary contact
        primary = self.contact_repo.get_by_id(primary_id)
        if not primary:
            return None
        
        # Merge each duplicate
        for dup_id in duplicate_ids:
            if dup_id == primary_id:
                continue
            
            duplicate = self.contact_repo.get_by_id(dup_id)
            if not duplicate:
                continue
            
            # Merge data (keep non-empty fields from duplicate)
            merged_data = {}
            
            # Merge fields
            for field in ['email', 'phone', 'company', 'position', 'address', 
                         'website', 'notes', 'linkedin_url', 'facebook_url']:
                primary_value = getattr(primary, field, None)
                dup_value = getattr(duplicate, field, None)
                
                if not primary_value and dup_value:
                    merged_data[field] = dup_value
            
            # Update primary with merged data
            if merged_data:
                self.contact_repo.update(primary, merged_data)
            
            # Mark duplicate pairs as merged
            dup_pairs = self.duplicate_repo.get_duplicates_for_contact(dup_id)
            for pair in dup_pairs:
                if pair.contact_id_1 == primary_id or pair.contact_id_2 == primary_id:
                    self.duplicate_repo.update(pair, {'status': 'merged'})
            
            # Delete the duplicate contact
            self.contact_repo.delete(duplicate)
        
        self.duplicate_repo.commit()
        
        # Refresh primary to get updated data
        self.db.refresh(primary)
        return primary
    
    def find_duplicates(
        self,
        threshold: float = 0.75,
        limit: Optional[int] = None
    ) -> List[dict]:
        """
        Find potential duplicate contacts.
        
        Args:
            threshold: Similarity threshold (0.0 - 1.0)
            limit: Maximum number of results
            
        Returns:
            List of duplicate pairs with similarity scores
        """
        # This would typically use the duplicate detection algorithm
        # For now, return existing duplicates
        duplicates = self.duplicate_repo.get_pending_duplicates()
        
        result = []
        for dup in duplicates:
            if dup.similarity >= threshold:
                result.append({
                    'id': dup.id,
                    'contact_1_id': dup.contact_id_1,
                    'contact_2_id': dup.contact_id_2,
                    'similarity': dup.similarity,
                    'match_type': dup.match_type,
                    'status': dup.status
                })
        
        if limit:
            result = result[:limit]
        
        return result
    
    def delete_duplicate(self, duplicate_id: int) -> bool:
        """
        Delete a duplicate record.
        
        Args:
            duplicate_id: Duplicate record ID
            
        Returns:
            True if deleted, False if not found
        """
        duplicate = self.duplicate_repo.get_by_id(duplicate_id)
        if not duplicate:
            return False
        
        self.duplicate_repo.delete(duplicate)
        self.duplicate_repo.commit()
        return True
    
    def count_pending_duplicates(self) -> int:
        """
        Count pending duplicates.
        
        Returns:
            Number of pending duplicates
        """
        pending = self.duplicate_repo.get_pending_duplicates()
        return len(pending)
