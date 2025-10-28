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
        # Position keywords (Russian + English) - EXPANDED
        self.position_keywords = [
            # Generic titles (Russian)
            r'директор', r'генеральный', r'исполнительный', r'коммерческий',
            r'технический', r'финансовый', r'операционный', r'исполняющий',
            # Specific roles (Russian)
            r'менеджер', r'специалист', r'консультант', r'координатор',
            r'руководитель', r'начальник', r'заведующий', r'управляющий',
            r'главный', r'ведущий', r'старший', r'младший', r'помощник',
            r'ассистент', r'советник', r'представитель', r'агент',
            # Departments (Russian)
            r'отдел', r'департамент', r'служба', r'управление', r'сектор',
            # Professions (Russian)
            r'инженер', r'архитектор', r'дизайнер', r'разработчик',
            r'программист', r'аналитик', r'бухгалтер', r'юрист',
            r'экономист', r'маркетолог', r'логист', r'врач', r'психолог',
            r'преподаватель', r'учитель', r'тренер', r'коуч', r'эксперт',
            r'администратор', r'секретарь', r'ресепшионист', r'оператор',
            # Sales/Marketing (Russian)
            r'продажи', r'продаж', r'маркетинг', r'рекламы', r'pr',
            # English titles
            r'director', r'manager', r'ceo', r'cto', r'cfo', r'coo', r'cmo',
            r'president', r'vice', r'head', r'chief', r'lead', r'senior',
            r'founder', r'owner', r'partner', r'consultant', r'advisor',
            r'executive', r'officer', r'administrator', r'coordinator',
            r'specialist', r'expert', r'analyst', r'developer', r'engineer',
            # Standalone titles (will match exactly)
            r'^ceo$', r'^cto$', r'^cfo$', r'^coo$', r'^cmo$',
            r'^директор$', r'^менеджер$', r'^специалист$',
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
        """Extract email with AGGRESSIVE pattern matching"""
        # Pattern 1: Standard email
        pattern = r'\b[a-zA-Z0-9][\w\.-]*@[\w\.-]+\.[a-zA-Z]{2,}\b'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).lower()
        
        # Pattern 2: Email without @ (try to reconstruct)
        # Example: "info mail.ru" → "info@mail.ru"
        pattern_no_at = r'\b([a-z0-9]+)[\s\._]+((?:[a-z0-9-]+\.)+[a-z]{2,})\b'
        match = re.search(pattern_no_at, text, re.IGNORECASE)
        if match:
            username, domain = match.groups()
            reconstructed = f"{username}@{domain}"
            logger.debug(f"📧 Reconstructed email: {text} → {reconstructed}")
            return reconstructed.lower()
        
        # Pattern 3: Look for domain indicators and try to find nearby username
        if any(domain in text.lower() for domain in ['.ru', '.com', '.org', '.net', 'mail', 'gmail', 'yandex']):
            # Try to extract domain
            domain_match = re.search(r'([a-z0-9-]+\.(?:ru|com|org|net|io))', text, re.IGNORECASE)
            if domain_match:
                domain = domain_match.group(1)
                # Look for username nearby (before domain)
                username_match = re.search(r'([a-z0-9_]+)\s*' + re.escape(domain), text, re.IGNORECASE)
                if username_match:
                    username = username_match.group(1)
                    reconstructed = f"{username}@{domain}"
                    logger.debug(f"📧 Reconstructed email (domain-based): {reconstructed}")
                    return reconstructed.lower()
        
        return None
    
    def _extract_phones(
        self,
        text: str,
        blocks: List
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract and normalize phone numbers (AGGRESSIVE mode)
        
        Returns: (main_phone, mobile, work)
        """
        # AGGRESSIVE phone patterns - find EVERYTHING that looks like a phone
        patterns = [
            # International formats
            r'\+7[\s\-\.\(\)]?\d{3}[\s\-\.\)\(]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
            r'\+\d{1,3}[\s\-\.\(\)]?\d{2,4}[\s\-\.\)\(]?\d{3,4}[\s\-\.]?\d{2,4}',
            # Russian 8-format
            r'8[\s\-\.\(\)]?\d{3}[\s\-\.\)\(]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
            # 7-start (without +)
            r'7[\s\-\.\(\)]?\d{3}[\s\-\.\)\(]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
            # With parentheses
            r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}',
            # Compact format
            r'\d{10,11}',  # 10 or 11 digits in a row
        ]
        
        phones = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                phone = match.group(0).strip()
                # Normalize: remove all non-digits except leading +
                normalized = phone[0] if phone.startswith('+') else ''
                normalized += ''.join(c for c in phone if c.isdigit())
                
                # Validate length
                if len(normalized.replace('+', '')) < 10:
                    continue
                
                # Normalize Russian numbers
                if normalized.startswith('8') and len(normalized) == 11:
                    normalized = '+7' + normalized[1:]  # 8XXX → +7XXX
                elif normalized.startswith('7') and len(normalized) == 11:
                    normalized = '+' + normalized  # 7XXX → +7XXX
                elif len(normalized) == 10:
                    normalized = '+7' + normalized  # XXX → +7XXX
                
                # Deduplicate
                if normalized not in phones:
                    phones.append(normalized)
                    logger.debug(f"📞 Found phone: {phone} → {normalized}")
        
        if not phones:
            return (None, None, None)
        
        # Classify by context (check each block)
        mobile = None
        work = None
        main = phones[0] if phones else None
        
        for block in blocks:
            block_text = block.text.lower()
            block_normalized = ''.join(c for c in block.text if c.isdigit())
            
            # Check if this block contains a phone
            for phone in phones:
                phone_digits = phone.replace('+', '')
                if phone_digits in block_normalized or block_normalized in phone_digits:
                    # Found phone in this block, check context
                    if any(kw in block_text for kw in ['моб', 'mobile', 'cell', 'сот', 'мобильный']):
                        mobile = phone
                        logger.debug(f"📱 Mobile: {phone}")
                    elif any(kw in block_text for kw in ['раб', 'work', 'office', 'тел', 'рабочий']):
                        work = phone
                        logger.debug(f"💼 Work: {phone}")
        
        # Fallback: if multiple phones but no classification
        if len(phones) > 1:
            if not mobile:
                mobile = phones[0]
            if not work and len(phones) > 1:
                work = phones[1]
        
        # Ensure main is set
        if not main and phones:
            main = phones[0]
        
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
        """
        Extract position/title using keywords and heuristics
        
        Strategy:
        1. First, try keyword-based search in ALL blocks
        2. Then, try positional heuristic (top 40% of image, after name)
        3. Filter out non-position blocks (email, phone, company, etc.)
        """
        # Strategy 1: Keyword-based search (most reliable)
        for block in blocks:
            block_text = block.text.strip()
            block_lower = block_text.lower()
            
            # Skip empty or very short blocks
            if len(block_text) < 3:
                continue
            
            # Check if block contains position keywords
            for keyword in self.position_keywords:
                if re.search(keyword, block_lower, re.IGNORECASE):
                    # Found position keyword!
                    logger.debug(f"💼 Position found by keyword '{keyword}': {block_text}")
                    return block_text
        
        # Strategy 2: Positional heuristic (for positions without keywords like "CEO", "Директор")
        # Position is usually in top 40% of card, after name, before company
        top_blocks = [b for b in blocks if hasattr(b, 'bbox') and b.bbox.y < blocks[0].bbox.y + (blocks[-1].bbox.y - blocks[0].bbox.y) * 0.4]
        
        for block in top_blocks:
            block_text = block.text.strip()
            block_lower = block_text.lower()
            
            # Skip if too short or too long
            if len(block_text) < 3 or len(block_text) > 60:
                continue
            
            # Skip if contains non-position patterns
            if any([
                '@' in block_text,  # Email
                'http' in block_lower,  # URL
                'www' in block_lower,  # URL
                '+' in block_text and len(block_text) > 8,  # Phone
                re.search(r'\d{3,}', block_text),  # Long numbers (phone, address)
                any(ind in block_text for ind in ['ООО', 'ОАО', 'ЗАО', 'ИП', 'LLC', 'Inc']),  # Company
            ]):
                continue
            
            # Check if looks like a position (short, capitalized, professional)
            # Common patterns: "Директор", "CEO", "Менеджер по продажам"
            words = block_text.split()
            if 1 <= len(words) <= 5:  # Position is usually 1-5 words
                # Additional checks: starts with capital, no excessive punctuation
                if block_text[0].isupper() and block_text.count('.') < 2:
                    logger.debug(f"💼 Position found by heuristic (top area): {block_text}")
                    return block_text
        
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
        
        name = candidate_blocks[0].text.strip()
        
        # Normalize name order (fix "Last First" → "First Last" if needed)
        name = self._normalize_name_order(name)
        
        return name
    
    def _normalize_name_order(self, name: str) -> str:
        """
        Normalize name order to "First Last" format
        
        Russian names can be in different orders:
        - "Иван Иванов" (First Last) ✓
        - "Иванов Иван" (Last First) → needs fixing
        - "Иванов Иван Петрович" (Last First Middle) → needs fixing
        
        Strategy:
        1. If name has 2+ words and ALL CAPS → likely "LAST FIRST" format
        2. If first word ends with common last name suffixes (-ов, -ев, -ин, -ский, -ая)
           and second word doesn't → likely "Last First", swap them
        3. Otherwise keep as is
        """
        if not name or ' ' not in name:
            return name
        
        words = name.split()
        if len(words) < 2:
            return name
        
        # Check if all caps (common for "LAST FIRST" format)
        if name.isupper():
            # ALL CAPS format, likely "LAST FIRST"
            # Swap to "FIRST LAST"
            logger.debug(f"👤 Name in ALL CAPS, swapping: '{name}' → '{words[1]} {words[0]}'")
            return f"{words[1]} {words[0]}"
        
        first_word = words[0]
        second_word = words[1] if len(words) > 1 else ""
        
        # Russian last name suffixes
        last_name_suffixes = [
            'ов', 'ова', 'ев', 'ева', 'ин', 'ина',
            'ский', 'ская', 'цкий', 'цкая', 'ной', 'ная',
            'ых', 'их', 'ко', 'юк', 'ук', 'як', 'ак'
        ]
        
        # Check if first word looks like a last name
        first_is_lastname = any(
            first_word.lower().endswith(suffix)
            for suffix in last_name_suffixes
        )
        
        # Check if second word looks like a last name
        second_is_lastname = any(
            second_word.lower().endswith(suffix)
            for suffix in last_name_suffixes
        ) if second_word else False
        
        # If first is last name and second is NOT last name, swap them
        if first_is_lastname and not second_is_lastname:
            # Swap "Last First" → "First Last"
            if len(words) == 2:
                swapped = f"{words[1]} {words[0]}"
                logger.debug(f"👤 Name order fixed: '{name}' → '{swapped}'")
                return swapped
            elif len(words) == 3:
                # "Last First Middle" → "First Middle Last"
                swapped = f"{words[1]} {words[2]} {words[0]}"
                logger.debug(f"👤 Name order fixed (3 words): '{name}' → '{swapped}'")
                return swapped
        
        # Otherwise, keep original order
        return name

