"""
Utilities for duplicate detection and contact merging.
"""
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
import json


def calculate_field_similarity(value1: Optional[str], value2: Optional[str]) -> float:
    """
    Calculate similarity between two field values.
    Returns score from 0.0 to 1.0.
    """
    if not value1 or not value2:
        return 0.0
    
    # Normalize
    v1 = str(value1).strip().lower()
    v2 = str(value2).strip().lower()
    
    if v1 == v2:
        return 1.0
    
    # Use fuzzy matching
    return fuzz.ratio(v1, v2) / 100.0


def calculate_contact_similarity(contact1: dict, contact2: dict, weights: Dict[str, float] = None) -> Tuple[float, Dict[str, float]]:
    """
    Calculate overall similarity between two contacts.
    
    Args:
        contact1: First contact data
        contact2: Second contact data
        weights: Field weights for similarity calculation
    
    Returns:
        Tuple of (overall_score, field_scores)
    """
    if weights is None:
        weights = {
            'full_name': 0.3,
            'first_name': 0.15,
            'last_name': 0.15,
            'email': 0.25,
            'phone': 0.20,
            'company': 0.10,
            'position': 0.05,
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
        
        score = calculate_field_similarity(val1, val2)
        field_scores[field] = score
        
        # Only include in total if at least one value exists
        if val1 or val2:
            total_weight += weight
            weighted_sum += score * weight
    
    # Calculate overall score
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    return overall_score, field_scores


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
