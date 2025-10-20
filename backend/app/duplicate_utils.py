"""
Duplicate detection and merging utilities for contacts.
"""
import logging
from typing import List, Dict, Tuple, Any
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number for comparison.
    Removes spaces, dashes, parentheses, country codes.
    """
    if not phone:
        return ''
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Remove leading country codes (1, 7, 8)
    if len(digits) >= 11 and digits[0] in ['1', '7', '8']:
        digits = digits[1:]
    
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_email(email: str) -> str:
    """
    Normalize email for comparison.
    Lowercase, strip whitespace.
    """
    if not email:
        return ''
    return email.lower().strip()


def normalize_name(name: str) -> str:
    """
    Normalize name for comparison.
    Lowercase, remove extra spaces, punctuation.
    """
    if not name:
        return ''
    
    # Lowercase and strip
    name = name.lower().strip()
    
    # Remove punctuation
    name = re.sub(r'[.,!?;:]', '', name)
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    return name


def string_similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity between two strings (0.0 to 1.0).
    Uses SequenceMatcher (Ratcliff/Obershelp algorithm).
    """
    if not s1 or not s2:
        return 0.0
    
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def calculate_duplicate_score(contact1: Dict[str, Any], contact2: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Calculate duplicate probability score between two contacts.
    Returns (score, reasons) where score is 0.0-1.0.
    
    Scoring rules:
    - Exact phone match: +0.5
    - Exact email match: +0.5
    - Similar name (>0.8): +0.3
    - Same company + similar position: +0.2
    - Similar full name (>0.9): +0.4
    """
    score = 0.0
    reasons = []
    
    # Phone comparison
    phone1 = normalize_phone(contact1.get('phone', ''))
    phone2 = normalize_phone(contact2.get('phone', ''))
    
    if phone1 and phone2 and phone1 == phone2:
        score += 0.5
        reasons.append('identical_phone')
    
    # Mobile phone comparison
    mobile1 = normalize_phone(contact1.get('phone_mobile', ''))
    mobile2 = normalize_phone(contact2.get('phone_mobile', ''))
    
    if mobile1 and mobile2 and mobile1 == mobile2:
        score += 0.5
        reasons.append('identical_mobile')
    
    # Email comparison
    email1 = normalize_email(contact1.get('email', ''))
    email2 = normalize_email(contact2.get('email', ''))
    
    if email1 and email2 and email1 == email2:
        score += 0.5
        reasons.append('identical_email')
    
    # Name comparison - try multiple fields
    name1_full = normalize_name(contact1.get('full_name', ''))
    name2_full = normalize_name(contact2.get('full_name', ''))
    
    name1_parts = f"{contact1.get('first_name', '')} {contact1.get('last_name', '')}".strip()
    name2_parts = f"{contact2.get('first_name', '')} {contact2.get('last_name', '')}".strip()
    name1_parts = normalize_name(name1_parts)
    name2_parts = normalize_name(name2_parts)
    
    # Use whichever name representation is available
    name1 = name1_full or name1_parts
    name2 = name2_full or name2_parts
    
    if name1 and name2:
        name_sim = string_similarity(name1, name2)
        
        if name_sim > 0.9:
            score += 0.4
            reasons.append(f'very_similar_name ({name_sim:.2f})')
        elif name_sim > 0.8:
            score += 0.3
            reasons.append(f'similar_name ({name_sim:.2f})')
        elif name_sim > 0.7:
            score += 0.15
            reasons.append(f'somewhat_similar_name ({name_sim:.2f})')
    
    # Company + Position comparison
    company1 = normalize_name(contact1.get('company', ''))
    company2 = normalize_name(contact2.get('company', ''))
    position1 = normalize_name(contact1.get('position', ''))
    position2 = normalize_name(contact2.get('position', ''))
    
    if company1 and company2 and company1 == company2:
        if position1 and position2:
            position_sim = string_similarity(position1, position2)
            if position_sim > 0.8:
                score += 0.2
                reasons.append('same_company_similar_position')
    
    return (score, reasons)


def find_duplicates(contacts: List[Dict[str, Any]], threshold: float = 0.6) -> List[Dict[str, Any]]:
    """
    Find potential duplicate contacts.
    
    Args:
        contacts: List of contact dicts
        threshold: Minimum similarity score (0.0-1.0) to consider duplicates
    
    Returns:
        List of duplicate groups with scores
    """
    duplicates = []
    processed = set()
    
    for i, contact1 in enumerate(contacts):
        if contact1['id'] in processed:
            continue
        
        group = []
        
        for j, contact2 in enumerate(contacts):
            if i >= j or contact2['id'] in processed:
                continue
            
            score, reasons = calculate_duplicate_score(contact1, contact2)
            
            if score >= threshold:
                if not group:
                    # Start new group with contact1
                    group.append({
                        'contact': contact1,
                        'score': 1.0,
                        'reasons': ['original']
                    })
                    processed.add(contact1['id'])
                
                # Add contact2 to group
                group.append({
                    'contact': contact2,
                    'score': score,
                    'reasons': reasons
                })
                processed.add(contact2['id'])
        
        if group:
            duplicates.append({
                'contacts': group,
                'group_id': f"dup_{contact1['id']}",
                'max_score': max([c['score'] for c in group])
            })
    
    # Sort by max score (most likely duplicates first)
    duplicates.sort(key=lambda x: x['max_score'], reverse=True)
    
    logger.info(f"Found {len(duplicates)} potential duplicate groups (threshold={threshold})")
    
    return duplicates


def merge_contacts(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two contacts, preferring non-empty fields from primary.
    If primary field is empty, use secondary field.
    
    Args:
        primary: Primary contact (will be kept)
        secondary: Secondary contact (will be merged into primary)
    
    Returns:
        Merged contact data (updates for primary)
    """
    merged = {}
    
    # Fields to merge
    fields = [
        'full_name', 'first_name', 'last_name', 'middle_name',
        'company', 'position', 'department',
        'email', 'phone', 'phone_mobile', 'phone_work', 'fax',
        'address', 'website',
        'birthday', 'source', 'status', 'priority',
        'comment'
    ]
    
    for field in fields:
        primary_value = primary.get(field)
        secondary_value = secondary.get(field)
        
        # If primary is empty, use secondary
        if not primary_value and secondary_value:
            merged[field] = secondary_value
        # If both have values and they're different, append to comment
        elif primary_value and secondary_value and primary_value != secondary_value:
            if field == 'comment':
                # Merge comments
                merged['comment'] = f"{primary_value}\n---\n{secondary_value}"
            elif field not in ['status', 'priority', 'source']:
                # Add note about conflicting data
                existing_comment = merged.get('comment', primary.get('comment', ''))
                note = f"\n[Merged from duplicate: {field}='{secondary_value}']"
                merged['comment'] = (existing_comment or '') + note
    
    # Merge tags (if present in dicts)
    primary_tags = set(t['id'] if isinstance(t, dict) else t for t in primary.get('tags', []))
    secondary_tags = set(t['id'] if isinstance(t, dict) else t for t in secondary.get('tags', []))
    all_tags = primary_tags | secondary_tags
    if all_tags:
        merged['tag_ids'] = list(all_tags)
    
    # Merge groups (if present in dicts)
    primary_groups = set(g['id'] if isinstance(g, dict) else g for g in primary.get('groups', []))
    secondary_groups = set(g['id'] if isinstance(g, dict) else g for g in secondary.get('groups', []))
    all_groups = primary_groups | secondary_groups
    if all_groups:
        merged['group_ids'] = list(all_groups)
    
    logger.info(f"Merged contact {secondary.get('id')} into {primary.get('id')}: {list(merged.keys())}")
    
    return merged

