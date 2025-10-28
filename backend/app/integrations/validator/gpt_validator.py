"""
GPT-based Validator
Uses OpenAI GPT for intelligent validation and correction
"""
import os
import logging
from typing import Dict, Any, Optional
from .base import BaseValidator

logger = logging.getLogger(__name__)


class GPTValidator(BaseValidator):
    """GPT-based validation using OpenAI API"""
    
    def __init__(self):
        super().__init__("GPT")
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not self.api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set, GPT validator disabled")
            self.enabled = False
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("✅ GPT validator initialized")
        except ImportError:
            logger.warning("⚠️ openai package not installed, GPT validator disabled")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT validator: {e}")
            self.enabled = False
    
    def validate(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Validate field using GPT"""
        if not self.enabled or not self.client:
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 0.5,
                "issues": ["GPT not available"]
            }
        
        if not value or not isinstance(value, str):
            return {
                "valid": False,
                "corrected_value": value,
                "confidence": 0.0,
                "issues": ["Empty or non-string value"]
            }
        
        # Build prompt based on field type
        prompt = self._build_prompt(field, value, data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data validator for business card OCR. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            result = self._parse_gpt_response(result_text, value)
            
            logger.debug(f"🤖 GPT {field}: '{value}' → '{result['corrected_value']}' (conf: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT validation error: {e}")
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 0.5,
                "issues": [f"GPT error: {str(e)}"]
            }
    
    def _build_prompt(self, field: str, value: str, data: Dict[str, Any]) -> str:
        """Build GPT prompt"""
        context = f"Business card OCR extracted: {field} = '{value}'"
        
        if field == 'full_name':
            return f"""{context}

Task: Validate and correct this name. Check:
1. Is this a valid person name?
2. Is the order correct? (First Last, not Last First)
3. Remove any OCR artifacts

Return JSON:
{{
  "valid": true/false,
  "corrected": "corrected name",
  "confidence": 0.0-1.0,
  "issue": "description if any"
}}"""
        
        elif field == 'email':
            return f"""{context}

Task: Validate and correct this email. Check:
1. Has @ symbol
2. Valid domain
3. No OCR artifacts (Cyrillic letters, spaces)

Return JSON:
{{
  "valid": true/false,
  "corrected": "corrected@email.com",
  "confidence": 0.0-1.0,
  "issue": "description if any"
}}"""
        
        elif field == 'phone':
            return f"""{context}

Task: Validate and correct this phone number. Check:
1. Normalize to international format (+7...)
2. Remove OCR artifacts (letters mixed in numbers)
3. Ensure 10-11 digits

Return JSON:
{{
  "valid": true/false,
  "corrected": "+71234567890",
  "confidence": 0.0-1.0,
  "issue": "description if any"
}}"""
        
        elif field == 'company':
            full_context = f"Name: {data.get('full_name', '')}, Position: {data.get('position', '')}, Company: {value}"
            return f"""{full_context}

Task: Validate this company name. Check:
1. Is this a company name or something else?
2. Remove OCR artifacts
3. Check consistency with position

Return JSON:
{{
  "valid": true/false,
  "corrected": "Company Name",
  "confidence": 0.0-1.0,
  "issue": "description if any"
}}"""
        
        else:
            return f"""{context}

Task: Validate this {field} field value. Fix any OCR errors.

Return JSON:
{{
  "valid": true/false,
  "corrected": "corrected value",
  "confidence": 0.0-1.0,
  "issue": "description if any"
}}"""
    
    def _parse_gpt_response(self, response_text: str, original_value: str) -> Dict[str, Any]:
        """Parse GPT JSON response"""
        import json
        
        try:
            # Try to parse as JSON
            result = json.loads(response_text)
            
            return {
                "valid": result.get("valid", True),
                "corrected_value": result.get("corrected", original_value),
                "confidence": result.get("confidence", 0.8),
                "issues": [result.get("issue", "")] if result.get("issue") else []
            }
        except json.JSONDecodeError:
            # Failed to parse, return original
            logger.warning(f"⚠️ Failed to parse GPT response: {response_text}")
            return {
                "valid": True,
                "corrected_value": original_value,
                "confidence": 0.5,
                "issues": ["GPT response parsing failed"]
            }

