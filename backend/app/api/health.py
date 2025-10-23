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
        'version': '3.0.4',
        'build': 'production',
        'api_version': 'v1'
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
            'name': 'Backend API',
            'description': 'FastAPI backend with OCR, CRM, and integrations',
            'url': f'{protocol}://{domain}/api' if domain != 'localhost' else None,
            'local_url': 'http://localhost:8000',
            'status': 'running'
        },
        'frontend': {
            'name': 'Frontend (React)',
            'description': 'React web application for business card management',
            'url': f'{protocol}://{domain}' if domain != 'localhost' else None,
            'local_url': 'http://localhost:3000',
            'status': 'running'
        },
        'postgres': {
            'name': 'PostgreSQL Database',
            'description': 'Main database for all application data',
            'url': None,
            'local_url': 'postgresql://localhost:5432',
            'status': 'running'
        },
        'redis': {
            'name': 'Redis Cache',
            'description': 'In-memory cache for OCR results and sessions',
            'url': None,
            'local_url': 'redis://localhost:6379',
            'status': 'running'
        },
        'prometheus': {
            'name': 'Prometheus',
            'description': 'Metrics collection and monitoring',
            'url': f'{protocol}://{domain}:9090' if domain != 'localhost' else None,
            'local_url': 'http://localhost:9090',
            'status': 'available'
        },
        'grafana': {
            'name': 'Grafana',
            'description': 'Metrics visualization and dashboards',
            'url': f'{protocol}://{domain}:3001' if domain != 'localhost' else None,
            'local_url': 'http://localhost:3001',
            'status': 'available'
        },
        'celery': {
            'name': 'Celery Workers',
            'description': 'Asynchronous task processing (OCR, exports, etc)',
            'url': None,
            'local_url': 'N/A',
            'status': 'running'
        },
        'telegram': {
            'name': 'Telegram Bot',
            'description': 'Telegram integration for business card scanning',
            'url': None,
            'local_url': 'N/A',
            'status': 'configured'
        },
        'whatsapp': {
            'name': 'WhatsApp Integration',
            'description': 'WhatsApp webhook for message processing',
            'url': None,
            'local_url': 'N/A',
            'status': 'configured'
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

