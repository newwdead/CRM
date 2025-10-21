"""
Administrative API endpoints (audit logs, statistics, documentation, backups)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List
from pathlib import Path
import logging

from ..database import get_db
from ..models import Contact, User, Tag, Group, AuditLog
from .. import schemas
from .. import auth_utils

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get('/audit/recent', response_model=List[schemas.AuditLogResponse])
def get_recent_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (contact, tag, group)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """Get recent audit logs (admin only)."""
    query = db.query(AuditLog)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return logs


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get('/statistics/overview')
def get_statistics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get overall statistics and analytics."""
    # Total counts
    total_contacts = db.query(Contact).count()
    total_tags = db.query(Tag).count()
    total_groups = db.query(Group).count()
    total_users = db.query(User).count()
    
    # Contacts with contact info
    with_email = db.query(Contact).filter(Contact.email.isnot(None), Contact.email != '').count()
    with_phone = db.query(Contact).filter(Contact.phone.isnot(None), Contact.phone != '').count()
    with_photo = db.query(Contact).filter(Contact.photo_path.isnot(None), Contact.photo_path != '').count()
    
    # Top companies (limit 10)
    top_companies = db.query(
        Contact.company,
        func.count(Contact.id).label('count')
    ).filter(
        Contact.company.isnot(None),
        Contact.company != ''
    ).group_by(Contact.company).order_by(func.count(Contact.id).desc()).limit(10).all()
    
    # Top positions (limit 10)
    top_positions = db.query(
        Contact.position,
        func.count(Contact.id).label('count')
    ).filter(
        Contact.position.isnot(None),
        Contact.position != ''
    ).group_by(Contact.position).order_by(func.count(Contact.id).desc()).limit(10).all()
    
    # Contacts by month (last 12 months)
    # Use database-agnostic approach
    if 'sqlite' in str(db.bind.url):
        # SQLite: use strftime
        contacts_by_month = db.query(
            func.strftime('%Y-%m', Contact.created_at).label('month'),
            func.count(Contact.id).label('count')
        ).group_by('month').order_by('month').limit(12).all()
    else:
        # PostgreSQL: use to_char
        contacts_by_month = db.query(
            func.to_char(Contact.created_at, 'YYYY-MM').label('month'),
            func.count(Contact.id).label('count')
        ).group_by('month').order_by('month').limit(12).all()
    
    return {
        "totals": {
            "contacts": total_contacts,
            "tags": total_tags,
            "groups": total_groups,
            "users": total_users,
        },
        "completeness": {
            "with_email": with_email,
            "with_phone": with_phone,
            "with_photo": with_photo,
            "email_percentage": round((with_email / total_contacts * 100) if total_contacts > 0 else 0, 1),
            "phone_percentage": round((with_phone / total_contacts * 100) if total_contacts > 0 else 0, 1),
            "photo_percentage": round((with_photo / total_contacts * 100) if total_contacts > 0 else 0, 1),
        },
        "top_companies": [{"name": comp, "count": count} for comp, count in top_companies],
        "top_positions": [{"name": pos, "count": count} for pos, count in top_positions],
        "contacts_by_month": [{"month": month, "count": count} for month, count in contacts_by_month],
    }


@router.get('/statistics/tags')
def get_tag_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get statistics about tags usage."""
    # Tag usage counts
    tags_with_counts = db.query(
        Tag.id,
        Tag.name,
        Tag.color,
        func.count(Contact.id).label('contact_count')
    ).outerjoin(Tag.contacts).group_by(Tag.id, Tag.name, Tag.color).order_by(
        func.count(Contact.id).desc()
    ).all()
    
    return {
        "tags": [
            {
                "id": tag_id,
                "name": name,
                "color": color,
                "contact_count": count
            }
            for tag_id, name, color, count in tags_with_counts
        ],
        "total_tags": len(tags_with_counts),
        "total_tagged_contacts": sum(count for _, _, _, count in tags_with_counts)
    }


@router.get('/statistics/groups')
def get_group_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get statistics about groups usage."""
    # Group usage counts
    groups_with_counts = db.query(
        Group.id,
        Group.name,
        Group.description,
        func.count(Contact.id).label('contact_count')
    ).outerjoin(Group.contacts).group_by(Group.id, Group.name, Group.description).order_by(
        func.count(Contact.id).desc()
    ).all()
    
    return {
        "groups": [
            {
                "id": group_id,
                "name": name,
                "description": description,
                "contact_count": count
            }
            for group_id, name, description, count in groups_with_counts
        ],
        "total_groups": len(groups_with_counts),
        "total_grouped_contacts": sum(count for _, _, _, count in groups_with_counts)
    }


