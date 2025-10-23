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
import os
import time
import logging

# Local imports
from .database import engine, Base
from .models import Contact
from .api import api_router
from .middleware import (
    ErrorHandlerMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# Initialize database on startup
init_db_with_retry()
backfill_uids()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="BizCard CRM API",
    description="Business Card Management with OCR, Duplicate Detection, and CRM features",
    version="3.1.6",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production
        "https://ibbase.ru",
        "https://www.ibbase.ru",
        "https://api.ibbase.ru",
        "https://monitoring.ibbase.ru",
        "http://ibbase.ru",
        "http://www.ibbase.ru",
        # Development
        "http://localhost:3000",
        "http://localhost:80",
        "http://frontend:80",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Custom Middleware (order matters!)
# 1. Request Logging (first to capture all requests)
app.add_middleware(RequestLoggingMiddleware)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Error Handler (last to catch all errors)
app.add_middleware(ErrorHandlerMiddleware)

# Include API routers (modular structure)
app.include_router(api_router)


# ============================================================================
# Application Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 60)
    logger.info("🚀 FastAPI Business Card CRM starting...")
    logger.info(f"📦 Version: 2.16")
    logger.info(f"🔧 Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"🗄️  Database: {os.getenv('DATABASE_URL', 'sqlite')[:30]}...")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 FastAPI Business Card CRM shutting down...")


# ============================================================================
# Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "BizCard CRM API",
        "version": "2.16",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

