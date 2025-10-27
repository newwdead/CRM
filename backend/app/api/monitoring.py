"""
Monitoring Dashboard API
Real-time monitoring of OCR v2.0 services and business card processing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, List
import os
import logging
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, Contact
from ..core import auth as auth_utils

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/dashboard')
async def get_monitoring_dashboard(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive monitoring dashboard data
    - Services status
    - Celery queue status
    - OCR processing stats
    - Recent scans
    """
    
    # 1. Services Status
    services_status = await get_services_status()
    
    # 2. Celery Queue Status
    queue_status = await get_celery_queue_status()
    
    # 3. OCR Processing Stats (last 24h)
    ocr_stats = await get_ocr_processing_stats(db)
    
    # 4. Recent Scans (last 20)
    recent_scans = await get_recent_scans(db)
    
    # 5. System Health
    system_health = await get_system_health()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status,
        "queue": queue_status,
        "ocr_stats": ocr_stats,
        "recent_scans": recent_scans,
        "system_health": system_health
    }


async def get_services_status() -> Dict[str, Any]:
    """Check status of all OCR v2.0 services"""
    services = {}
    
    # Backend
    services["backend"] = {
        "name": "Backend API",
        "version": "6.0.0",
        "status": "healthy",
        "uptime": "N/A"
    }
    
    # Celery Worker
    try:
        # Try to connect to Celery
        from ..celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        services["celery"] = {
            "name": "Celery Workers",
            "status": "healthy" if active_workers else "warning",
            "workers_count": len(active_workers) if active_workers else 0,
            "active_tasks": sum(len(tasks) for tasks in (active_workers or {}).values())
        }
    except Exception as e:
        logger.error(f"Failed to get Celery status: {e}")
        services["celery"] = {
            "name": "Celery Workers",
            "status": "error",
            "error": str(e)
        }
    
    # MinIO
    try:
        import requests
        response = requests.get("http://minio:9000/minio/health/live", timeout=2)
        services["minio"] = {
            "name": "MinIO Storage",
            "status": "healthy" if response.status_code == 200 else "error",
            "endpoint": "minio:9000"
        }
    except Exception as e:
        services["minio"] = {
            "name": "MinIO Storage",
            "status": "error",
            "error": "Connection failed"
        }
    
    # Redis
    try:
        import redis
        r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, socket_connect_timeout=2)
        r.ping()
        services["redis"] = {
            "name": "Redis Cache",
            "status": "healthy",
            "endpoint": f"{os.getenv('REDIS_HOST', 'redis')}:6379"
        }
    except Exception as e:
        services["redis"] = {
            "name": "Redis Cache",
            "status": "error",
            "error": "Connection failed"
        }
    
    # PostgreSQL
    try:
        services["postgres"] = {
            "name": "PostgreSQL",
            "status": "healthy",
            "endpoint": "db:5432"
        }
    except Exception as e:
        services["postgres"] = {
            "name": "PostgreSQL",
            "status": "error",
            "error": str(e)
        }
    
    # Label Studio
    try:
        import requests
        response = requests.get("http://label-studio:8080/health", timeout=2)
        services["label_studio"] = {
            "name": "Label Studio",
            "status": "healthy" if response.status_code == 200 else "warning",
            "endpoint": "label-studio:8080"
        }
    except Exception:
        services["label_studio"] = {
            "name": "Label Studio",
            "status": "unknown",
            "endpoint": "label-studio:8080"
        }
    
    return services


async def get_celery_queue_status() -> Dict[str, Any]:
    """Get Celery queue status and task statistics"""
    try:
        from ..celery_app import celery_app
        inspect = celery_app.control.inspect()
        
        # Active tasks
        active = inspect.active()
        active_count = sum(len(tasks) for tasks in (active or {}).values())
        
        # Scheduled tasks
        scheduled = inspect.scheduled()
        scheduled_count = sum(len(tasks) for tasks in (scheduled or {}).values())
        
        # Reserved tasks
        reserved = inspect.reserved()
        reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())
        
        # Stats
        stats = inspect.stats()
        
        return {
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
            "total_pending": active_count + scheduled_count + reserved_count,
            "workers": list(stats.keys()) if stats else [],
            "workers_count": len(stats) if stats else 0,
            "status": "operational" if stats else "no_workers"
        }
    except Exception as e:
        logger.error(f"Failed to get Celery queue status: {e}")
        return {
            "active_tasks": 0,
            "scheduled_tasks": 0,
            "reserved_tasks": 0,
            "total_pending": 0,
            "workers": [],
            "workers_count": 0,
            "status": "error",
            "error": str(e)
        }


