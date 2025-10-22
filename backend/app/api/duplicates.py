"""
Duplicate Detection API endpoints
Migrated to use DuplicateService (Repository Pattern)
"""
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
import logging

from ..database import get_db
from ..models import Contact, User, DuplicateContact
from ..services import DuplicateService
from .. import duplicate_utils
from .. import auth_utils
from ..core.utils import create_audit_log

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


@router.get('')
def get_duplicates(
    status: str = None,
    threshold: float = 0.6,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Find and return duplicate contacts grouped by similarity.
    
    This endpoint performs real-time duplicate detection and groups
    similar contacts together for review.
    
    Args:
        status: Optional filter by status (pending, reviewed, merged, ignored)
        threshold: Minimum similarity score (0.0-1.0, default 0.6)
        limit: Maximum number of contacts to check (default 50)
    """
    try:
        # Use ContactRepository for DB access
        from ..repositories import ContactRepository
        contact_repo = ContactRepository(db)
        contacts = contact_repo.find_all(limit=limit)
        
        if len(contacts) < 2:
            return {
                'duplicates': [],
                'total_groups': 0,
                'total_contacts': len(contacts),
                'threshold': threshold
            }
        
        # Convert to dicts for comparison
        contact_dicts = []
        for c in contacts:
            contact_dicts.append({
                'id': c.id,
                'full_name': c.full_name,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'middle_name': c.middle_name,
                'email': c.email,
                'phone': c.phone,
                'phone_mobile': c.phone_mobile,
                'phone_work': c.phone_work,
                'phone_additional': c.phone_additional,
                'company': c.company,
                'position': c.position,
                'address': c.address,
                'website': c.website,
                'comment': c.comment
            })
        
        # Find duplicates using utility function
        duplicates = duplicate_utils.find_duplicate_contacts(contact_dicts, threshold)
        
        # Group duplicates by contact clusters
        # Each group represents a set of similar contacts
        groups = {}
        group_counter = 0
        
        for contact1, contact2, score, field_scores in duplicates:
            # Find if either contact is already in a group
            found_group = None
            for group_id, group_data in groups.items():
                if contact1['id'] in [c['contact']['id'] for c in group_data['contacts']]:
                    found_group = group_id
                    break
                if contact2['id'] in [c['contact']['id'] for c in group_data['contacts']]:
                    found_group = group_id
                    break
            
            # Determine reasons for match
            reasons = []
            for field, field_score in field_scores.items():
                if field_score > 0.8:
                    if field == 'phone':
                        reasons.append('identical_phone')
                    elif field == 'phone_mobile':
                        reasons.append('identical_mobile')
                    elif field == 'email':
                        reasons.append('identical_email')
                    elif field in ['first_name', 'last_name', 'full_name']:
                        reasons.append('similar_name')
                    elif field == 'company':
                        reasons.append('same_company')
            
            # If found a group, add the new contact to it
            if found_group is not None:
                # Check if contact1 is already in the group
                if contact1['id'] not in [c['contact']['id'] for c in groups[found_group]['contacts']]:
                    groups[found_group]['contacts'].append({
                        'contact': contact1,
                        'score': score,
                        'reasons': reasons
                    })
                    groups[found_group]['max_score'] = max(groups[found_group]['max_score'], score)
                
                # Check if contact2 is already in the group
                if contact2['id'] not in [c['contact']['id'] for c in groups[found_group]['contacts']]:
                    groups[found_group]['contacts'].append({
                        'contact': contact2,
                        'score': score,
                        'reasons': reasons
                    })
                    groups[found_group]['max_score'] = max(groups[found_group]['max_score'], score)
            else:
                # Create new group
                group_counter += 1
                groups[group_counter] = {
                    'group_id': group_counter,
                    'contacts': [
                        {
                            'contact': contact1,
                            'score': score,
                            'reasons': reasons
                        },
                        {
                            'contact': contact2,
                            'score': score,
                            'reasons': reasons
                        }
                    ],
                    'max_score': score
                }
        
        # Convert groups dict to list
        result_groups = list(groups.values())
        
        return {
            'duplicates': result_groups,
            'total_groups': len(result_groups),
            'total_contacts': len(contacts),
            'threshold': threshold
        }
    
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find duplicates: {str(e)}"
        )


@router.post('/find')
def find_duplicates_manual(
    threshold: float = 0.75,
    contact_ids: List[int] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Manually trigger duplicate detection.
    If contact_ids provided, check only those contacts.
    Otherwise, check all contacts.
    Uses ContactRepository and DuplicateRepository
    """
    # Use repositories
    from ..repositories import ContactRepository, DuplicateRepository
    contact_repo = ContactRepository(db)
    duplicate_repo = DuplicateRepository(db)
    
    # Get contacts to check
    if contact_ids:
        contacts = [contact_repo.get_by_id(cid) for cid in contact_ids]
        contacts = [c for c in contacts if c is not None]
    else:
        contacts = contact_repo.get_all()
    
    if len(contacts) < 2:
        return {'message': 'Need at least 2 contacts to find duplicates', 'found': 0}
    
    # Convert to dicts for comparison
    contact_dicts = []
    for c in contacts:
        contact_dicts.append({
            'id': c.id,
            'full_name': c.full_name,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'phone': c.phone,
            'company': c.company,
            'position': c.position,
        })
    
    # Find duplicates using utility
    duplicates = duplicate_utils.find_duplicate_contacts(contact_dicts, threshold)
    
    # Save to database using repository
    saved_count = 0
    for contact1, contact2, score, field_scores in duplicates:
        contact_id_1 = min(contact1['id'], contact2['id'])
        contact_id_2 = max(contact1['id'], contact2['id'])
        
        # Check if already exists
        existing = duplicate_repo.get_by_contact_pair(contact_id_1, contact_id_2)
        
        if not existing:
            duplicate_data = {
                'contact_id_1': contact_id_1,
                'contact_id_2': contact_id_2,
                'similarity_score': score,
                'match_fields': field_scores,
                'status': 'pending',
                'auto_detected': False
            }
            duplicate_repo.create_duplicate(duplicate_data)
            saved_count += 1
    
    duplicate_repo.commit()
    
    return {
        'message': f'Found {len(duplicates)} potential duplicates',
        'found': len(duplicates),
        'saved': saved_count,
        'threshold': threshold
    }


@router.put('/{duplicate_id}/status')
def update_duplicate_status(
    duplicate_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Update duplicate status: pending, reviewed, ignored
    Uses DuplicateService for business logic
    """
    if status not in ["pending", "reviewed", "ignored"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Use DuplicateService
    service = DuplicateService(db)
    updated = service.update_duplicate_status(duplicate_id, status, current_user.id)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Duplicate not found")

    return {"message": "Status updated", "duplicate_id": duplicate_id, "status": status}


@router.post('/{duplicate_id}/ignore')
def ignore_duplicate(
    duplicate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Mark a duplicate as ignored (convenience endpoint for marking false positives).
    Uses DuplicateService
    """
    # Use DuplicateService
    service = DuplicateService(db)
    updated = service.mark_as_ignored(duplicate_id, current_user.id)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Duplicate not found")

    return {"message": "Duplicate marked as ignored", "duplicate_id": duplicate_id}


@router.post('/merge')
def merge_contacts_simple(
    primary_id: int = Body(...),
    secondary_id: int = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Merge two contacts (simple version).
    The secondary contact's data is merged into the primary contact,
    and the secondary contact is deleted.
    Uses DuplicateService for business logic
    """
    # Use DuplicateService
    service = DuplicateService(db)
    merged_contact = service.merge_contacts(primary_id, [secondary_id], current_user.id)
    
    if not merged_contact:
        raise HTTPException(status_code=404, detail='One or both contacts not found')
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=primary_id,
        user=current_user,
        action='merged',
        entity_type='contact',
        changes={'merged_from': secondary_id}
    )
    
    return {
        'message': 'Contacts merged successfully',
        'merged_contact_id': primary_id,
        'deleted_contact_id': secondary_id
    }


@router.post('/merge/{contact_id_1}/{contact_id_2}')
def merge_contacts_endpoint(
    contact_id_1: int,
    contact_id_2: int,
    selected_fields: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Merge two contacts (advanced version with field selection).
    selected_fields: dict mapping field_name -> 'primary' or 'secondary'
    Example: {'email': 'primary', 'phone': 'secondary', 'company': 'keep_both'}
    Uses ContactRepository and DuplicateRepository
    """
    # Use repositories
    from ..repositories import ContactRepository, DuplicateRepository
    contact_repo = ContactRepository(db)
    duplicate_repo = DuplicateRepository(db)
    
    # Get contacts using repository
    contact1 = contact_repo.get_by_id(contact_id_1)
    contact2 = contact_repo.get_by_id(contact_id_2)
    
    if not contact1 or not contact2:
        raise HTTPException(status_code=404, detail='One or both contacts not found')
    
    # Convert to dicts
    c1_dict = {
        'full_name': contact1.full_name,
        'first_name': contact1.first_name,
        'last_name': contact1.last_name,
        'middle_name': contact1.middle_name,
        'email': contact1.email,
        'phone': contact1.phone,
        'phone_mobile': contact1.phone_mobile,
        'phone_work': contact1.phone_work,
        'company': contact1.company,
        'position': contact1.position,
        'department': contact1.department,
        'address': contact1.address,
        'address_additional': contact1.address_additional,
        'website': contact1.website,
        'birthday': contact1.birthday,
        'comment': contact1.comment,
        'source': contact1.source,
        'status': contact1.status,
        'priority': contact1.priority,
    }
    
    c2_dict = {
        'full_name': contact2.full_name,
        'first_name': contact2.first_name,
        'last_name': contact2.last_name,
        'middle_name': contact2.middle_name,
        'email': contact2.email,
        'phone': contact2.phone,
        'phone_mobile': contact2.phone_mobile,
        'phone_work': contact2.phone_work,
        'company': contact2.company,
        'position': contact2.position,
        'department': contact2.department,
        'address': contact2.address,
        'address_additional': contact2.address_additional,
        'website': contact2.website,
        'birthday': contact2.birthday,
        'comment': contact2.comment,
        'source': contact2.source,
        'status': contact2.status,
        'priority': contact2.priority,
    }
    
    # Merge
    merged = duplicate_utils.merge_contacts(c1_dict, c2_dict, selected_fields)
    
    # Update primary contact
    for field, value in merged.items():
        if hasattr(contact1, field):
            setattr(contact1, field, value)
    
    # Update duplicate record using repository
    contact_id_min = min(contact_id_1, contact_id_2)
    contact_id_max = max(contact_id_1, contact_id_2)
    dup = duplicate_repo.get_by_contact_pair(contact_id_min, contact_id_max)
    
    if dup:
        update_data = {
            'status': 'merged',
            'reviewed_by': current_user.id,
            'merged_into': contact_id_1
        }
        duplicate_repo.update(dup, update_data)
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact_id_1,
        user=current_user,
        action='merged',
        entity_type='contact',
        changes={'merged_from': contact_id_2, 'selected_fields': selected_fields}
    )
    
    # Delete secondary contact using repository
    contact_repo.delete(contact2)
    
    # Commit both repositories
    contact_repo.commit()
    duplicate_repo.commit()
    
    # Refresh contact1
    db.refresh(contact1)
    
    return {
        'message': 'Contacts merged successfully',
        'merged_contact_id': contact_id_1,
        'deleted_contact_id': contact_id_2
    }

