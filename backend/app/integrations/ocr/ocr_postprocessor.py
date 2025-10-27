"""
OCR Post-Processing and Error Correction
Fixes common OCR mistakes in phone numbers, emails, and URLs
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OCRPostProcessor:
    """
    Post-processor for fixing common OCR errors
    
    Common issues:
    1. Cyrillic model confuses Latin letters with Cyrillic
    2. Numbers confused with letters (0→O, 1→I, 5→S, etc.)
    3. Special characters misread (:→l, /→I, @→@, etc.)
    """
    
    def __init__(self):
        # Mapping: OCR mistake → correct character
        self.latin_to_cyrillic_fixes = {
            # Common Latin/Cyrillic confusions
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y',
            'х': 'x', 'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
            'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',
        }
        
        # Phone number confusions
        self.phone_fixes = {
            'о': '0', 'О': '0', 'o': '0', 'O': '0',  # O → 0
            'з': '3', 'З': '3',                       # З → 3
            'б': '6', 'Б': '6',                       # Б → 6
            'І': '1', 'l': '1', '|': '1', 'і': '1',  # I/l → 1
            'S': '5', 's': '5',                       # S → 5
            'B': '8', 'в': '8', 'В': '8',            # B/В → 8
            'g': '9', 'q': '9',                       # g/q → 9
            'Z': '2', 'z': '2',                       # Z → 2
            'h': '4',                                 # h → 4
            'T': '7', 't': '7',                       # T → 7
            # Cyrillic that looks like numbers
            'э': '3', 'Э': '3',
            'а': '0', 'А': '0',
            'ђ': '6',
        }
        
        # URL/Email fixes
        self.url_fixes = {
            'httpsI': 'https://',
            'httpsІ': 'https://',
            'httpsl': 'https://',
            'httpI': 'http://',
            'httpІ': 'http://',
            'httpl': 'http://',
            'wwwI': 'www.',
            'wwwl': 'www.',
        }
    
    def fix_phone_number(self, text: str) -> Optional[str]:
        """
        Fix common OCR errors in phone numbers (ENHANCED)
        
        Args:
            text: Raw OCR text that might be a phone number
        
        Returns:
            Fixed phone number or None if not a valid phone
        """
        if not text or len(text) < 7:  # Minimum phone length (lowered from 10)
            return None
        
        # Remove spaces and common separators
        cleaned = text.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
        
        # AGGRESSIVE: Apply character fixes to EVERYTHING
        fixed = ''
        for char in cleaned:
            if char in self.phone_fixes:
                fixed += self.phone_fixes[char]
            elif char.isdigit():
                fixed += char
            elif char == '+':
                fixed += char
            # IMPORTANT: Skip all other characters (letters, etc.)
        
        # ENHANCED: Additional cyrillic-specific fixes
        # Some cyrillic letters that look like numbers but not in main dict
        additional_fixes = {
            'Ь': '6', 'ь': '6',  # Soft sign → 6
            'Ъ': '6', 'ъ': '6',  # Hard sign → 6
            'У': '4', 'у': '4',  # У → 4
            'Г': '4', 'г': '4',  # Г → 4
            'Ч': '4', 'ч': '4',  # Ч → 4
            'Е': '3', 'е': '3',  # Е → 3 (already in main, but emphasizing)
        }
        
        # Second pass with additional fixes
        fixed2 = ''
        for char in fixed:
            if char in additional_fixes:
                fixed2 += additional_fixes[char]
            else:
                fixed2 += char
        fixed = fixed2
        
        # Validate result
        # Russian format: +7XXXXXXXXXX or 8XXXXXXXXXX
        if len(fixed) >= 10:
            # Check if starts with +7 or 8 or 7
            if re.match(r'^\+?7\d{10}$', fixed):
                return fixed
            elif re.match(r'^8\d{10}$', fixed):
                return fixed
            # International format
            elif re.match(r'^\+\d{10,15}$', fixed):
                return fixed
            # Just 10+ digits (add +7 prefix for Russian)
            elif re.match(r'^\d{10}$', fixed):
                return '+7' + fixed
            elif re.match(r'^\d{11}$', fixed) and fixed[0] in ['7', '8']:
                # 7XXXXXXXXXX or 8XXXXXXXXXX → +7XXXXXXXXXX
                if fixed[0] == '8':
                    return '+7' + fixed[1:]
                else:
                    return '+' + fixed
        
        # FALLBACK: Try to find digit sequence
        digits_only = re.findall(r'\d+', fixed)
        if digits_only:
            all_digits = ''.join(digits_only)
            if len(all_digits) >= 10:
                # Try to format as phone
                if len(all_digits) == 10:
                    return '+7' + all_digits
                elif len(all_digits) == 11 and all_digits[0] in ['7', '8']:
                    if all_digits[0] == '8':
                        return '+7' + all_digits[1:]
                    else:
                        return '+' + all_digits
        
        return None
    
    def fix_email(self, text: str) -> Optional[str]:
        """
        Fix common OCR errors in email addresses (ENHANCED)
        
        Args:
            text: Raw OCR text that might be an email
        
        Returns:
            Fixed email or None if not valid
        """
        if not text or len(text) < 5:
            return None
        
        # AGGRESSIVE: Fix common @ confusions (expanded list)
        text = text.replace('©', '@').replace('®', '@').replace('Ⓒ', '@')
        text = text.replace('а', 'a')  # Cyrillic 'a' → Latin 'a'
        
        # Check for @ or potential @ patterns
        # Cyrillic model might recognize @ as: а, о, с, е, ©, ®, etc.
        potential_at_chars = ['@', '©', '®', 'Ⓒ', 'а', 'о']
        has_at = any(c in text for c in potential_at_chars)
        
        # AGGRESSIVE: Even without @, check if looks like email pattern
        # Pattern: word.word or word@word.word
        if not has_at:
            # Try to find email-like pattern: somethingDotsomethingDotsomething
            if re.search(r'[a-zа-я]+[\.][a-zа-я]+[\.][a-zа-я]{2,}', text, re.IGNORECASE):
                # Likely email without @, insert @ before first dot or after first word
                parts = re.split(r'[\.]+', text, 1)
                if len(parts) >= 2:
                    text = parts[0] + '@' + parts[1]
        
        # Fix common @ confusions
        for at_char in potential_at_chars:
            if at_char in text and at_char != '@':
                # Replace FIRST occurrence with @
                text = text.replace(at_char, '@', 1)
        
        # Fix cyrillic → latin in email
        fixed = ''
        for char in text:
            if char in self.latin_to_cyrillic_fixes:
                fixed += self.latin_to_cyrillic_fixes[char]
            else:
                fixed += char
        
        # Convert to lowercase
        fixed = fixed.lower()
        
        # Remove spaces
        fixed = fixed.replace(' ', '')
        
        # Additional cleanup: remove multiple @
        if fixed.count('@') > 1:
            # Keep only first @
            parts = fixed.split('@')
            fixed = parts[0] + '@' + ''.join(parts[1:])
        
        # Validate basic email format
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', fixed):
            return fixed
        
        # FALLBACK: Try to salvage partial email
        # If has @ and ends with common domain
        if '@' in fixed:
            # Check if ends with domain-like pattern
            if re.search(r'@[a-zA-Z0-9.-]+\.(ru|com|net|org|io)$', fixed):
                return fixed
        
        return None
    
    def fix_url(self, text: str) -> Optional[str]:
        """
        Fix common OCR errors in URLs
        
        Args:
            text: Raw OCR text that might be a URL
        
        Returns:
            Fixed URL or None if not valid
        """
        if not text or len(text) < 4:
            return None
        
        # Apply URL fixes
        for mistake, correct in self.url_fixes.items():
            text = text.replace(mistake, correct)
        
        # Fix :// confusions
        text = re.sub(r'(https?)[Il:/]+', r'\1://', text)
        
        # Fix common domain confusions
        for char in self.latin_to_cyrillic_fixes:
            text = text.replace(char, self.latin_to_cyrillic_fixes[char])
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove spaces
        text = text.replace(' ', '')
        
        # Ensure protocol
        if not text.startswith(('http://', 'https://')):
            if text.startswith('www.'):
                text = 'http://' + text
            elif '.' in text:
                text = 'http://' + text
        
        # Basic validation
        if re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
            return text
        
        return None
    
    def post_process_blocks(self, blocks: List) -> List:
        """
        Post-process all OCR blocks to fix common errors (AGGRESSIVE MODE)
        
        Args:
            blocks: List of TextBlock objects
        
        Returns:
            List of TextBlock objects with corrected text
        """
        corrected_blocks = []
        corrections_made = 0
        
        for block in blocks:
            text = block.text
            original_text = text
            
            # AGGRESSIVE: Try to fix phone numbers for ANY block with numbers or similar chars
            # Look for: digits, +, 7, 8, or cyrillic letters that look like numbers
            phone_indicators = any(c in text for c in '0123456789+78ЗзЭэБбОоаА')
            if phone_indicators or len(text) >= 10:
                fixed_phone = self.fix_phone_number(text)
                if fixed_phone and fixed_phone != text:
                    block.text = fixed_phone
                    corrections_made += 1
                    logger.debug(f"📞 Fixed phone: '{original_text}' → '{fixed_phone}'")
                    corrected_blocks.append(block)
                    continue
            
            # AGGRESSIVE: Try to fix emails for blocks with @, dots, or email-like patterns
            # Look for: @, ©, ®, dots with letters around them
            email_indicators = any(c in text for c in '@©®аоАО')
            has_dot_pattern = '.' in text and len(text) >= 5
            if email_indicators or has_dot_pattern:
                fixed_email = self.fix_email(text)
                if fixed_email and fixed_email != text:
                    block.text = fixed_email
                    corrections_made += 1
                    logger.debug(f"📧 Fixed email: '{original_text}' → '{fixed_email}'")
                    corrected_blocks.append(block)
                    continue
            
            # AGGRESSIVE: Try to fix URLs
            url_keywords = ['http', 'www', '.ru', '.com', '.net', '.org', '.io', 'https']
            if any(keyword in text.lower() for keyword in url_keywords):
                fixed_url = self.fix_url(text)
                if fixed_url and fixed_url != text:
                    block.text = fixed_url
                    corrections_made += 1
                    logger.debug(f"🌐 Fixed URL: '{original_text}' → '{fixed_url}'")
            
            corrected_blocks.append(block)
        
        if corrections_made > 0:
            logger.info(f"✨ Post-processing: {corrections_made} corrections made")
        
        return corrected_blocks
    
    def validate_and_fix_extracted_data(self, data: Dict) -> Dict:
        """
        Validate and fix extracted fields
        
        Args:
            data: Dictionary with extracted fields
        
        Returns:
            Dictionary with validated/fixed fields
        """
        # Fix phone
        if data.get('phone'):
            fixed = self.fix_phone_number(data['phone'])
            if fixed and fixed != data['phone']:
                logger.info(f"📞 Fixed extracted phone: '{data['phone']}' → '{fixed}'")
                data['phone'] = fixed
        
        # Fix phone_mobile
        if data.get('phone_mobile'):
            fixed = self.fix_phone_number(data['phone_mobile'])
            if fixed:
                data['phone_mobile'] = fixed
        
        # Fix phone_work
        if data.get('phone_work'):
            fixed = self.fix_phone_number(data['phone_work'])
            if fixed:
                data['phone_work'] = fixed
        
        # Fix email
        if data.get('email'):
            fixed = self.fix_email(data['email'])
            if fixed and fixed != data['email']:
                logger.info(f"📧 Fixed extracted email: '{data['email']}' → '{fixed}'")
                data['email'] = fixed
        
        # Fix website
        if data.get('website'):
            fixed = self.fix_url(data['website'])
            if fixed and fixed != data['website']:
                logger.info(f"🌐 Fixed extracted URL: '{data['website']}' → '{fixed}'")
                data['website'] = fixed
        
        return data

