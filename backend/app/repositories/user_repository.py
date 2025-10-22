"""
User Repository Layer
Handles all database operations for User models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ..models.user import User


class UserRepository:
    """Repository for User model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
        
        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
        
        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email address
        
        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of User instances
        """
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active User instances
        """
        return self.db.query(User).filter(User.is_active == True).all()
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary with user data
        
        Returns:
            Created User instance
        """
        user = User(**user_data)
        self.db.add(user)
        self.db.flush()
        return user
    
    def update_user(self, user: User, update_data: Dict[str, Any]) -> User:
        """
        Update user record.
        
        Args:
            user: User instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated User instance
        """
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.add(user)
        return user
    
    def delete_user(self, user: User) -> None:
        """
        Delete user record.
        
        Args:
            user: User instance to delete
        """
        self.db.delete(user)
    
    def count_users(self) -> int:
        """
        Count total number of users.
        
        Returns:
            Total count
        """
        return self.db.query(User).count()
    
    def count_active_users(self) -> int:
        """
        Count active users.
        
        Returns:
            Count of active users
        """
        return self.db.query(User).filter(User.is_active == True).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

