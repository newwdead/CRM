"""
Enhanced logging middleware with structured logging support
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.logging_config import get_logger, LogContext

logger = get_logger(__name__)


class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced logging middleware that logs:
    - All incoming requests
    - Response status codes
    - Request duration
    - Errors and exceptions
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request start with context
        with LogContext(request_id=request_id, endpoint=path, method=method):
            logger.info(
                f"Request started: {method} {path}",
                extra={
                    'client_ip': client_ip,
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            )
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate duration
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                # Log response
                logger.info(
                    f"Request completed: {method} {path} - {response.status_code}",
                    extra={
                        'status_code': response.status_code,
                        'duration_ms': duration_ms
                    }
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as exc:
                # Calculate duration
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                # Log error with full context
                logger.error(
                    f"Request failed: {method} {path}",
                    extra={
                        'status_code': 500,
                        'duration_ms': duration_ms,
                        'error_type': type(exc).__name__,
                        'error_message': str(exc)
                    },
                    exc_info=True
                )
                
                # Re-raise to let FastAPI handle it
                raise

