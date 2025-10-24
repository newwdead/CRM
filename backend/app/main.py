"""
FastAPI Business Card CRM - Main Application
Optimized version with modular architecture
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import os
import time
import logging

# Local imports
from .database import engine, Base
from .models import Contact
from .api import api_router
from .middleware import (
    ErrorHandlerMiddleware,
    SecurityHeadersMiddleware
)
from .middleware.enhanced_logging import EnhancedLoggingMiddleware
from .middleware.security import security_headers_middleware
from .middleware.rate_limit import enhanced_rate_limit, rate_limit_handler

# Configure structured logging
from .core.logging_config import setup_logging, get_logger

# Setup structured JSON logging (set json_logs=False for development)
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "true"
)
logger = get_logger(__name__)

# Initialize Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("TESTING") != "true"
)


def init_db_with_retry(max_retries: int = 30, delay: float = 1.0) -> bool:
    """
    Initialize database with retry logic.
    Handles PostgreSQL container startup delays.
    """
    last_err = None
    for i in range(max_retries):
        try:
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Run lightweight migrations for new columns
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS comment VARCHAR;
                """))
                conn.execute(text("""
                    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS uid VARCHAR UNIQUE;
                """))
                conn.execute(text("""
                    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS website VARCHAR;
                """))
                conn.execute(text("""
                    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS photo_path VARCHAR;
                """))
                conn.execute(text("""
                    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS ocr_raw VARCHAR;
                """))
                conn.commit()
            
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            last_err = e
            logger.warning(f"Database init attempt {i+1}/{max_retries} failed: {e}")
            time.sleep(delay)
    
    logger.error(f"Database init failed after {max_retries} retries: {last_err}")
    return False


def backfill_uids():
    """Backfill missing UIDs for existing contacts"""
    import uuid
    from sqlalchemy.orm import sessionmaker
    
    try:
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            missing = session.query(Contact).filter(
                (Contact.uid == None) | (Contact.uid == '')
            ).all()
            
            updated = 0
            for contact in missing:
                contact.uid = uuid.uuid4().hex
                updated += 1
            
            if updated:
                session.commit()
                logger.info(f"Backfilled UID for {updated} contact(s)")
    except Exception as e:
        logger.error(f"UID backfill failed: {e}")


# Security validation on startup
def validate_security_config():
    """Validate security configuration on startup"""
    import secrets as sec
    
    secret_key = os.getenv("SECRET_KEY", "")
    weak_keys = [
        "your-secret-key-change-this-in-production",
        "your-secret-key-change-in-production",
        "secret",
        "password",
        "123456"
    ]
    
    if not secret_key or any(weak in secret_key.lower() for weak in weak_keys):
        logger.error(
            "⚠️  SECURITY WARNING: Weak or default SECRET_KEY detected! "
            "Generate a strong key with: "
            "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Cannot start in production with weak SECRET_KEY!")
        else:
            logger.warning("Starting with weak key (development mode only)")
    
    if len(secret_key) < 32:
        logger.warning(f"SECRET_KEY too short ({len(secret_key)} chars). Recommended: 32+ chars")


# Initialize database on startup
init_db_with_retry()
backfill_uids()
validate_security_config()


# ============================================================================
# Lifespan Context Manager (replaces deprecated @app.on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 FastAPI Business Card CRM starting...")
    logger.info(f"📦 Version: 4.2.0")
    logger.info(f"🔧 Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"🗄️  Database: {os.getenv('DATABASE_URL', 'sqlite')[:30]}...")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("👋 FastAPI Business Card CRM shutting down...")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="BizCard CRM API",
    description="Business Card Management with OCR, Duplicate Detection, and CRM features",
    version="4.6.0",  # Critical Fixes: Admin navigation + modernization
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # Use lifespan context manager instead of on_event
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False
)

# Rate limiter configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files (uploaded business cards)
os.makedirs('uploads', exist_ok=True)
app.mount('/files', StaticFiles(directory='uploads'), name='files')

# CORS Middleware
# Allow origins from environment variable or use defaults
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default allowed origins
    allowed_origins = [
        # Production
        "https://ibbase.ru",
        "https://www.ibbase.ru",
        "https://api.ibbase.ru",
        # Development (only if not production)
        *([
            "http://localhost:3000",
            "http://localhost:80",
            "http://127.0.0.1:3000"
        ] if os.getenv("ENVIRONMENT") != "production" else [])
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Custom Middleware (order matters!)
# 1. Enhanced Logging with structured JSON (first to capture all requests)
app.add_middleware(EnhancedLoggingMiddleware)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Error Handler (last to catch all errors)
app.add_middleware(ErrorHandlerMiddleware)

# Include API routers (modular structure)
# Note: Nginx already handles /api/ prefix and proxies to / on backend
app.include_router(api_router)


# ============================================================================
# Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "BizCard CRM API",
        "version": "4.2.0",
        "python": "3.11",
        "fastapi": "0.115.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

