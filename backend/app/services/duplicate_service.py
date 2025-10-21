"""
Duplicate Detection Service

Handles all business logic related to duplicate contact detection:
- Finding duplicates
- Updating duplicate statuses  
- Merging contacts
- Managing duplicate records
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional, Tuple
import logging

from .base import BaseService
from ..models import Contact, User, DuplicateContact
from .. import duplicate_utils
from ..core.utils import create_audit_log


class DuplicateService(BaseService):
    """
    Service for managing duplicate contact detection and resolution.
    
    Provides methods for:
    - Detecting duplicates automatically and manually
    - Updating duplicate statuses
    - Merging duplicate contacts
    - Retrieving duplicate records
    """
    
    def get_duplicates(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get list of detected duplicate contacts.
        
        Args:
            status: Filter by status (pending, reviewed, merged, ignored)
            limit: Maximum number of results
        
        Returns:
            Dict with duplicates list and total count
        """
        query = self.db.query(DuplicateContact)
        
        if status:
            query = query.filter(DuplicateContact.status == status)
        
        duplicates = query.order_by(
            DuplicateContact.similarity_score.desc(),
            DuplicateContact.detected_at.desc()
        ).limit(limit).all()
        
        result = []
        for dup in duplicates:
            result.append({
                'id': dup.id,
                'contact_id_1': dup.contact_id_1,
                'contact_id_2': dup.contact_id_2,
                'contact_1': self._format_contact(dup.contact_1),
                'contact_2': self._format_contact(dup.contact_2),
                'similarity_score': dup.similarity_score,
                'match_fields': dup.match_fields if dup.match_fields else {},
                'status': dup.status,
                'auto_detected': dup.auto_detected,
                'detected_at': dup.detected_at.isoformat() if dup.detected_at else None,
            })
        
        return {
            'duplicates': result,
            'total': len(result)
        }
    
    def find_duplicates_manual(
        self,
        threshold: float = 0.75,
        contact_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Manually trigger duplicate detection.
        
        Args:
            threshold: Similarity threshold (0-1)
            contact_ids: Optional list of contact IDs to check. If None, check all contacts
        
        Returns:
            Dict with detection results
        """
        # Get contacts to check
        if contact_ids:
            contacts = self.db.query(Contact).filter(Contact.id.in_(contact_ids)).all()
        else:
            contacts = self.db.query(Contact).all()
        
        if len(contacts) < 2:
            return {
                'message': 'Need at least 2 contacts to find duplicates',
                'found': 0,
                'saved': 0,
                'threshold': threshold
            }
        
        # Convert to dicts for comparison
        contact_dicts = [self._contact_to_dict(c) for c in contacts]
        
        # Find duplicates
        duplicates = duplicate_utils.find_duplicate_contacts(contact_dicts, threshold)
        
        # Save to database
        saved_count = 0
        for contact1, contact2, score, field_scores in duplicates:
            id1 = min(contact1['id'], contact2['id'])
            id2 = max(contact1['id'], contact2['id'])
            
            # Check if already exists
            existing = self.db.query(DuplicateContact).filter(
                DuplicateContact.contact_id_1 == id1,
                DuplicateContact.contact_id_2 == id2
            ).first()
            
            if not existing:
                dup = DuplicateContact(
                    contact_id_1=id1,
                    contact_id_2=id2,
                    similarity_score=score,
                    match_fields=field_scores,
                    status='pending',
                    auto_detected=False
                )
                self.add(dup)
                saved_count += 1
        
        self.commit()
        
        return {
            'message': f'Found {len(duplicates)} potential duplicates',
            'found': len(duplicates),
            'saved': saved_count,
            'threshold': threshold
        }
    
    def update_duplicate_status(
        self,
        duplicate_id: int,
        status: str,
        current_user: User
    ) -> Optional[Dict[str, Any]]:
        """
        Update duplicate status.
        
        Args:
            duplicate_id: Duplicate record ID
            status: New status (pending, reviewed, ignored)
            current_user: User performing the update
        
        Returns:
            Dict with result or None if not found
        """
        if status not in ['pending', 'reviewed', 'ignored']:
            raise ValueError(f'Invalid status: {status}')
        
        dup = self.db.query(DuplicateContact).filter(
            DuplicateContact.id == duplicate_id
        ).first()
        
        if not dup:
            return None
        
        dup.status = status
        dup.reviewed_at = func.now()
        dup.reviewed_by = current_user.id
        
        self.commit()
        
        return {
            'message': 'Status updated',
            'duplicate_id': duplicate_id,
            'status': status
        }
    
    def ignore_duplicate(
        self,
        duplicate_id: int,
        current_user: User
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a duplicate as ignored (convenience method for false positives).
        
        Args:
            duplicate_id: Duplicate record ID
            current_user: User performing the action
        
        Returns:
            Dict with result or None if not found
        """
        return self.update_duplicate_status(duplicate_id, 'ignored', current_user)
    
    def merge_contacts(
        self,
        contact_id_1: int,
        contact_id_2: int,
        selected_fields: Dict[str, str],
        current_user: User
    ) -> Optional[Dict[str, Any]]:
        """
        Merge two contacts.
        
        Args:
            contact_id_1: Primary contact ID (will be kept)
            contact_id_2: Secondary contact ID (will be deleted)
            selected_fields: Dict mapping field_name -> 'primary' or 'secondary'
                            Example: {'email': 'primary', 'phone': 'secondary'}
            current_user: User performing the merge
        
        Returns:
            Dict with merge result or None if contacts not found
        """
        # Get contacts
        contact1 = self.db.query(Contact).filter(Contact.id == contact_id_1).first()
        contact2 = self.db.query(Contact).filter(Contact.id == contact_id_2).first()
        
        if not contact1 or not contact2:
            return None
        
        # Convert to dicts
        c1_dict = self._contact_to_full_dict(contact1)
        c2_dict = self._contact_to_full_dict(contact2)
        
        # Merge
        merged = duplicate_utils.merge_contacts(c1_dict, c2_dict, selected_fields)
        
        # Update primary contact
        for field, value in merged.items():
            if hasattr(contact1, field):
                setattr(contact1, field, value)
        
        # Update duplicate record
        dup = self.db.query(DuplicateContact).filter(
            DuplicateContact.contact_id_1 == min(contact_id_1, contact_id_2),
            DuplicateContact.contact_id_2 == max(contact_id_1, contact_id_2)
        ).first()
        
        if dup:
            dup.status = 'merged'
            dup.reviewed_at = func.now()
            dup.reviewed_by = current_user.id
            dup.merged_into = contact_id_1
        
        # Audit log
        create_audit_log(
            db=self.db,
            contact_id=contact_id_1,
            user=current_user,
            action='merged',
            entity_type='contact',
            changes={'merged_from': contact_id_2, 'selected_fields': selected_fields}
        )
        
        # Delete secondary contact
        self.delete(contact2)
        
        self.commit()
        self.refresh(contact1)
        
        return {
            'message': 'Contacts merged successfully',
            'merged_contact_id': contact_id_1,
            'deleted_contact_id': contact_id_2,
            'merged_contact': contact1
        }
    
    @staticmethod
    def _format_contact(contact: Contact) -> Dict[str, Any]:
        """
        Format contact for duplicate list display.
        
        Args:
            contact: Contact instance
        
        Returns:
            Dict with minimal contact data
        """
        full_name = contact.full_name or f"{contact.first_name or ''} {contact.last_name or ''}".strip()
        return {
            'id': contact.id,
            'full_name': full_name,
            'email': contact.email,
            'phone': contact.phone,
            'company': contact.company,
        }
    
    @staticmethod
    def _contact_to_dict(contact: Contact) -> Dict[str, Any]:
        """
        Convert Contact to dictionary for duplicate detection.
        
        Args:
            contact: Contact instance
        
        Returns:
            Dict with relevant fields for comparison
        """
        return {
            'id': contact.id,
            'full_name': contact.full_name,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'phone': contact.phone,
            'company': contact.company,
            'position': contact.position,
        }
    
    @staticmethod
    def _contact_to_full_dict(contact: Contact) -> Dict[str, Any]:
        """
        Convert Contact to full dictionary for merging.
        
        Args:
            contact: Contact instance
        
        Returns:
            Dict with all mergeable fields
        """
        return {
            'full_name': contact.full_name,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'middle_name': contact.middle_name,
            'email': contact.email,
            'phone': contact.phone,
            'phone_mobile': contact.phone_mobile,
            'phone_work': contact.phone_work,
            'company': contact.company,
            'position': contact.position,
            'department': contact.department,
            'address': contact.address,
            'address_additional': contact.address_additional,
            'website': contact.website,
            'birthday': contact.birthday,
            'comment': contact.comment,
            'source': contact.source,
            'status': contact.status,
            'priority': contact.priority,
        }

