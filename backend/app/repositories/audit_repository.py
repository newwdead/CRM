"""
Audit Repository Layer
Handles all database operations for Audit Log models.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.audit import AuditLog


class AuditRepository:
    """Repository for AuditLog model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_audit_by_id(self, audit_id: int) -> Optional[AuditLog]:
        """
        Get audit log by ID.
        
        Args:
            audit_id: Audit log ID
        
        Returns:
            AuditLog instance or None
        """
        return self.db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    
    def get_all_audit_logs(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all audit logs with pagination, ordered by timestamp desc.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).options(
            joinedload(AuditLog.user)
        ).order_by(
            desc(AuditLog.timestamp)
        ).offset(skip).limit(limit).all()
    
    def get_audit_logs_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            desc(AuditLog.timestamp)
        ).offset(skip).limit(limit).all()
    
    def get_audit_logs_by_action(
        self, 
        action: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs by action type.
        
        Args:
            action: Action type (e.g., 'create', 'update', 'delete')
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.action == action
        ).order_by(
            desc(AuditLog.timestamp)
        ).offset(skip).limit(limit).all()
    
    def get_audit_logs_by_entity(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific entity.
        
        Args:
            entity_type: Type of entity (e.g., 'contact', 'user')
            entity_id: Entity ID
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(
            desc(AuditLog.timestamp)
        ).all()
    
    def get_audit_logs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs within a date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ).order_by(
            desc(AuditLog.timestamp)
        ).offset(skip).limit(limit).all()
    
    def create_audit_log(self, audit_data: Dict[str, Any]) -> AuditLog:
        """
        Create a new audit log entry.
        
        Args:
            audit_data: Dictionary with audit log data
        
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(**audit_data)
        self.db.add(audit_log)
        self.db.flush()
        return audit_log
    
    def delete_audit_log(self, audit_log: AuditLog) -> None:
        """
        Delete audit log record.
        
        Args:
            audit_log: AuditLog instance to delete
        """
        self.db.delete(audit_log)
    
    def delete_old_audit_logs(self, before_date: datetime) -> int:
        """
        Delete audit logs older than specified date.
        
        Args:
            before_date: Delete logs before this date
        
        Returns:
            Number of deleted records
        """
        count = self.db.query(AuditLog).filter(
            AuditLog.timestamp < before_date
        ).delete()
        return count
    
    def count_audit_logs(self) -> int:
        """
        Count total number of audit logs.
        
        Returns:
            Total count
        """
        return self.db.query(AuditLog).count()
    
    def count_audit_logs_by_user(self, user_id: int) -> int:
        """
        Count audit logs for a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            Count of audit logs
        """
        return self.db.query(AuditLog).filter(AuditLog.user_id == user_id).count()
    
    def commit(self) -> None:
        """Commit database transaction."""
        self.db.commit()
    
    def refresh(self, instance) -> None:
        """Refresh instance from database."""
        self.db.refresh(instance)

