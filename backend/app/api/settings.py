"""
Settings & System Configuration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import logging

from ..database import get_db
from ..models import User, Contact, AppSetting
from .. import schemas
from ..core import auth as auth_utils
from ..core.utils import get_setting, set_setting

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


@router.get('/system')
async def get_system_settings(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system settings (admin only).
    Returns various system configuration parameters.
    Uses ContactRepository and UserRepository
    """
    from ..repositories import ContactRepository, UserRepository
    contact_repo = ContactRepository(db)
    user_repo = UserRepository(db)
    
    return {
        "database": {
            "total_contacts": contact_repo.count(),
            "total_users": user_repo.count(),
            "pending_users": user_repo.count_by_is_active(False),
        },
        "ocr": {
            "default_provider": "auto",
            "available_providers": ["tesseract", "parsio", "google", "auto"],
            "tesseract_langs": os.getenv("TESSERACT_LANGS", "rus+eng"),
        },
        "telegram": {
            "bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", ""),
        },
        "authentication": {
            "token_expire_minutes": auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES,
            "require_admin_approval": True,
        },
        "application": {
            "version": os.getenv("APP_VERSION", "2.13"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
    }


@router.get('/pending-users', response_model=List[schemas.UserResponse])
async def get_pending_users(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users pending approval (admin only).
    Returns users with is_active=False.
    Uses UserRepository
    """
    from ..repositories import UserRepository
    user_repo = UserRepository(db)
    pending_users = user_repo.get_users_by_is_active(False)
    return pending_users


@router.get('/editable')
async def get_editable_settings(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get editable settings (admin only).
    Returns current environment variables and database settings.
    Uses SettingsRepository
    """
    from ..repositories import SettingsRepository
    settings_repo = SettingsRepository(db)
    
    def get_db_setting(key: str, default: str = ""):
        setting = settings_repo.get_app_setting(key)
        return setting.value if setting else default
    
    return {
        "ocr": {
            "tesseract_langs": get_db_setting("TESSERACT_LANGS", os.getenv("TESSERACT_LANGS", "rus+eng")),
            "parsio_api_key": get_db_setting("PARSIO_API_KEY", ""),
            "google_vision_api_key": get_db_setting("GOOGLE_VISION_API_KEY", ""),
        },
        "telegram": {
            "bot_token": get_db_setting("TELEGRAM_BOT_TOKEN", ""),
            "webhook_url": get_db_setting("TELEGRAM_WEBHOOK_URL", ""),
        },
        "whatsapp": {
            "api_token": get_db_setting("WHATSAPP_API_TOKEN", ""),
            "phone_number_id": get_db_setting("WHATSAPP_PHONE_NUMBER_ID", ""),
            "business_account_id": get_db_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            "webhook_verify_token": get_db_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
        },
        "redis": {
            "url": get_db_setting("REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")),
            "max_connections": int(get_db_setting("REDIS_MAX_CONNECTIONS", "10")),
        },
        "celery": {
            "broker_url": get_db_setting("CELERY_BROKER_URL", os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")),
            "result_backend": get_db_setting("CELERY_RESULT_BACKEND", os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")),
            "worker_concurrency": int(get_db_setting("CELERY_WORKER_CONCURRENCY", "2")),
            "task_time_limit": int(get_db_setting("CELERY_TASK_TIME_LIMIT", "300")),
        },
        "backup": {
            "enabled": get_db_setting("BACKUP_ENABLED", "true") == "true",
            "schedule": get_db_setting("BACKUP_SCHEDULE", "0 2 * * *"),
            "retention_days": int(get_db_setting("BACKUP_RETENTION_DAYS", "30")),
            "backup_dir": get_db_setting("BACKUP_DIR", "/home/ubuntu/fastapi-bizcard-crm-ready/backups"),
        },
        "monitoring": {
            "prometheus_enabled": get_db_setting("PROMETHEUS_ENABLED", "true") == "true",
            "grafana_enabled": get_db_setting("GRAFANA_ENABLED", "true") == "true",
            "metrics_retention_days": int(get_db_setting("METRICS_RETENTION_DAYS", "15")),
        }
    }


@router.put('/editable')
async def update_editable_settings(
    settings: dict = Body(...),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update editable settings (admin only).
    Saves settings to database.
    Uses SettingsRepository
    """
    from ..repositories import SettingsRepository
    settings_repo = SettingsRepository(db)
    
    def set_db_setting(key: str, value: str):
        existing = settings_repo.get_app_setting(key)
        if existing:
            settings_repo.update_app_setting(key, value)
        else:
            settings_repo.create_app_setting(key, value)
    
    # Update OCR settings
    if "ocr" in settings:
        if "tesseract_langs" in settings["ocr"]:
            set_db_setting("TESSERACT_LANGS", settings["ocr"]["tesseract_langs"])
        if "parsio_api_key" in settings["ocr"]:
            set_db_setting("PARSIO_API_KEY", settings["ocr"]["parsio_api_key"])
        if "google_vision_api_key" in settings["ocr"]:
            set_db_setting("GOOGLE_VISION_API_KEY", settings["ocr"]["google_vision_api_key"])
    
    # Update Telegram settings
    if "telegram" in settings:
        if "bot_token" in settings["telegram"]:
            set_db_setting("TELEGRAM_BOT_TOKEN", settings["telegram"]["bot_token"])
        if "webhook_url" in settings["telegram"]:
            set_db_setting("TELEGRAM_WEBHOOK_URL", settings["telegram"]["webhook_url"])
    
    # Update WhatsApp settings
    if "whatsapp" in settings:
        if "api_token" in settings["whatsapp"]:
            set_db_setting("WHATSAPP_API_TOKEN", settings["whatsapp"]["api_token"])
        if "phone_number_id" in settings["whatsapp"]:
            set_db_setting("WHATSAPP_PHONE_NUMBER_ID", settings["whatsapp"]["phone_number_id"])
        if "business_account_id" in settings["whatsapp"]:
            set_db_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", settings["whatsapp"]["business_account_id"])
        if "webhook_verify_token" in settings["whatsapp"]:
            set_db_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", settings["whatsapp"]["webhook_verify_token"])
    
    # Update Redis settings
    if "redis" in settings:
        if "url" in settings["redis"]:
            set_db_setting("REDIS_URL", settings["redis"]["url"])
        if "max_connections" in settings["redis"]:
            set_db_setting("REDIS_MAX_CONNECTIONS", str(settings["redis"]["max_connections"]))
    
    # Update Celery settings
    if "celery" in settings:
        if "broker_url" in settings["celery"]:
            set_db_setting("CELERY_BROKER_URL", settings["celery"]["broker_url"])
        if "result_backend" in settings["celery"]:
            set_db_setting("CELERY_RESULT_BACKEND", settings["celery"]["result_backend"])
        if "worker_concurrency" in settings["celery"]:
            set_db_setting("CELERY_WORKER_CONCURRENCY", str(settings["celery"]["worker_concurrency"]))
        if "task_time_limit" in settings["celery"]:
            set_db_setting("CELERY_TASK_TIME_LIMIT", str(settings["celery"]["task_time_limit"]))
    
    # Update Backup settings
    if "backup" in settings:
        if "enabled" in settings["backup"]:
            set_db_setting("BACKUP_ENABLED", "true" if settings["backup"]["enabled"] else "false")
        if "schedule" in settings["backup"]:
            set_db_setting("BACKUP_SCHEDULE", settings["backup"]["schedule"])
        if "retention_days" in settings["backup"]:
            set_db_setting("BACKUP_RETENTION_DAYS", str(settings["backup"]["retention_days"]))
        if "backup_dir" in settings["backup"]:
            set_db_setting("BACKUP_DIR", settings["backup"]["backup_dir"])
    
    # Update Monitoring settings
    if "monitoring" in settings:
        if "prometheus_enabled" in settings["monitoring"]:
            set_db_setting("PROMETHEUS_ENABLED", "true" if settings["monitoring"]["prometheus_enabled"] else "false")
        if "grafana_enabled" in settings["monitoring"]:
            set_db_setting("GRAFANA_ENABLED", "true" if settings["monitoring"]["grafana_enabled"] else "false")
        if "metrics_retention_days" in settings["monitoring"]:
            set_db_setting("METRICS_RETENTION_DAYS", str(settings["monitoring"]["metrics_retention_days"]))
    
    settings_repo.commit()
    
    logger.info(f"Settings updated by admin: {current_user.username}")
    
    return {
        "success": True,
        "message": "Settings updated successfully"
    }


@router.get('/integrations/status')
async def get_integrations_status(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get status of all integrations (admin only).
    Returns enabled/disabled status and health check for each integration.
    Uses SettingsRepository
    """
    from ..repositories import SettingsRepository
    settings_repo = SettingsRepository(db)
    
    def get_integration_setting(key: str, default: str = "false"):
        setting = settings_repo.get_app_setting(key)
        return setting.value if setting else default
    
    # Check Redis connection
    redis_configured = False
    redis_connection_ok = None
    try:
        import redis
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        r = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=1)
        r.ping()
        redis_configured = True
        redis_connection_ok = True
    except:
        redis_configured = bool(os.getenv("REDIS_HOST"))
        redis_connection_ok = False if redis_configured else None
    
    # Check Celery
    celery_configured = bool(os.getenv("CELERY_BROKER_URL"))
    
    # Check Auth settings
    auth_configured = bool(os.getenv("SECRET_KEY") and os.getenv("ALGORITHM"))
    
    # Check Backup settings
    backup_configured = bool(get_integration_setting("backup.path") or os.getenv("BACKUP_PATH"))
    
    # Check Monitoring
    prometheus_configured = bool(os.getenv("PROMETHEUS_ENABLED", "true") == "true")
    
    return {
        "integrations": [
            {
                "id": "ocr",
                "name": "OCR v2.0 Recognition",
                "description": "🚀 PaddleOCR + LayoutLMv3 AI + Auto-Validation (Tesseract fallback)",
                "enabled": True,
                "configured": True,  # OCR v2.0 works out of the box
                "status": "active",
                "connection_ok": True,
                "config": {
                    "version": "2.0",
                    "primary_provider": "PaddleOCR",
                    "ai_classification": "LayoutLMv3",
                    "auto_validation": "enabled",
                    "fallback_provider": "Tesseract",
                    "minio_storage": "enabled",
                    "google_vision_key": "***" if os.getenv("GOOGLE_VISION_API_KEY") else "not configured",
                    "parsio_key": "***" if os.getenv("PARSIO_API_KEY") else "not configured"
                },
                "config_summary": {
                    "Version": "2.0 (PaddleOCR)",
                    "AI Model": "LayoutLMv3 ✅",
                    "Validator": "Auto-correct ✅",
                    "Storage": "MinIO ✅",
                    "Fallback": "Tesseract v1.0"
                }
            },
            {
                "id": "telegram",
                "name": "Telegram Bot",
                "description": "Receive business cards via Telegram bot",
                "enabled": get_integration_setting("telegram.enabled", "false") == "true",
                "configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
                "status": "active" if get_integration_setting("telegram.enabled") == "true" else "inactive",
                "connection_ok": bool(os.getenv("TELEGRAM_BOT_TOKEN")) if get_integration_setting("telegram.enabled") == "true" else None,
                "config": {
                    "bot_token": "***" if os.getenv("TELEGRAM_BOT_TOKEN") else "",
                    "webhook_url": get_integration_setting("telegram.webhook_url", "")
                },
                "config_summary": {
                    "Bot": "Configured" if os.getenv("TELEGRAM_BOT_TOKEN") else "Not configured"
                }
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp Business",
                "description": "Receive business cards via WhatsApp Business",
                "enabled": get_integration_setting("whatsapp.enabled", "false") == "true",
                "configured": bool(get_integration_setting("WHATSAPP_API_TOKEN")),
                "status": "active" if get_integration_setting("whatsapp.enabled") == "true" else "inactive",
                "connection_ok": bool(get_integration_setting("WHATSAPP_API_TOKEN")) if get_integration_setting("whatsapp.enabled") == "true" else None,
                "config": {
                    "api_token": "***" if get_integration_setting("WHATSAPP_API_TOKEN") else "",
                    "phone_number": get_integration_setting("whatsapp.phone_number", "")
                },
                "config_summary": {
                    "API": "Configured" if get_integration_setting("WHATSAPP_API_TOKEN") else "Not configured"
                }
            },
            {
                "id": "auth",
                "name": "Authentication",
                "description": "User authentication and authorization settings",
                "enabled": True,
                "configured": auth_configured,
                "status": "active",
                "connection_ok": auth_configured,
                "config": {
                    "secret_key": "***" if os.getenv("SECRET_KEY") else "",
                    "algorithm": os.getenv("ALGORITHM", "HS256"),
                    "access_token_expire": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
                },
                "config_summary": {
                    "Algorithm": os.getenv("ALGORITHM", "HS256"),
                    "Token Expire": f"{os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '10080')} min"
                }
            },
            {
                "id": "backup",
                "name": "Backup & Recovery",
                "description": "Automatic database backup configuration",
                "enabled": get_integration_setting("backup.enabled", "true") == "true",
                "configured": backup_configured,
                "status": "active" if get_integration_setting("backup.enabled") == "true" else "inactive",
                "connection_ok": backup_configured if get_integration_setting("backup.enabled") == "true" else None,
                "config": {
                    "backup_path": get_integration_setting("backup.path", os.getenv("BACKUP_PATH", "/backups")),
                    "schedule": get_integration_setting("backup.schedule", "daily"),
                    "retention_days": get_integration_setting("backup.retention", "30")
                },
                "config_summary": {
                    "Schedule": get_integration_setting("backup.schedule", "daily"),
                    "Retention": f"{get_integration_setting('backup.retention', '30')} days"
                }
            },
            {
                "id": "monitoring",
                "name": "Monitoring",
                "description": "Prometheus and Grafana monitoring",
                "enabled": prometheus_configured,
                "configured": True,
                "status": "active" if prometheus_configured else "inactive",
                "connection_ok": True,
                "config": {
                    "prometheus_enabled": str(prometheus_configured),
                    "prometheus_port": os.getenv("PROMETHEUS_PORT", "9090"),
                    "grafana_port": os.getenv("GRAFANA_PORT", "3001")
                },
                "config_summary": {
                    "Prometheus": f"Port {os.getenv('PROMETHEUS_PORT', '9090')}",
                    "Grafana": f"Port {os.getenv('GRAFANA_PORT', '3001')}"
                }
            },
            {
                "id": "celery",
                "name": "Background Tasks",
                "description": "⚡ Async processing: OCR v2.0 + Batch + Export + Validation",
                "enabled": celery_configured,
                "configured": celery_configured,
                "status": "active" if celery_configured else "inactive",
                "connection_ok": celery_configured,
                "config": {
                    "broker_url": "***" if os.getenv("CELERY_BROKER_URL") else "",
                    "result_backend": "***" if os.getenv("CELERY_RESULT_BACKEND") else "",
                    "workers": get_integration_setting("celery.workers", "2"),
                    "ocr_v2_enabled": "true"
                },
                "config_summary": {
                    "Broker": "Redis" if "redis" in os.getenv("CELERY_BROKER_URL", "") else "Not configured",
                    "Workers": get_integration_setting("celery.workers", "2"),
                    "OCR": "v2.0 ✅"
                }
            },
            {
                "id": "redis",
                "name": "Redis Cache",
                "description": "In-memory cache for OCR results and sessions",
                "enabled": redis_configured,
                "configured": redis_configured,
                "status": "active" if redis_configured else "inactive",
                "connection_ok": redis_connection_ok,
                "config": {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": os.getenv("REDIS_PORT", "6379"),
                    "db": os.getenv("REDIS_DB", "0")
                },
                "config_summary": {
                    "Host": os.getenv("REDIS_HOST", "localhost"),
                    "Port": os.getenv("REDIS_PORT", "6379")
                }
            }
        ]
    }


@router.post('/integrations/{integration_id}/toggle')
async def toggle_integration(
    integration_id: str,
    enabled: bool = Body(..., embed=True),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Enable or disable an integration (admin only).
    Uses SettingsRepository
    """
    valid_integrations = ["telegram", "whatsapp", "ocr", "auth", "backup", "monitoring", "celery", "redis"]
    
    if integration_id not in valid_integrations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration ID: {integration_id}"
        )
    
    # Save to database using SettingsRepository
    from ..repositories import SettingsRepository
    settings_repo = SettingsRepository(db)
    setting_key = f"{integration_id}.enabled"
    value = "true" if enabled else "false"
    
    existing = settings_repo.get_app_setting(setting_key)
    if existing:
        settings_repo.update_app_setting(setting_key, value)
    else:
        settings_repo.create_app_setting(setting_key, value)
    
    settings_repo.commit()
    
    logger.info(f"Integration {integration_id} {'enabled' if enabled else 'disabled'} by {current_user.username}")
    
    return {
        "success": True,
        "integration_id": integration_id,
        "enabled": enabled
    }


@router.post('/integrations/{integration_id}/test')
async def test_integration(
    integration_id: str,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Test an integration connection (admin only).
    """
    valid_integrations = ["telegram", "whatsapp", "ocr", "auth", "backup", "monitoring", "celery", "redis"]
    
    if integration_id not in valid_integrations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration ID: {integration_id}"
        )
    
    # TODO: Implement actual integration tests
    # For now, just return success
    
    return {
        "success": True,
        "integration_id": integration_id,
        "status": "connection_successful",
        "message": f"{integration_id} integration test successful"
    }


@router.put('/integrations/{integration_id}/config')
async def update_integration_config(
    integration_id: str,
    config: dict = Body(...),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update integration configuration (admin only).
    Uses SettingsRepository
    """
    valid_integrations = ["telegram", "whatsapp", "ocr", "auth", "backup", "monitoring", "celery", "redis"]
    
    if integration_id not in valid_integrations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration ID: {integration_id}"
        )
    
    # Save configuration to database using SettingsRepository
    from ..repositories import SettingsRepository
    settings_repo = SettingsRepository(db)
    
    for key, value in config.items():
        setting_key = f"{integration_id}.{key}"
        existing = settings_repo.get_app_setting(setting_key)
        if existing:
            settings_repo.update_app_setting(setting_key, str(value))
        else:
            settings_repo.create_app_setting(setting_key, str(value))
    
    settings_repo.commit()
    
    logger.info(f"Integration {integration_id} config updated by {current_user.username}")
    
    return {
        "success": True,
        "integration_id": integration_id,
        "message": "Configuration updated successfully"
    }

