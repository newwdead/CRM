"""
Settings Service

Handles all business logic related to system settings:
- Getting and setting system settings
- Managing settings with defaults
- Validating settings
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from .base import BaseService
from ..models import AppSetting, SystemSettings
from ..core.utils import get_system_setting


class SettingsService(BaseService):
    """
    Service for managing system settings.
    
    Provides methods for:
    - Getting and setting system settings
    - Managing configuration
    - Settings validation
    """
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a system setting value.
        
        Args:
            key: Setting key
            default: Default value if setting not found
        
        Returns:
            Setting value or default
        """
        return get_system_setting(self.db, key, default)
    
    def set_setting(self, key: str, value: str) -> AppSetting:
        """
        Set a system setting value.
        
        Args:
            key: Setting key
            value: Setting value
        
        Returns:
            AppSetting instance
        """
        setting = self.db.query(AppSetting).filter(AppSetting.key == key).first()
        
        if setting:
            setting.value = value
        else:
            setting = AppSetting(key=key, value=value)
            self.add(setting)
        
        self.commit()
        self.refresh(setting)
        
        return setting
    
    def get_all_settings(self) -> List[AppSetting]:
        """
        Get all system settings.
        
        Returns:
            List of AppSetting instances
        """
        return self.db.query(AppSetting).all()
    
    def get_settings_dict(self) -> Dict[str, str]:
        """
        Get all settings as a dictionary.
        
        Returns:
            Dict mapping keys to values
        """
        settings = self.get_all_settings()
        return {s.key: s.value for s in settings}
    
    def delete_setting(self, key: str) -> bool:
        """
        Delete a system setting.
        
        Args:
            key: Setting key to delete
        
        Returns:
            True if deleted, False if not found
        """
        setting = self.db.query(AppSetting).filter(AppSetting.key == key).first()
        
        if not setting:
            return False
        
        self.delete(setting)
        self.commit()
        
        return True
    
    def get_system_settings(self) -> Optional[SystemSettings]:
        """
        Get the SystemSettings record (singleton).
        
        Returns:
            SystemSettings instance or None
        """
        return self.db.query(SystemSettings).first()
    
    def update_system_settings(self, data: Dict[str, Any]) -> SystemSettings:
        """
        Update system settings.
        
        Args:
            data: Dictionary of settings to update
        
        Returns:
            Updated SystemSettings instance
        """
        settings = self.get_system_settings()
        
        if not settings:
            settings = SystemSettings()
            self.add(settings)
        
        # Update fields
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.commit()
        self.refresh(settings)
        
        return settings
    
    def get_ocr_settings(self) -> Dict[str, Any]:
        """
        Get OCR-related settings.
        
        Returns:
            Dict with OCR settings
        """
        return {
            'provider': self.get_setting('ocr_provider', 'tesseract'),
            'language': self.get_setting('ocr_language', 'eng'),
            'enable_preprocessing': self.get_setting('ocr_enable_preprocessing', 'true'),
            'confidence_threshold': float(self.get_setting('ocr_confidence_threshold', '0.5')),
        }
    
    def get_duplicate_detection_settings(self) -> Dict[str, Any]:
        """
        Get duplicate detection settings.
        
        Returns:
            Dict with duplicate detection settings
        """
        return {
            'enabled': self.get_setting('duplicate_detection_enabled', 'true').lower() == 'true',
            'threshold': float(self.get_setting('duplicate_similarity_threshold', '0.75')),
            'auto_detect': self.get_setting('duplicate_auto_detect', 'true').lower() == 'true',
        }
    
    def set_ocr_provider(self, provider: str) -> AppSetting:
        """
        Set OCR provider.
        
        Args:
            provider: Provider name (tesseract, google_vision, paddleocr)
        
        Returns:
            Updated AppSetting
        """
        valid_providers = ['tesseract', 'google_vision', 'paddleocr']
        if provider not in valid_providers:
            raise ValueError(f'Invalid OCR provider. Must be one of: {valid_providers}')
        
        return self.set_setting('ocr_provider', provider)
    
    def set_duplicate_detection_enabled(self, enabled: bool) -> AppSetting:
        """
        Enable or disable duplicate detection.
        
        Args:
            enabled: Whether to enable duplicate detection
        
        Returns:
            Updated AppSetting
        """
        return self.set_setting('duplicate_detection_enabled', 'true' if enabled else 'false')
    
    def set_duplicate_threshold(self, threshold: float) -> AppSetting:
        """
        Set duplicate similarity threshold.
        
        Args:
            threshold: Similarity threshold (0-1)
        
        Returns:
            Updated AppSetting
        """
        if not 0 <= threshold <= 1:
            raise ValueError('Threshold must be between 0 and 1')
        
        return self.set_setting('duplicate_similarity_threshold', str(threshold))

