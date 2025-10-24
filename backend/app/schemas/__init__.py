"""
Pydantic schemas package for request/response validation.
"""
from .user import (
    UserRegister,
    UserLogin,
    Token,
    RefreshTokenRequest,
    TokenData,
    UserResponse,
    UserUpdate,
)
from .contact import (
    ContactBase,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    PaginatedContactsResponse,
    TagBase,
    TagCreate,
    TagUpdate,
    TagResponse,
    GroupBase,
    GroupCreate,
    GroupUpdate,
    GroupResponse,
)
from .audit import AuditLogResponse
from .duplicate import DuplicateContactResponse

__all__ = [
    # User schemas
    'UserRegister',
    'UserLogin',
    'Token',
    'RefreshTokenRequest',
    'TokenData',
    'UserResponse',
    'UserUpdate',
    # Contact schemas
    'ContactBase',
    'ContactCreate',
    'ContactUpdate',
    'ContactResponse',
    'PaginatedContactsResponse',
    # Tag schemas
    'TagBase',
    'TagCreate',
    'TagUpdate',
    'TagResponse',
    # Group schemas
    'GroupBase',
    'GroupCreate',
    'GroupUpdate',
    'GroupResponse',
    # Audit schemas
    'AuditLogResponse',
    # Duplicate schemas
    'DuplicateContactResponse',
]
