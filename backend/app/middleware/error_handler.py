"""
Error Handler Middleware
Global error handling for all exceptions.
"""

import logging
import traceback
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling all exceptions globally.
    Provides consistent error responses and logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and handle any exceptions.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response with proper error handling
        """
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # FastAPI HTTPException - let it pass through
            logger.warning(
                f"HTTP Exception: {exc.status_code} - {exc.detail}",
                extra={
                    "status_code": exc.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code,
                    "path": request.url.path
                }
            )
            
        except SQLAlchemyError as exc:
            # Database errors
            logger.error(
                f"Database Error: {str(exc)}",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Database operation failed",
                    "type": "SQLAlchemyError",
                    "status_code": 500,
                    "path": request.url.path
                }
            )
            
        except ValueError as exc:
            # Value errors (validation, etc.)
            logger.warning(
                f"Value Error: {str(exc)}",
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": str(exc),
                    "type": "ValueError",
                    "status_code": 400,
                    "path": request.url.path
                }
            )
            
        except Exception as exc:
            # Catch-all for unexpected errors
            logger.error(
                f"Unhandled Exception: {type(exc).__name__}: {str(exc)}",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "type": type(exc).__name__,
                    "status_code": 500,
                    "path": request.url.path,
                    # Include details only in development
                    # "details": str(exc) if settings.DEBUG else None
                }
            )