# ============================================================================
# DOCUMENTATION ENDPOINTS
# ============================================================================

@router.get('/documentation/{doc_name}')
async def get_documentation(
    doc_name: str,
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get documentation content (admin only).
    Supports all markdown files from project root.
    """
    # Security: ensure doc_name doesn't contain path traversal
    if ".." in doc_name or "/" in doc_name or "\\" in doc_name:
        raise HTTPException(status_code=400, detail="Invalid document name")
    
    # Only allow .md files
    if not doc_name.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown files are allowed")
    
    docs_root = Path("/home/ubuntu/fastapi-bizcard-crm-ready")
    doc_path = docs_root / doc_name
    
    # Verify the file exists and is actually in the project root (not in subdirectories)
    if not doc_path.exists() or doc_path.parent != docs_root:
        raise HTTPException(status_code=404, detail="Documentation file not found")
    
    try:
        content = doc_path.read_text(encoding='utf-8')
        return {
            "filename": doc_name,
            "content": content,
            "size": len(content),
            "last_modified": doc_path.stat().st_mtime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read documentation: {str(e)}")


@router.get('/documentation')
async def list_documentation(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    List available documentation files (admin only).
    Automatically scans for all .md files in project root.
    """
    docs_root = Path("/home/ubuntu/fastapi-bizcard-crm-ready")
    
    # Mapping of filenames to descriptions and categories
    doc_metadata = {
        "README.md": ("Основная документация проекта", "readme"),
        "CONTRIBUTING.md": ("Руководство для разработчиков", "development"),
        "ARCHITECTURE.md": ("Архитектура системы", "development"),
        "TECHNICAL_DEBT.md": ("Реестр технического долга", "development"),
        "PRODUCTION_DEPLOYMENT.md": ("Production Deployment", "production"),
        "TELEGRAM_SETUP.md": ("Настройка Telegram", "telegram"),
        "WHATSAPP_SETUP.md": ("Настройка WhatsApp", "whatsapp"),
        "MONITORING_SETUP.md": ("Настройка мониторинга", "monitoring"),
        "SSL_SETUP.md": ("Настройка SSL/HTTPS", "production"),
        "SYSTEM_SETTINGS_GUIDE.md": ("Системные настройки", "settings"),
        "GITHUB_WORKFLOWS_GUIDE.md": ("GitHub Actions", "development"),
        "OCR_TRAINING_GUIDE.md": ("Обучение OCR", "ocr"),
    }
    
    available_docs = []
    
    # Scan all .md files in project root
    for md_file in sorted(docs_root.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        filename = md_file.name
        
        # Get metadata if available, otherwise generate generic
        if filename in doc_metadata:
            description, category = doc_metadata[filename]
        elif filename.startswith("RELEASE_NOTES_"):
            version = filename.replace("RELEASE_NOTES_", "").replace(".md", "")
            description = f"Release Notes {version}"
            category = "releases"
        elif filename.startswith("DEPLOYMENT_"):
            version = filename.replace("DEPLOYMENT_", "").replace(".md", "")
            description = f"Deployment {version}"
            category = "production"
        else:
            description = filename.replace("_", " ").replace(".md", "")
            category = "other"
        
        stat = md_file.stat()
        available_docs.append({
            "filename": filename,
            "title": description,
            "category": category,
            "size": stat.st_size,
            "last_modified": stat.st_mtime,
        })
    
    return {
        "documents": available_docs,
        "total": len(available_docs)
    }


# ============================================================================
# BACKUP ENDPOINTS
# ============================================================================

@router.get('/backups')
async def list_backups(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    List available database backups (admin only).
    """
    backup_dir = Path("/home/ubuntu/fastapi-bizcard-crm-ready/backups")
    
    if not backup_dir.exists():
        return {"backups": [], "total": 0}
    
    backups = []
    for backup_file in sorted(backup_dir.glob("*.sql.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": stat.st_mtime,
        })
    
    return {
        "backups": backups,
        "total": len(backups),
        "backup_dir": str(backup_dir)
    }


@router.post('/backups/create')
async def create_backup(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Create a new database backup (admin only).
    NOTE: This is a placeholder - actual backup logic should be implemented.
    """
    # TODO: Implement actual backup creation logic
    logger.info(f"Backup requested by admin: {current_user.username}")
    
    return {
        "success": True,
        "message": "Backup creation initiated",
        "note": "Backup implementation pending"
    }

