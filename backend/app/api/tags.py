"""
Tags API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Contact, Tag
from .. import schemas
from ..core.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get('/', response_model=List[schemas.TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tags"""
    tags = db.query(Tag).all()
    return tags


@router.post('/', response_model=schemas.TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new tag"""
    # Check if tag already exists
    existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag_data.name}' already exists"
        )
    
    new_tag = Tag(
        name=tag_data.name,
        color=tag_data.color or "#3B82F6"
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


@router.put('/{tag_id}', response_model=schemas.TagResponse)
def update_tag(
    tag_id: int,
    tag_data: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a tag"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Check if new name conflicts with existing tag
    if tag_data.name != tag.name:
        existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag_data.name}' already exists"
            )
    
    tag.name = tag_data.name
    if tag_data.color:
        tag.color = tag_data.color
    
    db.commit()
    db.refresh(tag)
    return tag


@router.delete('/{tag_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a tag"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    db.delete(tag)
    db.commit()
    return None


@router.post('/{tag_id}/contacts/{contact_id}', response_model=schemas.ContactResponse)
def add_tag_to_contact(
    contact_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a tag to a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    if tag not in contact.tags:
        contact.tags.append(tag)
        db.commit()
        db.refresh(contact)
    
    return contact


@router.delete('/{tag_id}/contacts/{contact_id}', response_model=schemas.ContactResponse)
def remove_tag_from_contact(
    contact_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a tag from a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    if tag in contact.tags:
        contact.tags.remove(tag)
        db.commit()
        db.refresh(contact)
    
    return contact

