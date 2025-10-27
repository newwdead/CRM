"""
Enhanced Field Extraction for Business Cards
Improved regex patterns and heuristics for better field recognition
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Simple text block representation"""
    text: str
    y: float  # Y coordinate
    confidence: float


class FieldExtractor:
    """
    Enhanced field extractor with improved patterns for Russian/Cyrillic cards
    """
    
    def __init__(self):
        # Position keywords (Russian)
        self.position_keywords = [
            # Generic titles
            r'директор', r'генеральный', r'исполнительный', r'коммерческий',
            r'технический', r'финансовый', r'операционный',
            # Specific roles
            r'менеджер', r'специалист', r'консультант', r'координатор',
            r'руководитель', r'начальник', r'заведующий', r'управляющий',
            r'главный', r'ведущий', r'старший', r'младший',
            # Departments
            r'отдел', r'департамент', r'служба', r'управление',
            # Professions
            r'инженер', r'архитектор', r'дизайнер', r'разработчик',
            r'программист', r'аналитик', r'бухгалтер', r'юрист',
            r'экономист', r'маркетолог', r'логист',
            # English
            r'director', r'manager', r'ceo', r'cto', r'cfo', r'coo',
            r'president', r'vice', r'head', r'chief', r'lead', r'senior',
        ]
        
        # Company indicators
        self.company_indicators = [
            r'ООО', r'ОАО', r'ЗАО', r'ПАО', r'ИП', r'АО',
            r'LLC', r'Inc', r'Ltd', r'GmbH', r'Corp',
            r'Компания', r'Группа', r'Холдинг', r'Корпорация',
            r'Company', r'Group', r'Corporation', r'Holding',
        ]
        
        # Address indicators  
        self.address_indicators = [
            r'ул\.', r'улица', r'пр\.', r'проспект', r'пер\.', r'переулок',
            r'д\.', r'дом', r'стр\.', r'строение', r'кв\.', r'квартира',
            r'оф\.', r'офис', r'эт\.', r'этаж', r'пом\.', r'помещение',
            r'\d{6}',  # Postal code
            r'г\.', r'город', r'обл\.', r'область',
            # English
            r'street', r'st\.', r'ave', r'avenue', r'road', r'rd\.',
            r'floor', r'fl\.', r'suite', r'ste\.', r'building', r'bldg\.',
        ]
    
    def extract_fields(
        self,
        blocks: List,
        image_size: Tuple[int, int],
        combined_text: str
    ) -> Dict[str, Optional[str]]:
        """
        Extract all fields with improved heuristics
        
        Args:
            blocks: List of TextBlock objects with position
            image_size: (width, height) of image
            combined_text: All text concatenated
        
        Returns:
            Dictionary with all extracted fields
        """
        data = {
            "full_name": None,
            "company": None,
            "position": None,
            "email": None,
            "phone": None,
            "phone_mobile": None,
            "phone_work": None,
            "address": None,
            "website": None,
        }
        
        # Sort blocks by position (top to bottom)
        sorted_blocks = sorted(blocks, key=lambda b: b.bbox.y)
        
        # Extract structured fields
        data["email"] = self._extract_email(combined_text)
        data["phone"], data["phone_mobile"], data["phone_work"] = self._extract_phones(combined_text, sorted_blocks)
        data["website"] = self._extract_website(combined_text)
        data["address"] = self._extract_address(combined_text, sorted_blocks)
        data["position"] = self._extract_position(combined_text, sorted_blocks)
        data["company"] = self._extract_company(combined_text, sorted_blocks)
        data["full_name"] = self._extract_name(sorted_blocks, image_size, combined_text, data)
        
        # Log extraction results
        found_fields = [k for k, v in data.items() if v]
        logger.info(f"📊 Extracted fields: {', '.join(found_fields)} ({len(found_fields)}/9)")
        
        return data
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email with improved pattern"""
        # More comprehensive email pattern
        pattern = r'\b[a-zA-Z0-9][\w\.-]*@[\w\.-]+\.[a-zA-Z]{2,}\b'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).lower() if match else None
    
    def _extract_phones(
        self,
        text: str,
        blocks: List
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract all phone numbers and classify them
        
        Returns: (main_phone, mobile, work)
        """
        # Enhanced phone patterns for Russian formats
        patterns = [
            # International format
            r'\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            r'\+7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            r'\+\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{2,4}',
            # Russian 8-format
            r'8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            # Short format with parentheses
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            # Just numbers
            r'\d{3}[\s\-]\d{3}[\s\-]\d{2}[\s\-]\d{2}',
        ]
        
        phones = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                phone = match.group(0).strip()
                # Normalize
                phone = re.sub(r'[\s\-\(\)]', '', phone)
                if phone not in phones and len(phone) >= 10:
                    phones.append(phone)
        
        if not phones:
            return (None, None, None)
        
        # Classify phones by context
        mobile = None
        work = None
        main = phones[0] if phones else None
        
        # Try to find mobile/work keywords near phone numbers
        for block in blocks:
            block_text = block.text.lower()
            if any(kw in block_text for kw in ['моб', 'mobile', 'cell', 'сот']):
                # Find phone in this block
                for phone in phones:
                    if phone in block.text.replace(' ', '').replace('-', ''):
                        mobile = phone
            elif any(kw in block_text for kw in ['раб', 'work', 'office', 'тел']):
                for phone in phones:
                    if phone in block.text.replace(' ', '').replace('-', ''):
                        work = phone
        
        # If we have multiple phones but no classification, assume first is mobile, second is work
        if len(phones) > 1 and not mobile and not work:
            mobile = phones[0]
            work = phones[1] if len(phones) > 1 else None
        
        return (main, mobile, work)
    
    def _extract_website(self, text: str) -> Optional[str]:
        """Extract website/URL with improved patterns"""
        patterns = [
            r'https?://[^\s]+',
            r'www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',
            r'[a-zA-Z0-9][a-zA-Z0-9\-]*\.(com|net|org|ru|рф|co\.uk|de|fr|io|ai|me)(?:/[^\s]*)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                website = match.group(0)
                # Clean up
                website = website.rstrip('.,;:)')
                # Add http:// if no protocol
                if not website.startswith(('http://', 'https://')):
                    website = 'http://' + website
                return website
        
        return None
    
    def _extract_address(self, text: str, blocks: List) -> Optional[str]:
        """Extract address using indicators and position"""
        # Find blocks with address indicators
        address_blocks = []
        
        for block in blocks:
            block_lower = block.text.lower()
            # Check if block contains address indicators
            has_indicator = any(
                re.search(indicator, block_lower, re.IGNORECASE)
                for indicator in self.address_indicators
            )
            
            if has_indicator:
                address_blocks.append(block.text)
        
        if address_blocks:
            # Combine nearby address blocks
            return ', '.join(address_blocks[:3])  # Max 3 lines
        
        # Fallback: look for postal code pattern
        postal_match = re.search(r'\b\d{6}\b', text)
        if postal_match:
            # Get surrounding context
            start = max(0, postal_match.start() - 50)
            end = min(len(text), postal_match.end() + 50)
            context = text[start:end].strip()
            return context
        
        return None
    
    def _extract_position(self, text: str, blocks: List) -> Optional[str]:
        """Extract position/title using keywords"""
        # Look for position keywords
        for block in blocks:
            block_lower = block.text.lower()
            
            # Check if block contains position keywords
            for keyword in self.position_keywords:
                if re.search(keyword, block_lower, re.IGNORECASE):
                    # This block likely contains position
                    return block.text.strip()
        
        return None
    
    def _extract_company(self, text: str, blocks: List) -> Optional[str]:
        """Extract company name using indicators"""
        # Look for company indicators
        for block in blocks:
            block_text = block.text
            
            # Check if block contains company indicators
            for indicator in self.company_indicators:
                if re.search(indicator, block_text, re.IGNORECASE):
                    # This block likely contains company name
                    return block_text.strip()
        
        # Fallback: look for block right after name (usually company)
        # This will be implemented when we know name position
        
        return None
    
    def _extract_name(
        self,
        blocks: List,
        image_size: Tuple[int, int],
        text: str,
        other_fields: Dict
    ) -> Optional[str]:
        """
        Extract full name using position and context
        
        Strategy:
        1. Name is usually at the top of card
        2. Name should not contain: email, phone, URL, position keywords
        3. Name is often the longest text in top area
        4. Name should have reasonable length (2-50 chars)
        """
        if not blocks:
            return None
        
        # Get blocks from top 35% of image
        top_blocks = [b for b in blocks if b.bbox.y < image_size[1] * 0.35]
        
        if not top_blocks:
            top_blocks = blocks[:3]  # Fallback: first 3 blocks
        
        # Filter out blocks that are clearly not names
        candidate_blocks = []
        for block in top_blocks:
            text = block.text.strip()
            text_lower = text.lower()
            
            # Skip if too short or too long
            if len(text) < 2 or len(text) > 50:
                continue
            
            # Skip if contains non-name patterns
            if any([
                '@' in text,
                'http' in text_lower,
                'www' in text_lower,
                '+' in text and len(text) > 5,  # Phone
                text.replace('-', '').replace(' ', '').isdigit(),  # Pure numbers
                any(ind in text for ind in ['ООО', 'ОАО', 'ЗАО', 'ИП']),  # Company
            ]):
                continue
            
            # Skip if matches other extracted fields
            if other_fields.get('position') and text in other_fields['position']:
                continue
            if other_fields.get('company') and text in other_fields['company']:
                continue
            
            # Skip if contains position keywords
            contains_position = any(
                re.search(kw, text_lower, re.IGNORECASE)
                for kw in ['директор', 'менеджер', 'manager', 'специалист']
            )
            if contains_position:
                continue
            
            candidate_blocks.append(block)
        
        if not candidate_blocks:
            return None
        
        # Sort by confidence and length, pick best candidate
        candidate_blocks.sort(key=lambda b: (b.confidence, len(b.text)), reverse=True)
        
        return candidate_blocks[0].text.strip()

