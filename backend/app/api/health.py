"""
Health check and system info endpoints
"""
from fastapi import APIRouter
import os

router = APIRouter()


@router.get('/version')
def get_version():
    """Get API version"""
    return {
        'version': '6.0.0',
        'build': 'production',
        'api_version': 'v1',
        'python': '3.11.14',
        'fastapi': '0.115.0',
        'sqlalchemy': '2.0.36',
        'react': '18.3.1',
        'security_update': 'phase1-complete',
        '2fa': 'enabled',
        'file_security': 'enhanced',
        'refresh_tokens': 'enabled',
        'auto_refresh': 'frontend-enabled'
    }


@router.get('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'ok'}


@router.get('/system/resources')
def get_system_resources():
    """
    Get system resources and service URLs
    Returns information about deployed services, URLs, and environment
    """
    # Get domain from environment or use default
    domain = os.getenv('DOMAIN', 'localhost')
    protocol = 'https' if domain != 'localhost' else 'http'
    
    services = {
        'backend': {
            'name': 'Backend API v6.0',
            'description': '🚀 FastAPI + OCR v2.0 (PaddleOCR + LayoutLMv3 + Validator)',
            'url': f'{protocol}://{domain}/api' if domain != 'localhost' else None,
            'local_url': 'http://localhost:8000',
            'status': 'running'
        },
        'frontend': {
            'name': 'Frontend (React)',
            'description': 'Веб-приложение на React для управления визитками',
            'url': f'{protocol}://{domain}' if domain != 'localhost' else None,
            'local_url': 'http://localhost:3000',
            'status': 'running'
        },
        'postgres': {
            'name': 'PostgreSQL Database',
            'description': 'Основная база данных для всех данных приложения',
            'url': None,
            'local_url': 'postgresql://localhost:5432',
            'status': 'running'
        },
        'redis': {
            'name': 'Redis Cache',
            'description': 'Кеш в памяти для результатов OCR и сессий',
            'url': None,
            'local_url': 'redis://localhost:6379',
            'status': 'running'
        },
        'celery': {
            'name': 'Celery Workers',
            'description': '⚡ Асинхронная обработка: OCR v2.0 + Batch + Export + Validation',
            'url': None,
            'local_url': 'N/A',
            'status': 'running'
        },
        'whatsapp': {
            'name': 'WhatsApp Integration',
            'description': 'Интеграция WhatsApp для обработки сообщений',
            'url': None,
            'local_url': 'N/A',
            'status': 'configured'
        },
        'label_studio': {
            'name': 'Label Studio',
            'description': '🏷️ Инструмент для аннотирования визиток (OCR v2.0 training)',
            'url': f'{protocol}://{domain}:8081' if domain != 'localhost' else None,
            'local_url': 'http://localhost:8081',
            'status': 'available'
        },
        'minio': {
            'name': 'MinIO Storage',
            'description': '📦 S3-совместимое хранилище для изображений и OCR результатов',
            'url': f'{protocol}://{domain}:9000' if domain != 'localhost' else None,
            'local_url': 'http://localhost:9000',
            'status': 'running'
        },
        'minio_console': {
            'name': 'MinIO Console',
            'description': '🖥️ Веб-интерфейс для управления MinIO (S3 browser)',
            'url': f'{protocol}://{domain}:9001' if domain != 'localhost' else None,
            'local_url': 'http://localhost:9001',
            'status': 'running'
        },
        'prometheus': {
            'name': 'Prometheus',
            'description': 'Сбор метрик и мониторинг системы',
            'url': None,
            'local_url': 'http://localhost:9090',
            'status': 'running'
        },
        'grafana': {
            'name': 'Grafana',
            'description': 'Визуализация метрик и дашборды мониторинга',
            'url': f'https://monitoring.{domain}' if domain != 'localhost' else None,
            'local_url': 'http://localhost:3001',
            'status': 'available'
        },
        'cadvisor': {
            'name': 'cAdvisor',
            'description': 'Мониторинг ресурсов Docker контейнеров',
            'url': None,  # Только локальный доступ
            'local_url': 'http://localhost:8080',
            'status': 'running'
        },
        'node_exporter': {
            'name': 'Node Exporter',
            'description': 'Экспорт метрик сервера для Prometheus',
            'url': None,
            'local_url': 'http://localhost:9100',
            'status': 'running'
        },
        'redis_exporter': {
            'name': 'Redis Exporter',
            'description': 'Экспорт метрик Redis для Prometheus',
            'url': None,
            'local_url': 'http://localhost:9121',
            'status': 'running'
        },
        'postgres_exporter': {
            'name': 'PostgreSQL Exporter',
            'description': 'Экспорт метрик PostgreSQL для Prometheus',
            'url': None,
            'local_url': 'http://localhost:9187',
            'status': 'running'
        }
    }
    
    environment = {
        'domain': domain,
        'protocol': protocol,
        'server_host': os.getenv('SERVER_HOST', 'localhost'),
        'environment': os.getenv('ENVIRONMENT', 'development')
    }
    
    return {
        'services': services,
        'environment': environment,
        'total_services': len(services)
    }

