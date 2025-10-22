"""
Security Headers Middleware
Adds security-related HTTP headers to all responses.
"""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    Implements OWASP best practices.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control which features and APIs can be used
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "midi=(), "
            "camera=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "microphone=()"
        )
        
        # HSTS (HTTP Strict Transport Security)
        # Only enable in production with HTTPS
        # response.headers["Strict-Transport-Security"] = (
        #     "max-age=31536000; includeSubDomains; preload"
        # )
        
        # Content Security Policy (CSP)
        # Customize based on your application needs
        # response.headers["Content-Security-Policy"] = (
        #     "default-src 'self'; "
        #     "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        #     "style-src 'self' 'unsafe-inline'; "
        #     "img-src 'self' data: https:; "
        #     "font-src 'self' data:; "
        #     "connect-src 'self'"
        # )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Prevent caching sensitive data
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

