"""
Groups API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Contact, Group
from .. import schemas
from ..core.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get('/', response_model=List[schemas.GroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all groups"""
    groups = db.query(Group).all()
    return groups


@router.post('/', response_model=schemas.GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new group"""
    # Check if group already exists
    existing = db.query(Group).filter(Group.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group '{group_data.name}' already exists"
        )
    
    new_group = Group(
        name=group_data.name,
        description=group_data.description
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.put('/{group_id}', response_model=schemas.GroupResponse)
def update_group(
    group_id: int,
    group_data: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if new name conflicts with existing group
    if group_data.name != group.name:
        existing = db.query(Group).filter(Group.name == group_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Group '{group_data.name}' already exists"
            )
    
    group.name = group_data.name
    group.description = group_data.description
    
    db.commit()
    db.refresh(group)
    return group


@router.delete('/{group_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    db.delete(group)
    db.commit()
    return None


@router.post('/{group_id}/contacts/{contact_id}', response_model=schemas.ContactResponse)
def add_group_to_contact(
    contact_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a contact to a group"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group not in contact.groups:
        contact.groups.append(group)
        db.commit()
        db.refresh(contact)
    
    return contact


@router.delete('/{group_id}/contacts/{contact_id}', response_model=schemas.ContactResponse)
def remove_group_from_contact(
    contact_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a contact from a group"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group in contact.groups:
        contact.groups.remove(group)
        db.commit()
        db.refresh(contact)
    
    return contact

