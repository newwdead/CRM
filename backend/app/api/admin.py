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
from ..core import auth as auth_utils

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
    """
    Get recent audit logs (admin only).
    Uses AuditRepository
    """
    from ..repositories import AuditRepository
    audit_repo = AuditRepository(db)
    
    logs = audit_repo.get_recent_logs(limit=limit, entity_type=entity_type)
    
    return logs


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get('/statistics/overview')
def get_statistics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get overall statistics and analytics.
    Uses ContactRepository and UserRepository for counts
    """
    from ..repositories import ContactRepository, UserRepository
    contact_repo = ContactRepository(db)
    user_repo = UserRepository(db)
    
    # Total counts - using repositories
    total_contacts = contact_repo.count()
    total_users = user_repo.count()
    
    # Tags and Groups - keeping direct queries for now (no repositories yet)
    total_tags = db.query(Tag).count()
    total_groups = db.query(Group).count()
    
    # Contacts with contact info - keeping direct queries for complex filters
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
    Returns list sorted by creation time (newest first).
    """
    from datetime import datetime
    
    # Use relative path (same as create_backup)
    backup_dir = Path("backups")
    
    if not backup_dir.exists():
        logger.info("Backups directory does not exist")
        return []
    
    backups = []
    try:
        backup_files = list(backup_dir.glob('*.sql.gz')) + list(backup_dir.glob('*.sql'))
        
        if not backup_files:
            logger.info("No backup files found")
            return []
        
        for file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                stat = file.stat()
                created_dt = datetime.fromtimestamp(stat.st_mtime)
                size_mb = stat.st_size / (1024 * 1024)
                
                backups.append({
                    'filename': file.name,
                    'size_bytes': stat.st_size,
                    'size_mb': round(size_mb, 2),
                    'created_timestamp': stat.st_mtime,
                    'created_date': created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    'created_relative': _get_relative_time(created_dt)
                })
            except Exception as e:
                logger.warning(f"Failed to get stats for {file.name}: {e}")
                continue
        
        logger.info(f"Found {len(backups)} backup files")
        return backups
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


def _get_relative_time(dt):
    """Get human-readable relative time"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")


@router.post('/backups/create')
async def create_backup(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Create a new database backup (admin only).
    Uses pg_dump to create a compressed SQL dump.
    """
    import subprocess
    import os
    from datetime import datetime
    
    logger.info(f"Backup requested by admin: {current_user.username}")
    
    # Get database connection details from environment
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "bizcard_crm")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    
    # Create backups directory if it doesn't exist
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sql.gz"
    backup_path = backup_dir / backup_filename
    
    try:
        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # Run pg_dump with gzip compression
        pg_dump_cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "--no-password",
            "--format=plain",
            "--no-owner",
            "--no-acl"
        ]
        
        gzip_cmd = ["gzip", "-"]
        
        # Execute pg_dump | gzip > backup_file
        with open(backup_path, "wb") as f:
            pg_dump_proc = subprocess.Popen(
                pg_dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            gzip_proc = subprocess.Popen(
                gzip_cmd,
                stdin=pg_dump_proc.stdout,
                stdout=f,
                stderr=subprocess.PIPE
            )
            
            # Wait for both processes to complete
            pg_dump_proc.stdout.close()
            gzip_stdout, gzip_stderr = gzip_proc.communicate()
            
            # Wait for pg_dump to finish and get its output
            pg_dump_proc.wait()
            pg_dump_stderr = pg_dump_proc.stderr.read()
            
            # Check for errors with better error messages
            if pg_dump_proc.returncode is not None and pg_dump_proc.returncode != 0:
                error_msg = pg_dump_stderr.decode('utf-8').strip() if pg_dump_stderr else f"pg_dump exited with code {pg_dump_proc.returncode}"
                logger.error(f"pg_dump failed (exit code {pg_dump_proc.returncode}): {error_msg}")
                logger.error(f"pg_dump command: {' '.join(pg_dump_cmd)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Backup failed: {error_msg}"
                )
            
            if gzip_proc.returncode is not None and gzip_proc.returncode != 0:
                error_msg = gzip_stderr.decode('utf-8').strip() if gzip_stderr else f"gzip exited with code {gzip_proc.returncode}"
                logger.error(f"gzip failed (exit code {gzip_proc.returncode}): {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Compression failed: {error_msg}"
                )
        
        # Get backup file size
        backup_size = backup_path.stat().st_size
        size_mb = backup_size / (1024 * 1024)
        
        logger.info(f"Backup created successfully: {backup_filename} ({size_mb:.2f} MB)")
        
        return {
            "success": True,
            "message": f"Backup created successfully: {backup_filename}",
            "filename": backup_filename,
            "size_bytes": backup_size,
            "size_mb": round(size_mb, 2),
            "created_at": timestamp,
            "created_by": current_user.username
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Backup timed out after 300 seconds")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup timed out (>5 minutes)"
        )
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}", exc_info=True)
        
        # Clean up partial backup file
        if backup_path.exists():
            backup_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )

