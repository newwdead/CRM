"""
AppSetting Repository Layer
Handles all database operations for AppSetting models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ..models.settings import AppSetting, SystemAppSetting


class AppSettingRepository:
    """Repository for AppSetting model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_setting_by_key(self, key: str) -> Optional[AppSetting]:
        """
        Get setting by key.
        
        Args:
            key: Setting key
        
        Returns:
            AppSetting instance or None
        """
        return self.db.query(AppSetting).filter(AppSetting.key == key).first()
    
    def get_all_settings(self) -> List[AppSetting]:
        """
        Get all settings.
        
        Returns:
            List of AppSetting instances
        """
        return self.db.query(AppSetting).all()
    
    def get_settings_by_category(self, category: str) -> List[AppSetting]:
        """
        Get settings by category.
        
        Args:
            category: AppSetting category
        
        Returns:
            List of AppSetting instances
        """
        return self.db.query(AppSetting).filter(AppSetting.category == category).all()
    
    def create_setting(self, setting_data: Dict[str, Any]) -> AppSetting:
        """
        Create a new setting.
        
        Args:
            setting_data: Dictionary with setting data
        
        Returns:
            Created AppSetting instance
        """
        setting = AppSetting(**setting_data)
        self.db.add(setting)
        self.db.flush()
        return setting
    
    def update_setting(self, setting: AppSetting, update_data: Dict[str, Any]) -> AppSetting:
        """
        Update setting record.
        
        Args:
            setting: AppSetting instance to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated AppSetting instance
        """
        for key, value in update_data.items():
            if hasattr(setting, key):
                setattr(setting, key, value)
        self.db.add(setting)
        return setting
    
    def update_setting_value(self, key: str, value: str) -> Optional[AppSetting]:
        """
        Update setting value by key.
        
        Args:
            key: Setting key
            value: New value
        
        Returns:
            Updated AppSetting instance or None
        """
        setting = self.get_setting_by_key(key)
        if setting:
            setting.value = value
            self.db.add(setting)
        return setting
    
    def delete_setting(self, setting: AppSetting) -> None:
        """
        Delete setting record.
        
        Args:
            setting: AppSetting instance to delete
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
        return self.db.query(AppSetting).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

