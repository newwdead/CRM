"""
Validator Service - Post-processing and validation of extracted fields
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ValidatorService:
    """Service for validating and correcting extracted contact fields"""
    
    def validate_and_correct(self, data: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """
        Validate and correct all fields
        
        Args:
            data: Extracted contact fields
        
        Returns:
            Corrected data
        """
        corrected = data.copy()
        
        # Email validation
        if corrected.get('email'):
            corrected['email'] = self._validate_email(corrected['email'])
        
        # Phone validation
        if corrected.get('phone'):
            corrected['phone'] = self._validate_phone(corrected['phone'])
        
        # Website validation
        if corrected.get('website'):
            corrected['website'] = self._validate_website(corrected['website'])
        
        return corrected
    
    def _validate_email(self, email: str) -> Optional[str]:
        """Validate and normalize email"""
        email_pattern = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, email, re.IGNORECASE)
        return match.group(0).lower() if match else None
    
    def _validate_phone(self, phone: str) -> Optional[str]:
        """Validate and normalize phone"""
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned if len(cleaned) >= 7 else None
    
    def _validate_website(self, website: str) -> Optional[str]:
        """Validate and normalize website"""
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website


# Global singleton
_validator_service = None


def get_validator_service() -> ValidatorService:
    """Get validator service instance"""
    global _validator_service
    if _validator_service is None:
        _validator_service = ValidatorService()
    return _validator_service
