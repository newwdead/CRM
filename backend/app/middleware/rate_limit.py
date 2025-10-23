"""
Enhanced Rate Limiting Configuration
Extends slowapi with more granular control
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException
import os
import logging

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting
    Uses X-Forwarded-For if behind proxy, otherwise remote address
    """
    # Check if behind proxy (Nginx)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # Take the first one (original client)
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # For authenticated users, also use user ID for more accurate limiting
    # This prevents one user from exhausting the IP-based limit
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"{client_ip}:{user_id}"
    
    return client_ip


# Enhanced rate limiter
enhanced_rate_limit = Limiter(
    key_func=get_client_identifier,
    default_limits=["100/minute"],  # Global default
    storage_uri=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    strategy="fixed-window",  # Options: fixed-window, moving-window
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors
    """
    logger.warning(
        f"Rate limit exceeded for {get_client_identifier(request)} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after": exc.detail.split(" ")[-1] if exc.detail else "60 seconds"
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(exc.detail.split("/")[0] if exc.detail else "100"),
            "X-RateLimit-Remaining": "0"
        }
    )


# Rate limit presets for different endpoint types
RATE_LIMITS = {
    # Authentication endpoints (strict)
    "auth_login": "30/minute",
    "auth_register": "10/hour",
    "auth_refresh": "60/hour",
    
    # Upload endpoints (moderate)
    "upload_single": "60/minute",
    "upload_batch": "20/hour",
    
    # API read operations (generous)
    "api_read": "200/minute",
    
    # API write operations (moderate)
    "api_write": "100/minute",
    
    # Admin operations (strict)
    "admin": "30/minute",
    
    # Search/filter operations (moderate)
    "search": "100/minute",
    
    # Export operations (strict, resource intensive)
    "export": "10/minute",
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit string for a specific endpoint type
    """
    return RATE_LIMITS.get(endpoint_type, "100/minute")

