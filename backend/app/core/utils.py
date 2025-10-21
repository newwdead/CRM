"""
Core utility functions
"""
from sqlalchemy.orm import Session
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    contact_id: Optional[int],
    user,
    action: str,
    entity_type: str = 'contact',
    changes: Optional[dict] = None
):
    """Create an audit log entry."""
    from ..models import AuditLog
    
    audit_entry = AuditLog(
        contact_id=contact_id,
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        entity_type=entity_type,
        changes=json.dumps(changes, ensure_ascii=False) if changes else None
    )
    db.add(audit_entry)


def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an app setting value."""
    from ..models import AppSetting
    
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default


def set_setting(db: Session, key: str, value: Optional[str]):
    """Set an app setting value."""
    from ..models import AppSetting
    
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
        db.add(row)
    db.commit()


def get_system_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a system setting value."""
    from ..models import SystemSettings
    
    row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return row.value if row else default


def set_system_setting(db: Session, key: str, value: Optional[str]):
    """Set a system setting value."""
    from ..models import SystemSettings
    
    row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if row:
        row.value = value
    else:
        row = SystemSettings(key=key, value=value)
        db.add(row)
    db.commit()

