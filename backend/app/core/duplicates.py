"""
Utilities for duplicate detection and contact merging.
Enhanced with transliteration, phone normalization, and weighted scoring.
"""
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
import json
import re


# Transliteration maps (Cyrillic ↔ Latin)
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z',
    'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

LATIN_TO_CYRILLIC = {v: k for k, v in CYRILLIC_TO_LATIN.items() if v}


def transliterate_cyrillic_to_latin(text: str) -> str:
    """Convert Cyrillic text to Latin (Иванов → Ivanov)"""
    result = []
    for char in text.lower():
        result.append(CYRILLIC_TO_LATIN.get(char, char))
    return ''.join(result)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number for comparison.
    Removes all non-digits and normalizes prefix.
    Examples:
        +7 (999) 123-45-67 → 79991234567
        8 999 123 45 67 → 79991234567
        9991234567 → 79991234567
    """
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Normalize Russian numbers
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    elif digits.startswith('9') and len(digits) == 10:
        digits = '7' + digits
    
    return digits


def calculate_field_similarity(value1: Optional[str], value2: Optional[str], field_type: str = 'text') -> float:
    """
    Calculate similarity between two field values with enhanced matching.
    Returns score from 0.0 to 1.0.
    
    Args:
        value1: First value
        value2: Second value
        field_type: Type of field ('text', 'name', 'phone', 'email')
    """
    if not value1 or not value2:
        return 0.0
    
    # Normalize
    v1 = str(value1).strip().lower()
    v2 = str(value2).strip().lower()
    
    # Exact match
    if v1 == v2:
        return 1.0
    
    # Special handling for phones
    if field_type == 'phone':
        n1 = normalize_phone(v1)
        n2 = normalize_phone(v2)
        if n1 and n2:
            if n1 == n2:
                return 1.0
            # Partial match (last 7 digits)
            if len(n1) >= 7 and len(n2) >= 7 and n1[-7:] == n2[-7:]:
                return 0.85
            return fuzz.ratio(n1, n2) / 100.0
    
    # Special handling for names (with transliteration)
    if field_type == 'name':
        # Try direct comparison
        score_direct = fuzz.token_sort_ratio(v1, v2) / 100.0
        
        # Try transliterated comparison (Ivanov ↔ Иванов)
        v1_translit = transliterate_cyrillic_to_latin(v1)
        v2_translit = transliterate_cyrillic_to_latin(v2)
        score_translit = fuzz.token_sort_ratio(v1_translit, v2_translit) / 100.0
        
        # Return best score
        return max(score_direct, score_translit)
    
    # Default: fuzzy matching
    return fuzz.ratio(v1, v2) / 100.0


def calculate_contact_similarity(contact1: dict, contact2: dict, weights: Dict[str, float] = None) -> Tuple[float, Dict[str, float]]:
    """
    Calculate overall similarity between two contacts with enhanced matching.
    
    Args:
        contact1: First contact data
        contact2: Second contact data
        weights: Field weights for similarity calculation
    
    Returns:
        Tuple of (overall_score, field_scores)
    """
    if weights is None:
        # Updated weights: email and phone are more important
        weights = {
            'full_name': 0.20,
            'first_name': 0.12,
            'last_name': 0.13,
            'email': 0.30,  # Increased: email is unique
            'phone': 0.25,  # Increased: phone is unique
            'company': 0.08,
            'position': 0.04,
        }
    
    # Define field types for enhanced matching
    field_types = {
        'full_name': 'name',
        'first_name': 'name',
        'last_name': 'name',
        'middle_name': 'name',
        'email': 'email',
        'phone': 'phone',
        'phone_mobile': 'phone',
        'phone_work': 'phone',
        'company': 'text',
        'position': 'text',
    }
    
    field_scores = {}
    total_weight = 0.0
    weighted_sum = 0.0
    
    for field, weight in weights.items():
        val1 = contact1.get(field)
        val2 = contact2.get(field)
        
        # Skip if both values are empty
        if not val1 and not val2:
            continue
        
        # Get field type for enhanced matching
        field_type = field_types.get(field, 'text')
        score = calculate_field_similarity(val1, val2, field_type)
        field_scores[field] = round(score, 2)
        
        # Only include in total if at least one value exists
        if val1 or val2:
            total_weight += weight
            weighted_sum += score * weight
    
    # Check all phone fields (mobile, work, additional)
    phone_fields = ['phone', 'phone_mobile', 'phone_work', 'phone_additional']
    max_phone_score = 0.0
    for pf1 in phone_fields:
        for pf2 in phone_fields:
            p1 = contact1.get(pf1)
            p2 = contact2.get(pf2)
            if p1 and p2:
                score = calculate_field_similarity(p1, p2, 'phone')
                max_phone_score = max(max_phone_score, score)
    
    # If we found a better phone match across different fields, use it
    if max_phone_score > field_scores.get('phone', 0):
        field_scores['phone'] = round(max_phone_score, 2)
        if 'phone' in weights:
            weighted_sum += (max_phone_score - field_scores.get('phone', 0)) * weights['phone']
    
    # Calculate overall score
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    return round(overall_score, 4), field_scores


def find_duplicates_for_new_contact(new_contact: dict, existing_contacts: List[dict], threshold: float = 0.75) -> List[Tuple[dict, float, Dict[str, float]]]:
    """
    Find potential duplicates for a newly created contact.
    
    Args:
        new_contact: Newly created contact data
        existing_contacts: List of existing contact dictionaries
        threshold: Minimum similarity score to consider as duplicate
    
    Returns:
        List of tuples: (existing_contact, similarity_score, field_scores)
        Sorted by similarity score (highest first)
    """
    duplicates = []
    
    for existing in existing_contacts:
        # Skip self
        if existing.get('id') == new_contact.get('id'):
            continue
        
        overall_score, field_scores = calculate_contact_similarity(new_contact, existing)
        
        if overall_score >= threshold:
            duplicates.append((existing, overall_score, field_scores))
    
    # Sort by similarity score (highest first)
    duplicates.sort(key=lambda x: x[1], reverse=True)
    
    return duplicates


def find_duplicate_contacts(contacts: List[dict], threshold: float = 0.75) -> List[Tuple[dict, dict, float, Dict[str, float]]]:
    """
    Find potential duplicates in a list of contacts.
    
    Args:
        contacts: List of contact dictionaries
        threshold: Minimum similarity score to consider as duplicate
    
    Returns:
        List of tuples: (contact1, contact2, similarity_score, field_scores)
    """
    duplicates = []
    
    for i in range(len(contacts)):
        for j in range(i + 1, len(contacts)):
            contact1 = contacts[i]
            contact2 = contacts[j]
            
            overall_score, field_scores = calculate_contact_similarity(contact1, contact2)
            
            if overall_score >= threshold:
                duplicates.append((contact1, contact2, overall_score, field_scores))
    
    # Sort by similarity score (highest first)
    duplicates.sort(key=lambda x: x[2], reverse=True)
    
    return duplicates


def merge_contacts(primary: dict, secondary: dict, selected_fields: Dict[str, str]) -> dict:
    """
    Merge two contacts based on selected fields.
    
    Args:
        primary: Primary contact data (base)
        secondary: Secondary contact data (to merge from)
        selected_fields: Dict mapping field_name -> 'primary' or 'secondary'
                        Example: {'name': 'secondary', 'email': 'primary'}
    
    Returns:
        Merged contact data
    """
    merged = primary.copy()
    
    for field, source in selected_fields.items():
        if source == 'secondary' and field in secondary:
            merged[field] = secondary[field]
        elif source == 'primary' and field in primary:
            merged[field] = primary[field]
        # If source is 'keep_both' or 'combine', handle specially
        elif source == 'keep_both':
            primary_val = primary.get(field, '')
            secondary_val = secondary.get(field, '')
            if primary_val and secondary_val and primary_val != secondary_val:
                merged[field] = f"{primary_val}; {secondary_val}"
            else:
                merged[field] = primary_val or secondary_val
    
    return merged


def get_mergeable_fields() -> List[Dict[str, str]]:
    """
    Get list of fields that can be merged between contacts.
    
    Returns:
        List of field definitions with name, label, and type
    """
    return [
        {'name': 'full_name', 'label': 'Full Name', 'type': 'text'},
        {'name': 'first_name', 'label': 'First Name', 'type': 'text'},
        {'name': 'last_name', 'label': 'Last Name', 'type': 'text'},
        {'name': 'middle_name', 'label': 'Middle Name', 'type': 'text'},
        {'name': 'email', 'label': 'Email', 'type': 'email'},
        {'name': 'phone', 'label': 'Phone', 'type': 'phone'},
        {'name': 'phone_mobile', 'label': 'Mobile Phone', 'type': 'phone'},
        {'name': 'phone_work', 'label': 'Work Phone', 'type': 'phone'},
        {'name': 'company', 'label': 'Company', 'type': 'text'},
        {'name': 'position', 'label': 'Position', 'type': 'text'},
        {'name': 'department', 'label': 'Department', 'type': 'text'},
        {'name': 'address', 'label': 'Address', 'type': 'text'},
        {'name': 'address_additional', 'label': 'Additional Address', 'type': 'text'},
        {'name': 'website', 'label': 'Website', 'type': 'url'},
        {'name': 'birthday', 'label': 'Birthday', 'type': 'text'},
        {'name': 'comment', 'label': 'Comment', 'type': 'text'},
        {'name': 'source', 'label': 'Source', 'type': 'text'},
        {'name': 'status', 'label': 'Status', 'type': 'text'},
        {'name': 'priority', 'label': 'Priority', 'type': 'text'},
    ]