async def get_ocr_processing_stats(db: Session) -> Dict[str, Any]:
    """Get OCR processing statistics for last 24 hours"""
    try:
        # Get contacts created in last 24h
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        # Total scans
        total_scans = db.query(func.count(Contact.id)).filter(
            Contact.created_at >= yesterday
        ).scalar() or 0
        
        # Scans with recognition method
        ocr_scans = db.query(func.count(Contact.id)).filter(
            Contact.created_at >= yesterday,
            Contact.recognition_method.isnot(None)
        ).scalar() or 0
        
        # Scans by recognition method
        method_stats = db.query(
            Contact.recognition_method,
            func.count(Contact.id).label('count')
        ).filter(
            Contact.created_at >= yesterday
        ).group_by(Contact.recognition_method).all()
        
        methods_breakdown = {
            method: count for method, count in method_stats if method
        }
        
        # Average confidence (if available)
        # Note: You might need to add a confidence field to Contact model
        
        return {
            "period": "last_24h",
            "total_scans": total_scans,
            "ocr_scans": ocr_scans,
            "methods_breakdown": methods_breakdown,
            "success_rate": round((ocr_scans / total_scans * 100) if total_scans > 0 else 0, 2)
        }
    except Exception as e:
        logger.error(f"Failed to get OCR stats: {e}")
        return {
            "period": "last_24h",
            "total_scans": 0,
            "ocr_scans": 0,
            "methods_breakdown": {},
            "success_rate": 0,
            "error": str(e)
        }


async def get_recent_scans(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent business card scans"""
    try:
        recent_contacts = db.query(Contact).order_by(
            desc(Contact.created_at)
        ).limit(limit).all()
        
        scans = []
        for contact in recent_contacts:
            scans.append({
                "id": contact.id,
                "full_name": contact.full_name or "Unknown",
                "company": contact.company or "",
                "recognition_method": contact.recognition_method or "unknown",
                "created_at": contact.created_at.isoformat() if contact.created_at else None,
                "has_photo": bool(contact.photo_path),
                "fields_count": sum([
                    bool(contact.full_name),
                    bool(contact.email),
                    bool(contact.phone),
                    bool(contact.company),
                    bool(contact.position),
                    bool(contact.website),
                ])
            })
        
        return scans
    except Exception as e:
        logger.error(f"Failed to get recent scans: {e}")
        return []


async def get_system_health() -> Dict[str, Any]:
    """Get overall system health indicators"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Overall health status
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            status = "critical"
        elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "disk_percent": round(disk_percent, 2),
            "uptime": "N/A"  # Can be calculated from start time
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "status": "unknown",
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "error": str(e)
        }


@router.get('/services/docker')
async def get_docker_services(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get Docker services status
    """
    try:
        import docker
        client = docker.from_env()
        
        # Get all containers
        containers = client.containers.list(all=True)
        
        services = []
        for container in containers:
            # Filter only bizcard-related containers
            if 'bizcard' in container.name or 'label-studio' in container.name:
                services.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "health": container.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown'),
                    "created": container.attrs.get('Created', ''),
                    "ports": container.attrs.get('NetworkSettings', {}).get('Ports', {})
                })
        
        return {
            "services": services,
            "total_count": len(services),
            "running_count": len([s for s in services if s['status'] == 'running']),
            "healthy_count": len([s for s in services if s['health'] == 'healthy'])
        }
    except Exception as e:
        logger.error(f"Failed to get Docker services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Docker services: {str(e)}")

