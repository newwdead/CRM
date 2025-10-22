"""
Contact Repository
Handles all database operations for contacts
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc
from typing import List, Optional, Dict, Any, Tuple
import logging

from ..models import Contact, Tag, Group

logger = logging.getLogger(__name__)


class ContactRepository:
    """
    Repository for Contact database operations.
    
    Encapsulates all SQL queries and database access for contacts,
    following the Repository pattern for clean separation of concerns.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        eager_load: bool = True
    ) -> List[Contact]:
        """Get all contacts with optional eager loading."""
        query = self.db.query(Contact)
        
        if eager_load:
            query = query.options(
                joinedload(Contact.tags),
                joinedload(Contact.groups)
            )
        
        return query.offset(skip).limit(limit).all()
    
    def find_by_id(self, contact_id: int, eager_load: bool = True) -> Optional[Contact]:
        """Find contact by ID."""
        query = self.db.query(Contact).filter(Contact.id == contact_id)
        
        if eager_load:
            query = query.options(
                joinedload(Contact.tags),
                joinedload(Contact.groups)
            )
        
        return query.first()
    
    def find_by_uid(self, uid: str) -> Optional[Contact]:
        """Find contact by UID."""
        return self.db.query(Contact).filter(Contact.uid == uid).first()
    
    def search(
        self,
        search_term: str,
        fields: Optional[List[str]] = None
    ) -> List[Contact]:
        """
        Search contacts by multiple fields.
        
        Args:
            search_term: Search query
            fields: List of fields to search in (default: all text fields)
        """
        if not fields:
            fields = ['full_name', 'company', 'position', 'email', 'phone', 'website', 'address']
        
        search_pattern = f"%{search_term}%"
        filters = []
        
        if 'full_name' in fields:
            filters.append(Contact.full_name.ilike(search_pattern))
        if 'company' in fields:
            filters.append(Contact.company.ilike(search_pattern))
        if 'position' in fields:
            filters.append(Contact.position.ilike(search_pattern))
        if 'email' in fields:
            filters.append(Contact.email.ilike(search_pattern))
        if 'phone' in fields:
            filters.append(Contact.phone.ilike(search_pattern))
        if 'website' in fields:
            filters.append(Contact.website.ilike(search_pattern))
        if 'address' in fields:
            filters.append(Contact.address.ilike(search_pattern))
        
        return self.db.query(Contact).filter(or_(*filters)).all()
    
    def filter_by(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort_by: str = 'id',
        sort_order: str = 'desc'
    ) -> Tuple[List[Contact], int]:
        """
        Filter contacts with pagination and sorting.
        
        Returns:
            Tuple of (contacts list, total count)
        """
        query = self.db.query(Contact).options(
            joinedload(Contact.tags),
            joinedload(Contact.groups)
        )
        
        # Apply filters
        for key, value in filters.items():
            if value and hasattr(Contact, key):
                if isinstance(value, str):
                    query = query.filter(getattr(Contact, key).ilike(f"%{value}%"))
                else:
                    query = query.filter(getattr(Contact, key) == value)
        
        # Sorting
        sort_field = getattr(Contact, sort_by, Contact.id)
        if sort_order.lower() == 'asc':
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        contacts = query.offset(skip).limit(limit).all()
        
        return contacts, total
    
    def filter_by_tags(self, tag_names: List[str]) -> List[Contact]:
        """Filter contacts that have any of the specified tags."""
        tag_records = self.db.query(Tag).filter(Tag.name.in_(tag_names)).all()
        tag_ids = [tag.id for tag in tag_records]
        
        if not tag_ids:
            return []
        
        return self.db.query(Contact).filter(
            Contact.tags.any(Tag.id.in_(tag_ids))
        ).all()
    
    def filter_by_groups(self, group_names: List[str]) -> List[Contact]:
        """Filter contacts that have any of the specified groups."""
        group_records = self.db.query(Group).filter(Group.name.in_(group_names)).all()
        group_ids = [group.id for group in group_records]
        
        if not group_ids:
            return []
        
        return self.db.query(Contact).filter(
            Contact.groups.any(Group.id.in_(group_ids))
        ).all()
    
    def create(self, contact_data: Dict[str, Any]) -> Contact:
        """Create a new contact."""
        contact = Contact(**contact_data)
        self.db.add(contact)
        return contact
    
    def update(self, contact: Contact, update_data: Dict[str, Any]) -> Contact:
        """Update an existing contact."""
        for key, value in update_data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        return contact
    
    def delete(self, contact: Contact) -> None:
        """Delete a contact."""
        self.db.delete(contact)
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count contacts with optional filters."""
        query = self.db.query(Contact)
        
        if filters:
            for key, value in filters.items():
                if value and hasattr(Contact, key):
                    if isinstance(value, str):
                        query = query.filter(getattr(Contact, key).ilike(f"%{value}%"))
                    else:
                        query = query.filter(getattr(Contact, key) == value)
        
        return query.count()
    
    def exists(self, contact_id: int) -> bool:
        """Check if contact exists."""
        return self.db.query(Contact).filter(Contact.id == contact_id).count() > 0
    
    def flush(self) -> None:
        """Flush changes to database without committing."""
        self.db.flush()
    
    def commit(self) -> None:
        """Commit changes to database."""
        self.db.commit()
    
    def refresh(self, contact: Contact) -> None:
        """Refresh contact from database."""
        self.db.refresh(contact)
    
    def rollback(self) -> None:
        """Rollback changes."""
        self.db.rollback()

