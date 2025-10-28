"""
spaCy-based Validator
Uses NER (Named Entity Recognition) for names, locations
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseValidator

logger = logging.getLogger(__name__)


class SpacyValidator(BaseValidator):
    """spaCy NER validation for names and locations"""
    
    def __init__(self):
        super().__init__("spaCy")
        self.nlp = None
        self._initialize_spacy()
    
    def _initialize_spacy(self):
        """Initialize spaCy model"""
        try:
            import spacy
            
            # Try to load Russian model
            try:
                self.nlp = spacy.load("ru_core_news_sm")
                logger.info("✅ spaCy Russian model loaded")
            except OSError:
                # Fallback to English
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.warning("⚠️ Using English model, Russian model not found")
                except OSError:
                    logger.warning("⚠️ No spaCy models found, validator disabled")
                    self.enabled = False
        except ImportError:
            logger.warning("⚠️ spaCy not installed, validator disabled")
            self.enabled = False
    
    def validate(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Validate field using spaCy NER"""
        if not self.enabled or not self.nlp:
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 0.5,
                "issues": ["spaCy not available"]
            }
        
        if not value or not isinstance(value, str):
            return {
                "valid": False,
                "corrected_value": value,
                "confidence": 0.0,
                "issues": ["Empty or non-string value"]
            }
        
        value = value.strip()
        
        # Validate based on field type
        if field == 'full_name':
            return self._validate_name(value)
        elif field == 'address':
            return self._validate_address(value)
        elif field == 'company':
            return self._validate_company(value)
        
        # Default: pass through
        return {
            "valid": True,
            "corrected_value": value,
            "confidence": 0.5,
            "issues": []
        }
    
    def _validate_name(self, name: str) -> Dict[str, Any]:
        """Validate name using NER"""
        doc = self.nlp(name)
        
        issues = []
        confidence = 0.5
        
        # Check if contains PERSON entity
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PER' or ent.label_ == 'PERSON']
        
        if persons:
            # Found person entity
            confidence = 0.9
            corrected = persons[0]  # Use first person entity
            if corrected != name:
                issues.append(f"Extracted person name: {corrected}")
                return {
                    "valid": True,
                    "corrected_value": corrected,
                    "confidence": confidence,
                    "issues": issues
                }
        else:
            # No person entity found, but might still be valid
            # Check if it looks like a name (capitalized words)
            words = name.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words if w):
                confidence = 0.7
                issues.append("Looks like a name (capitalized words)")
            else:
                confidence = 0.3
                issues.append("No PERSON entity found")
        
        return {
            "valid": True,
            "corrected_value": name,
            "confidence": confidence,
            "issues": issues
        }
    
    def _validate_address(self, address: str) -> Dict[str, Any]:
        """Validate address using NER"""
        doc = self.nlp(address)
        
        # Check for location entities
        locations = [ent.text for ent in doc.ents if ent.label_ in ['LOC', 'GPE', 'FAC']]
        
        confidence = 0.8 if locations else 0.5
        issues = []
        
        if locations:
            issues.append(f"Contains locations: {', '.join(locations)}")
        else:
            issues.append("No location entities found")
        
        return {
            "valid": True,
            "corrected_value": address,
            "confidence": confidence,
            "issues": issues
        }
    
    def _validate_company(self, company: str) -> Dict[str, Any]:
        """Validate company name using NER"""
        doc = self.nlp(company)
        
        # Check for organization entities
        orgs = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        
        confidence = 0.9 if orgs else 0.6
        issues = []
        
        if orgs:
            corrected = orgs[0]
            if corrected != company:
                issues.append(f"Extracted org: {corrected}")
                return {
                    "valid": True,
                    "corrected_value": corrected,
                    "confidence": confidence,
                    "issues": issues
                }
        else:
            # Check for company indicators (ООО, LLC, etc.)
            indicators = ['ООО', 'ОАО', 'ЗАО', 'ПАО', 'LLC', 'Inc', 'Ltd', 'Corp']
            if any(ind in company for ind in indicators):
                confidence = 0.8
                issues.append("Contains company indicator")
        
        return {
            "valid": True,
            "corrected_value": company,
            "confidence": confidence,
            "issues": issues
        }

