"""
Health check and system info endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get('/version')
def get_version():
    """Get API version"""
    return {
        'version': '2.17.0',
        'build': 'production',
        'api_version': 'v1'
    }


@router.get('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'ok'}

