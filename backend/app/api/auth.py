"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import logging

from ..database import get_db
from ..models import User
from .. import schemas
from .. import auth_utils
from slowapi import Limiter
from slowapi.util import get_remote_address

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics
from ..core.metrics import (
    auth_attempts_counter,
    users_total,
    user_logins_counter,
    user_registrations_counter,
    record_auth_attempt
)

def get_metric(name):
    """Helper to get existing metrics from registry"""
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    return None

# We'll use direct counter calls instead of storing references
# to avoid duplication errors


@router.post('/register', response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")  # 10 registrations per hour per IP
async def register(request: Request, user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (alphanumeric, 3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    """
    try:
        # Create user (auth_utils will check for duplicates)
        user = auth_utils.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_admin=False  # Regular users can't self-promote to admin
        )
        logger.info(f"New user registered: {user.username}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post('/login', response_model=schemas.Token)
@limiter.limit("30/minute")  # 30 login attempts per minute per IP
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    Returns JWT access token.
    
    - **username**: Username or email
    - **password**: User password
    """
    user = auth_utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        auth_attempts_counter.labels(status='failed').inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        auth_attempts_counter.labels(status='pending_approval').inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting administrator approval. Please contact the system administrator."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Update auth metrics
    auth_attempts_counter.labels(status='success').inc()
    user_logins_counter.inc()
    users_total.set(db.query(User).count())
    
    logger.info(f"User logged in: {user.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get('/me', response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get current authenticated user information.
    Requires valid JWT token.
    """
    return current_user


@router.put('/me', response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: User = Depends(auth_utils.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    Requires valid JWT token.
    
    - **email**: New email (optional)
    - **full_name**: New full name (optional)
    - **password**: New password (optional)
    """
    # Update fields
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing = auth_utils.get_user_by_email(db, user_update.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.hashed_password = auth_utils.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User updated profile: {current_user.username}")
    
    return current_user


@router.get('/users', response_model=List[schemas.UserResponse])
async def list_users(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    Requires valid JWT token with admin privileges.
    """
    users = db.query(User).all()
    return users


@router.get('/users/{user_id}', response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID (admin only).
    Requires valid JWT token with admin privileges.
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted by admin {current_user.username}: {user.username}")
    
    return None


@router.patch('/users/{user_id}/admin', response_model=schemas.UserResponse)
async def toggle_admin(
    user_id: int,
    is_admin: bool = Body(..., embed=True),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status for a user (admin only).
    Requires valid JWT token with admin privileges.
    Cannot change your own admin status.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    
    logger.info(f"Admin status changed by {current_user.username}: {user.username} -> {is_admin}")
    
    return user


@router.post('/users/{user_id}/reset-password')
async def reset_user_password(
    user_id: int,
    new_password: str = Body(..., embed=True, min_length=6),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset user password (admin only).
    Sets a new password for the specified user.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the new password
    user.hashed_password = auth_utils.get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password reset by admin {current_user.username} for user: {user.username}")
    
    return {
        "success": True,
        "message": f"Password reset successful for user: {user.username}"
    }


@router.patch('/users/{user_id}/activate', response_model=schemas.UserResponse)
async def activate_user(
    user_id: int,
    is_active: bool = Body(..., embed=True),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a user (admin only).
    Used to approve new user registrations.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    
    action = "activated" if is_active else "deactivated"
    logger.info(f"User {action} by admin {current_user.username}: {user.username}")
    
    return user


@router.put('/users/{user_id}/profile', response_model=schemas.UserResponse)
async def update_user_profile(
    user_id: int,
    update_data: schemas.UserUpdate,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile (admin only).
    Allows updating email, full_name, and password.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_data.email is not None:
        # Check if email already exists for another user
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another user"
            )
        user.email = update_data.email
    
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    
    if update_data.password is not None:
        user.hashed_password = auth_utils.get_password_hash(update_data.password)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User profile updated by admin {current_user.username}: {user.username}")
    
    return user

