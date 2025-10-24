"""
Contact Service

Handles all business logic related to contacts including:
- CRUD operations
- Search and filtering
- Duplicate detection
- Audit logging
- Phone number formatting
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any, Tuple
import uuid
import logging

from .base import BaseService
from ..models import Contact, User, Tag, Group, DuplicateContact, AuditLog
from ..core import duplicates as duplicate_utils
from ..core.phone import format_phone_number
from ..core.utils import create_audit_log, get_system_setting
from ..core.metrics import (
    contacts_created_counter,
    contacts_updated_counter,
    contacts_deleted_counter,
    contacts_total
)


class ContactService(BaseService):
    """
    Service for managing contacts business logic.
    
    Separates business logic from API endpoints, providing reusable
    methods for contact operations across the application.
    """
    
    def list_contacts(
        self,
        q: Optional[str] = None,
        company: Optional[str] = None,
        position: Optional[str] = None,
        tags: Optional[str] = None,
        groups: Optional[str] = None,
        sort_by: str = 'id',
        sort_order: str = 'desc',
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of contacts with advanced search and filtering.
        
        Args:
            q: Full-text search query
            company: Company name filter
            position: Position filter
            tags: Comma-separated tag names
            groups: Comma-separated group names
            sort_by: Field to sort by (id, full_name, company, position)
            sort_order: Sort direction (asc, desc)
            page: Page number (starts from 1)
            limit: Items per page
        
        Returns:
            Dict with items, total, page, limit, and pages
        """
        query = self.db.query(Contact)
        
        # Full-text search
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Contact.full_name.ilike(search_term),
                    Contact.company.ilike(search_term),
                    Contact.position.ilike(search_term),
                    Contact.email.ilike(search_term),
                    Contact.phone.ilike(search_term),
                    Contact.website.ilike(search_term),
                    Contact.address.ilike(search_term)
                )
            )
        
        # Filter by company
        if company:
            query = query.filter(Contact.company.ilike(f"%{company}%"))
        
        # Filter by position
        if position:
            query = query.filter(Contact.position.ilike(f"%{position}%"))
        
        # Filter by tags
        if tags:
            tag_names = [name.strip() for name in tags.split(',') if name.strip()]
            if tag_names:
                tag_records = self.db.query(Tag).filter(Tag.name.in_(tag_names)).all()
                tag_ids = [tag.id for tag in tag_records]
                
                if tag_ids:
                    query = query.filter(Contact.tags.any(Tag.id.in_(tag_ids)))
        
        # Filter by groups
        if groups:
            group_names = [name.strip() for name in groups.split(',') if name.strip()]
            if group_names:
                group_records = self.db.query(Group).filter(Group.name.in_(group_names)).all()
                group_ids = [group.id for group in group_records]
                
                if group_ids:
                    query = query.filter(Contact.groups.any(Group.id.in_(group_ids)))
        
        # Sorting
        sort_field = getattr(Contact, sort_by, Contact.id)
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Get total count before pagination
        total = query.count()
        
        # Calculate pagination
        pages = (total + limit - 1) // limit  # Ceiling division
        offset = (page - 1) * limit
        
        # Apply pagination
        items = query.offset(offset).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages
        }
    
    def search_contacts(self, q: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fast global search for contacts.
        
        Args:
            q: Search query
            limit: Maximum number of results
        
        Returns:
            List of contact dictionaries with minimal data
        """
        search_term = f"%{q}%"
        
        contacts = self.db.query(Contact).filter(
            or_(
                Contact.full_name.ilike(search_term),
                Contact.company.ilike(search_term),
                Contact.position.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.phone.ilike(search_term)
            )
        ).limit(limit).all()
        
        # Return simplified data
        return [{
            'id': c.id,
            'full_name': c.full_name,
            'company': c.company,
            'position': c.position,
            'email': c.email,
            'phone': c.phone
        } for c in contacts]
    
    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """
        Get a contact by ID.
        
        Args:
            contact_id: Contact ID
        
        Returns:
            Contact instance or None if not found
        """
        return self.db.query(Contact).filter(Contact.id == contact_id).first()
    
    def get_by_uid(self, uid: str) -> Optional[Contact]:
        """
        Get a contact by UID.
        
        Args:
            uid: Contact UID
        
        Returns:
            Contact instance or None if not found
        """
        return self.db.query(Contact).filter(Contact.uid == uid).first()
    
    def create_contact(
        self,
        data: Dict[str, Any],
        current_user: User,
        auto_detect_duplicates: bool = True
    ) -> Contact:
        """
        Create a new contact with automatic phone formatting and duplicate detection.
        
        Args:
            data: Contact data dictionary
            current_user: User creating the contact
            auto_detect_duplicates: Whether to auto-detect duplicates
        
        Returns:
            Created Contact instance
        """
        payload = data.copy()
        
        # Generate UID if not provided
        if not payload.get('uid'):
            payload['uid'] = uuid.uuid4().hex
        
        # Format phone numbers
        self._format_phone_numbers(payload)
        
        # Create contact
        contact = Contact(**payload)
        self.add(contact)
        self.flush()  # Get ID without committing
        
        # Audit log
        create_audit_log(
            db=self.db,
            contact_id=contact.id,
            user=current_user,
            action='created',
            entity_type='contact',
            changes=payload
        )
        
        self.commit()
        self.refresh(contact)
        
        # Update metrics
        contacts_created_counter.inc()
        contacts_total.set(self.db.query(Contact).count())
        
        # Auto-detect duplicates if enabled
        if auto_detect_duplicates:
            try:
                self._detect_and_save_duplicates(contact)
            except Exception as e:
                # Don't fail contact creation if duplicate detection fails
                self.logger.error(f"Duplicate detection error: {e}")
        
        return contact
    
    def update_contact(
        self,
        contact_id: int,
        data: Dict[str, Any],
        current_user: User
    ) -> Optional[Contact]:
        """
        Update an existing contact.
        
        Args:
            contact_id: Contact ID to update
            data: Update data dictionary
            current_user: User performing the update
        
        Returns:
            Updated Contact instance or None if not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return None
        
        update_data = data.copy()
        
        # Format phone numbers
        self._format_phone_numbers(update_data)
        
        # Audit log
        create_audit_log(
            db=self.db,
            contact_id=contact.id,
            user=current_user,
            action='updated',
            entity_type='contact',
            changes=update_data
        )
        
        # Update fields
        for k, v in update_data.items():
            if hasattr(contact, k):
                setattr(contact, k, v)
        
        self.commit()
        self.refresh(contact)
        
        # Update metrics
        contacts_updated_counter.inc()
        
        return contact
    
    def delete_contact(self, contact_id: int, current_user: User) -> bool:
        """
        Delete a contact.
        
        Args:
            contact_id: Contact ID to delete
            current_user: User performing the deletion
        
        Returns:
            True if deleted, False if not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return False
        
        # Audit log (before deletion)
        create_audit_log(
            db=self.db,
            contact_id=contact.id,
            user=current_user,
            action='deleted',
            entity_type='contact',
            changes={'full_name': contact.full_name, 'company': contact.company}
        )
        
        self.delete(contact)
        self.commit()
        
        # Update metrics
        contacts_deleted_counter.inc()
        contacts_total.set(self.db.query(Contact).count())
        
        return True
    
    def get_contact_history(self, contact_id: int, limit: int = 50) -> List[AuditLog]:
        """
        Get audit history for a contact.
        
        Args:
            contact_id: Contact ID
            limit: Maximum number of records
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.contact_id == contact_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def _format_phone_numbers(self, data: Dict[str, Any]) -> None:
        """
        Format all phone number fields in the data dictionary.
        
        Args:
            data: Data dictionary to modify in-place
        """
        phone_fields = ['phone', 'phone_mobile', 'phone_work', 'phone_additional']
        for field in phone_fields:
            if field in data and data[field]:
                data[field] = format_phone_number(data[field])
    
    def _detect_and_save_duplicates(self, contact: Contact) -> None:
        """
        Detect and save potential duplicates for a contact.
        
        Args:
            contact: Contact instance to check for duplicates
        """
        # Check if duplicate detection is enabled
        duplicate_enabled = get_system_setting(self.db, 'duplicate_detection_enabled', 'true')
        if duplicate_enabled.lower() != 'true':
            return
        
        threshold = float(get_system_setting(self.db, 'duplicate_similarity_threshold', '0.75'))
        
        # Get existing contacts for comparison
        existing_contacts = self.db.query(Contact).filter(Contact.id != contact.id).all()
        
        # Convert to dict for comparison
        contact_dict = self._contact_to_dict(contact)
        existing_dicts = [self._contact_to_dict(c) for c in existing_contacts]
        
        # Find duplicates
        duplicates = duplicate_utils.find_duplicates_for_new_contact(
            contact_dict,
            existing_dicts,
            threshold
        )
        
        # Save duplicates to database
        for existing_contact_dict, score, field_scores in duplicates:
            existing_id = existing_contact_dict['id']
            id1, id2 = sorted([contact.id, existing_id])
            
            # Check if already exists
            existing_dup = self.db.query(DuplicateContact).filter(
                (DuplicateContact.contact_id_1 == id1) & (DuplicateContact.contact_id_2 == id2)
            ).first()
            
            if not existing_dup:
                new_dup = DuplicateContact(
                    contact_id_1=id1,
                    contact_id_2=id2,
                    similarity_score=score,
                    match_fields=field_scores,
                    status='pending',
                    auto_detected=True
                )
                self.add(new_dup)
        
        self.commit()
    
    @staticmethod
    def _contact_to_dict(contact: Contact) -> Dict[str, Any]:
        """
        Convert Contact model to dictionary for duplicate comparison.
        
        Args:
            contact: Contact instance
        
        Returns:
            Dictionary with relevant fields
        """
        return {
            'id': contact.id,
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
        }

