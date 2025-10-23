"""
Security Headers Middleware
Adds OWASP recommended security headers to all responses
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    Based on OWASP recommendations
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Strict-Transport-Security (HSTS)
        # Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        # Enable XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy (CSP)
        # Restrict resource loading to prevent XSS
        # Note: Adjust for your specific needs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # 'unsafe-inline' for React
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Permissions-Policy (formerly Feature-Policy)
        # Disable unused browser features
        permissions = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers["Permissions-Policy"] = permissions
        
        # X-Permitted-Cross-Domain-Policies
        # Restrict Adobe Flash/PDF cross-domain requests
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Cache-Control for sensitive endpoints
        if "/api/" in request.url.path and request.url.path not in ["/api/health", "/api/version"]:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        
        return response


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """
    Functional middleware version (alternative to class-based)
    """
    response = await call_next(request)
    
    # Add security headers
    security_headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Permitted-Cross-Domain-Policies": "none"
    }
    
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response

