"""
Settings Repository Layer
Handles all database operations for Settings models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ..models.settings import Settings


class SettingsRepository:
    """Repository for Settings model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_setting_by_key(self, key: str) -> Optional[Settings]:
        """
        Get setting by key.
        
        Args:
            key: Setting key
        
        Returns:
            Settings instance or None
        """
        return self.db.query(Settings).filter(Settings.key == key).first()
    
    def get_all_settings(self) -> List[Settings]:
        """
        Get all settings.
        
        Returns:
            List of Settings instances
        """
        return self.db.query(Settings).all()
    
    def get_settings_by_category(self, category: str) -> List[Settings]:
        """
        Get settings by category.
        
        Args:
            category: Settings category
        
        Returns:
            List of Settings instances
        """
        return self.db.query(Settings).filter(Settings.category == category).all()
    
    def create_setting(self, setting_data: Dict[str, Any]) -> Settings:
        """
        Create a new setting.
        
        Args:
            setting_data: Dictionary with setting data
        
        Returns:
            Created Settings instance
        """
        setting = Settings(**setting_data)
        self.db.add(setting)
        self.db.flush()
        return setting
    
    def update_setting(self, setting: Settings, update_data: Dict[str, Any]) -> Settings:
        """
        Update setting record.
        
        Args:
            setting: Settings instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated Settings instance
        """
        for key, value in update_data.items():
            if hasattr(setting, key):
                setattr(setting, key, value)
        self.db.add(setting)
        return setting
    
    def update_setting_value(self, key: str, value: str) -> Optional[Settings]:
        """
        Update setting value by key.
        
        Args:
            key: Setting key
            value: New value
        
        Returns:
            Updated Settings instance or None
        """
        setting = self.get_setting_by_key(key)
        if setting:
            setting.value = value
            self.db.add(setting)
        return setting
    
    def delete_setting(self, setting: Settings) -> None:
        """
        Delete setting record.
        
        Args:
            setting: Settings instance to delete
        """
        self.db.delete(setting)
    
    def delete_setting_by_key(self, key: str) -> bool:
        """
        Delete setting by key.
        
        Args:
            key: Setting key
        
        Returns:
            True if deleted, False otherwise
        """
        setting = self.get_setting_by_key(key)
        if setting:
            self.db.delete(setting)
            return True
        return False
    
    def count_settings(self) -> int:
        """
        Count total number of settings.
        
        Returns:
            Total count
        """
        return self.db.query(Settings).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

