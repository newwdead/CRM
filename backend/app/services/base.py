"""
Base service class for business logic layer.

All services should inherit from this class to ensure consistent structure
and shared functionality across the service layer.
"""
from sqlalchemy.orm import Session
from typing import Optional
import logging


class BaseService:
    """
    Base service class providing common functionality for all services.
    
    This class provides:
    - Database session management
    - Logging setup
    - Common utility methods
    - Consistent error handling patterns
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def commit(self):
        """Commit the current transaction."""
        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing transaction: {e}")
            self.db.rollback()
            raise
    
    def rollback(self):
        """Rollback the current transaction."""
        self.db.rollback()
    
    def refresh(self, instance):
        """
        Refresh an instance from the database.
        
        Args:
            instance: SQLAlchemy model instance to refresh
        """
        self.db.refresh(instance)
        return instance
    
    def add(self, instance):
        """
        Add an instance to the session.
        
        Args:
            instance: SQLAlchemy model instance to add
        """
        self.db.add(instance)
        return instance
    
    def delete(self, instance):
        """
        Delete an instance from the database.
        
        Args:
            instance: SQLAlchemy model instance to delete
        """
        self.db.delete(instance)
    
    def flush(self):
        """Flush pending changes to the database."""
        self.db.flush()

