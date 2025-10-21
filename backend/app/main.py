from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update, text
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict
from datetime import timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge, Histogram
from .database import engine, Base, get_db
from .models import Contact, AppSetting, User
from .ocr_providers import OCRManager
from . import ocr_utils  # Enhanced OCR parsing
from . import qr_utils  # QR code scanning
from . import duplicate_utils  # Duplicate detection
from . import auth_utils
from . import image_processing  # Image preprocessing and multi-card detection
from .auth_utils import get_current_active_user, get_current_admin_user
from . import schemas
import io, csv, tempfile, pandas as pd, os, uuid, json, requests, time, subprocess, glob
from pathlib import Path
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация OCR Manager
ocr_manager = OCRManager()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics (imported from core.metrics)
from .core.metrics import (
    ocr_processing_counter,
    ocr_processing_time,
    qr_scan_counter,
    contacts_total,
    contacts_created_counter,
    users_total,
    auth_attempts_counter,
    telegram_messages_counter
)

def init_db_with_retry(max_retries: int = 30, delay: float = 1.0):
    last_err = None
    for i in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            # Lightweight migrations for new columns
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
            print("Database initialized and schema ensured")
            return True
        except Exception as e:
            last_err = e
            time.sleep(delay)
    print(f"Database init failed after retries: {last_err}")
    return False

# Initialize DB on import (container start)
init_db_with_retry()

def backfill_uids_safe():
    try:
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as s:
            missing = s.query(Contact).filter((Contact.uid == None) | (Contact.uid == '')).all()
            updated = 0
            for c in missing:
                c.uid = uuid.uuid4().hex
                updated += 1
            if updated:
                s.commit()
                print(f"Backfilled UID for {updated} contact(s)")
    except Exception as e:
        print(f"UID backfill failed: {e}")

def init_default_users():
    """Initialize default admin user if no users exist."""
    try:
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as db:
            auth_utils.init_default_admin(db)
    except Exception as e:
        print(f"User initialization failed: {e}")

backfill_uids_safe()
init_default_users()

# ============================================================================
# AUDIT LOG HELPER
# ============================================================================

def create_audit_log(
    db: Session,
    contact_id: Optional[int],
    user: User,
    action: str,
    entity_type: str = 'contact',
    changes: Optional[dict] = None
):
    """Create an audit log entry."""
    from .models import AuditLog
    import json
    
    audit_entry = AuditLog(
        contact_id=contact_id,
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        entity_type=entity_type,
        changes=json.dumps(changes, ensure_ascii=False) if changes else None
    )
    db.add(audit_entry)
    # Note: Commit should be done by the caller

# --- Image utils ---
def downscale_image_bytes(data: bytes, max_side: int = 2000) -> bytes:
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert('RGB')
            # downscale in-place keeping aspect ratio
            im.thumbnail((max_side, max_side))
            out = io.BytesIO()
            im.save(out, format='JPEG', quality=90)
            return out.getvalue()
    except Exception:
        # if Pillow cannot open, return original
        return data

def create_thumbnail(image_path: str, size: tuple = (200, 200), quality: int = 85) -> str:
    """
    Create a thumbnail for the given image.
    
    Args:
        image_path: Path to the original image
        size: Thumbnail size (width, height), default (200, 200)
        quality: JPEG quality (1-100), default 85
    
    Returns:
        Path to the created thumbnail
    """
    try:
        # Generate thumbnail filename
        path_obj = Path(image_path)
        thumb_name = f"{path_obj.stem}_thumb{path_obj.suffix}"
        thumb_path = path_obj.parent / thumb_name
        
        # Open image and create thumbnail
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode:
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(str(thumb_path), 'JPEG', quality=quality, optimize=True)
            
        logger.info(f"Thumbnail created: {thumb_path}")
        return str(thumb_path)
    
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        # Return original path if thumbnail creation fails
        return image_path

# Pydantic models for validation
class ContactCreate(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    comment: Optional[str] = None
    website: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not any(c.isdigit() for c in v):
            raise ValueError('Phone must contain at least one digit')
        return v

class ContactUpdate(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    comment: Optional[str] = None
    website: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not any(c.isdigit() for c in v):
            raise ValueError('Phone must contain at least one digit')
        return v

app = FastAPI(title="BizCard CRM")

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

os.makedirs('uploads', exist_ok=True)
app.mount('/files', StaticFiles(directory='uploads'), name='files')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production domains
        "https://ibbase.ru",
        "https://www.ibbase.ru",
        "https://api.ibbase.ru",
        "https://monitoring.ibbase.ru",
        "http://ibbase.ru",
        "http://www.ibbase.ru",
        # Development/localhost
        "http://localhost:3000",
        "http://localhost:80", 
        "http://frontend:80",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ============================================================================
# Include API Routers (New Modular Structure)
# ============================================================================
from .api import api_router

app.include_router(api_router)

# Version endpoint (frontend calls /api/version; nginx strips /api/ and forwards to /version)
@app.get('/version')
def get_version():
    return {
        'version': os.environ.get('APP_VERSION', 'unknown'),
        'commit': os.environ.get('APP_COMMIT', ''),
        'message': os.environ.get('APP_MESSAGE', ''),
    }

# --- Health ---
@app.get('/health')
def health():
    return {'status':'ok'}

# --- OCR Providers Info ---
@app.get('/ocr/providers')
def get_ocr_providers():
    """Получить информацию о доступных OCR провайдерах"""
    return {
        'available': ocr_manager.get_available_providers(),
        'details': ocr_manager.get_provider_info()
    }

# --- Settings helpers ---
def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default

def set_setting(db: Session, key: str, value: Optional[str]):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
        db.add(row)
    db.commit()

class TelegramSettings(BaseModel):
    enabled: bool = False
    token: Optional[str] = None
    allowed_chats: Optional[str] = None  # comma-separated chat IDs
    provider: Optional[str] = 'auto'  # 'auto' | 'tesseract' | 'parsio' | 'google'

@app.get('/settings/telegram')
def get_telegram_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return {
        'enabled': get_setting(db, 'tg.enabled', 'false') == 'true',
        'token': get_setting(db, 'tg.token', None),
        'allowed_chats': get_setting(db, 'tg.allowed_chats', ''),
        'provider': get_setting(db, 'tg.provider', 'auto') or 'auto',
    }

@app.put('/settings/telegram')
def put_telegram_settings(
    data: TelegramSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Only admin can change settings
):
    set_setting(db, 'tg.enabled', 'true' if data.enabled else 'false')
    set_setting(db, 'tg.token', (data.token or '').strip() or None)
    set_setting(db, 'tg.allowed_chats', (data.allowed_chats or '').strip())
    set_setting(db, 'tg.provider', (data.provider or 'auto'))
    return {'ok': True}

# --- Telegram webhook ---
@app.post('/telegram/webhook')
def telegram_webhook(update: dict = Body(...), db: Session = Depends(get_db)):
    try:
        # Check enabled and token present
        if get_setting(db, 'tg.enabled', 'false') != 'true':
            return {'ignored': 'disabled'}
        token = get_setting(db, 'tg.token', None)
        if not token:
            raise HTTPException(status_code=400, detail='Telegram token not configured')

        message = update.get('message') or update.get('edited_message')
        if not message:
            return {'ignored': 'no_message'}

        chat_id = str(message.get('chat', {}).get('id')) if message.get('chat') else None
        allowed = (get_setting(db, 'tg.allowed_chats', '') or '').strip()
        if allowed:
            allowed_set = {x.strip() for x in allowed.split(',') if x.strip()}
            if chat_id not in allowed_set:
                return {'ignored': 'chat_not_allowed'}

        photos = message.get('photo') or []
        if not photos:
            return {'ignored': 'no_photo'}

        # choose largest photo
        best = max(photos, key=lambda p: (p.get('width', 0) or 0) * (p.get('height', 0) or 0))
        file_id = best.get('file_id')
        if not file_id:
            raise HTTPException(status_code=400, detail='No file_id in photo')

        # get file path
        api = f'https://api.telegram.org/bot{token}'
        r = requests.get(f'{api}/getFile', params={'file_id': file_id}, timeout=15)
        r.raise_for_status()
        file_path = r.json().get('result', {}).get('file_path')
        if not file_path:
            raise HTTPException(status_code=400, detail='Cannot get file_path')

        # download file bytes
        file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'
        img_res = requests.get(file_url, timeout=30)
        img_res.raise_for_status()
        content = img_res.content

        # STEP 0: Image preprocessing - detect and split multiple cards
        logger.info("Telegram: Processing image with auto_crop=True, detect_multi=True")
        processed_cards = image_processing.process_business_card_image(
            content,
            auto_crop=True,
            detect_multi=True,
            enhance=False
        )
        
        logger.info(f"Telegram: {len(processed_cards)} card(s) detected")
        
        # Process each detected card
        created_contacts = []
        provider = get_setting(db, 'tg.provider', 'auto') or 'auto'
        
        for idx, card_bytes in enumerate(processed_cards[:5]):  # Limit to 5 cards
            logger.info(f"Telegram: Processing card {idx + 1}/{len(processed_cards)}")
            
            # Save card to uploads
            card_safe_name = f"{uuid.uuid4().hex}_tg_card{idx+1 if len(processed_cards) > 1 else ''}_{os.path.basename(file_path)}"
            card_save_path = os.path.join('uploads', card_safe_name)
            with open(card_save_path, 'wb') as f:
                f.write(card_bytes)
            
            # Create thumbnail
            card_thumbnail_path = create_thumbnail(card_save_path, size=(200, 200), quality=85)
            card_thumbnail_name = os.path.basename(card_thumbnail_path)
            
            # Process card using helper function
            card_data = process_single_card(
                card_bytes,
                card_safe_name,
                card_thumbnail_name,
                provider,
                os.path.basename(file_path),
                db
            )
            
            if card_data:
                created_contacts.append(card_data)
                logger.info(f"Telegram: Card {idx + 1} created, contact_id={card_data['id']}")
        
        # Return result
        if len(created_contacts) == 0:
            raise HTTPException(status_code=400, detail='No cards could be processed')
        elif len(created_contacts) == 1:
            return {'created_id': created_contacts[0]['id']}
        else:
            return {
                'created_ids': [c['id'] for c in created_contacts],
                'count': len(created_contacts),
                'message': f'{len(created_contacts)} business cards detected and processed'
            }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# --- CRUD ---
@app.get('/contacts/', response_model=schemas.PaginatedContactsResponse)
def list_contacts(
    q: str = Query(None, description="Search query (full-text search across all fields)"),
    company: str = Query(None, description="Filter by company"),
    position: str = Query(None, description="Filter by position"),
    tags: str = Query(None, description="Filter by tag names (comma-separated)"),
    groups: str = Query(None, description="Filter by group names (comma-separated)"),
    sort_by: str = Query('id', description="Sort field: id, full_name, company, position"),
    sort_order: str = Query('desc', description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get paginated list of contacts with advanced search and filtering.
    
    Parameters:
    - q: Full-text search across all fields (name, company, position, email, phone)
    - company: Filter by company (case-insensitive partial match)
    - position: Filter by position (case-insensitive partial match)
    - tags: Filter by tag names (comma-separated, e.g., "vip,client")
    - groups: Filter by group names (comma-separated, e.g., "partners,customers")
    - sort_by: Field to sort by (id, full_name, company, position)
    - sort_order: Sort direction (asc, desc)
    - page: Page number (starts from 1)
    - limit: Items per page (1-100, default 20)
    """
    from .models import Tag, Group
    
    query = db.query(Contact)
    
    # Full-text search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Contact.full_name.ilike(search_term)) |
            (Contact.company.ilike(search_term)) |
            (Contact.position.ilike(search_term)) |
            (Contact.email.ilike(search_term)) |
            (Contact.phone.ilike(search_term)) |
            (Contact.website.ilike(search_term)) |
            (Contact.address.ilike(search_term))
        )
    
    # Filter by company
    if company:
        query = query.filter(Contact.company.ilike(f"%{company}%"))
    
    # Filter by position
    if position:
        query = query.filter(Contact.position.ilike(f"%{position}%"))
    
    # Filter by tags
    if tags:
        tag_names = [name.strip() for name in tags.split(',') if name.strip()]
        if tag_names:
            # Get tag IDs for the given names
            tag_records = db.query(Tag).filter(Tag.name.in_(tag_names)).all()
            tag_ids = [tag.id for tag in tag_records]
            
            if tag_ids:
                # Filter contacts that have ANY of the specified tags
                query = query.filter(Contact.tags.any(Tag.id.in_(tag_ids)))
    
    # Filter by groups
    if groups:
        group_names = [name.strip() for name in groups.split(',') if name.strip()]
        if group_names:
            # Get group IDs for the given names
            group_records = db.query(Group).filter(Group.name.in_(group_names)).all()
            group_ids = [group.id for group in group_records]
            
            if group_ids:
                # Filter contacts that have ANY of the specified groups
                query = query.filter(Contact.groups.any(Group.id.in_(group_ids)))
    
    # Sorting
    sort_field = getattr(Contact, sort_by, Contact.id)
    if sort_order.lower() == 'asc':
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Get total count before pagination
    total = query.count()
    
    # Calculate pagination
    pages = (total + limit - 1) // limit  # Ceiling division
    offset = (page - 1) * limit
    
    # Apply pagination
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

@app.get('/contacts/search/')
def search_contacts(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results (1-50)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fast global search for SearchOverlay (Ctrl+K).
    Searches across names, company, position, email, phone.
    Returns minimal data for quick results.
    """
    search_term = f"%{q}%"
    
    # Search with relevance ranking
    contacts = db.query(Contact).filter(
        (Contact.full_name.ilike(search_term)) |
        (Contact.first_name.ilike(search_term)) |
        (Contact.last_name.ilike(search_term)) |
        (Contact.company.ilike(search_term)) |
        (Contact.position.ilike(search_term)) |
        (Contact.email.ilike(search_term)) |
        (Contact.phone.ilike(search_term))
    ).limit(limit).all()
    
    return {
        "items": contacts,
        "total": len(contacts)
    }


@app.get('/duplicates/')
def find_duplicate_contacts(
    threshold: float = Query(0.6, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find potential duplicate contacts.
    Returns groups of similar contacts with similarity scores.
    
    Args:
        threshold: Minimum similarity score (default 0.6)
    
    Returns:
        List of duplicate groups with contacts and scores
    """
    try:
        # Get all contacts
        contacts = db.query(Contact).all()
        
        # Convert to dicts for duplicate_utils
        contacts_data = []
        for c in contacts:
            contact_dict = {
                'id': c.id,
                'uid': c.uid,
                'full_name': c.full_name,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'middle_name': c.middle_name,
                'company': c.company,
                'position': c.position,
                'department': c.department,
                'email': c.email,
                'phone': c.phone,
                'phone_mobile': c.phone_mobile,
                'phone_work': c.phone_work,
                'address': c.address,
                'website': c.website,
                'tags': [{'id': t.id, 'name': t.name} for t in c.tags],
                'groups': [{'id': g.id, 'name': g.name} for g in c.groups],
            }
            contacts_data.append(contact_dict)
        
        # Find duplicates
        duplicates = duplicate_utils.find_duplicates(contacts_data, threshold=threshold)
        
        logger.info(f"Found {len(duplicates)} duplicate groups with threshold {threshold}")
        
        return {
            "duplicates": duplicates,
            "total_groups": len(duplicates),
            "threshold": threshold
        }
        
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding duplicates: {str(e)}")


@app.post('/duplicates/merge')
def merge_duplicate_contacts(
    primary_id: int = Body(..., description="Primary contact ID (will be kept)"),
    secondary_id: int = Body(..., description="Secondary contact ID (will be deleted)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Merge two duplicate contacts.
    Primary contact is kept and updated with data from secondary.
    Secondary contact is deleted.
    
    Operation is logged in audit log.
    """
    try:
        # Get contacts
        primary = db.query(Contact).filter(Contact.id == primary_id).first()
        secondary = db.query(Contact).filter(Contact.id == secondary_id).first()
        
        if not primary:
            raise HTTPException(status_code=404, detail=f"Primary contact {primary_id} not found")
        if not secondary:
            raise HTTPException(status_code=404, detail=f"Secondary contact {secondary_id} not found")
        
        if primary.id == secondary.id:
            raise HTTPException(status_code=400, detail="Cannot merge contact with itself")
        
        # Convert to dicts for merging
        primary_dict = {
            'id': primary.id,
            'full_name': primary.full_name,
            'first_name': primary.first_name,
            'last_name': primary.last_name,
            'middle_name': primary.middle_name,
            'company': primary.company,
            'position': primary.position,
            'department': primary.department,
            'email': primary.email,
            'phone': primary.phone,
            'phone_mobile': primary.phone_mobile,
            'phone_work': primary.phone_work,
            'fax': primary.fax,
            'address': primary.address,
            'website': primary.website,
            'birthday': primary.birthday,
            'source': primary.source,
            'status': primary.status,
            'priority': primary.priority,
            'comment': primary.comment,
            'tags': primary.tags,
            'groups': primary.groups,
        }
        
        secondary_dict = {
            'id': secondary.id,
            'full_name': secondary.full_name,
            'first_name': secondary.first_name,
            'last_name': secondary.last_name,
            'middle_name': secondary.middle_name,
            'company': secondary.company,
            'position': secondary.position,
            'department': secondary.department,
            'email': secondary.email,
            'phone': secondary.phone,
            'phone_mobile': secondary.phone_mobile,
            'phone_work': secondary.phone_work,
            'fax': secondary.fax,
            'address': secondary.address,
            'website': secondary.website,
            'birthday': secondary.birthday,
            'source': secondary.source,
            'status': secondary.status,
            'priority': secondary.priority,
            'comment': secondary.comment,
            'tags': secondary.tags,
            'groups': secondary.groups,
        }
        
        # Merge data
        merged_data = duplicate_utils.merge_contacts(primary_dict, secondary_dict)
        
        # Apply updates to primary contact
        for key, value in merged_data.items():
            if key not in ['tag_ids', 'group_ids']:
                setattr(primary, key, value)
        
        # Merge tags
        if 'tag_ids' in merged_data:
            from .models import Tag
            primary.tags = db.query(Tag).filter(Tag.id.in_(merged_data['tag_ids'])).all()
        
        # Merge groups
        if 'group_ids' in merged_data:
            from .models import Group
            primary.groups = db.query(Group).filter(Group.id.in_(merged_data['group_ids'])).all()
        
        # Create audit log entry
        from .models import AuditLog
        audit_entry = AuditLog(
            contact_id=primary.id,
            action='merge',
            user_id=current_user.id,
            changes=json.dumps({
                'merged_from': secondary.id,
                'merged_from_uid': secondary.uid,
                'merged_data': merged_data
            }, ensure_ascii=False)
        )
        db.add(audit_entry)
        
        # Delete secondary contact
        db.delete(secondary)
        
        # Commit changes
        db.commit()
        db.refresh(primary)
        
        # Update metrics
        contacts_total.set(db.query(Contact).count())
        
        logger.info(f"Successfully merged contact {secondary_id} into {primary_id} by user {current_user.username}")
        
        return {
            "success": True,
            "primary_id": primary.id,
            "merged_contact": primary,
            "message": f"Contact {secondary_id} merged into {primary_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error merging contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Error merging contacts: {str(e)}")


@app.get('/contacts/{contact_id}')
def get_contact_by_id(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a single contact by ID.
    Requires valid JWT token.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return contact

@app.get('/contacts/{contact_id}/ocr-blocks')
def get_contact_ocr_blocks(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get OCR bounding boxes and text blocks for a contact's image.
    Returns coordinates and text for visual editing.
    """
    from . import tesseract_boxes
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    if not contact.photo_path:
        raise HTTPException(status_code=400, detail='Contact has no image')
    
    # Read image file
    image_path = os.path.join('uploads', contact.photo_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail='Image file not found')
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Get Tesseract language from settings
        tesseract_langs = get_setting(db, 'TESSERACT_LANGS', 'rus+eng')
        
        # Extract blocks
        result = tesseract_boxes.get_text_blocks(image_bytes, lang=tesseract_langs)
        
        # Group into lines for easier visualization
        lines = tesseract_boxes.group_blocks_by_line(result['blocks'])
        
        return {
            'contact_id': contact_id,
            'image_width': result['image_width'],
            'image_height': result['image_height'],
            'blocks': result['blocks'],  # Word-level blocks
            'lines': lines,  # Line-level grouped blocks
            'current_data': {
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'middle_name': contact.middle_name,
                'company': contact.company,
                'position': contact.position,
                'email': contact.email,
                'phone': contact.phone,
                'phone_mobile': contact.phone_mobile,
                'phone_work': contact.phone_work,
                'phone_additional': contact.phone_additional,
                'address': contact.address,
                'address_additional': contact.address_additional,
                'website': contact.website
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting OCR blocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract OCR blocks: {str(e)}")


@app.post('/contacts/{contact_id}/ocr-corrections')
def save_ocr_correction(
    contact_id: int,
    correction_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save OCR correction for training purposes.
    Stores original OCR text, corrected text, and field assignment.
    """
    from .models import OCRCorrection
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Create correction record
    correction = OCRCorrection(
        contact_id=contact_id,
        user_id=current_user.id,
        original_text=correction_data.get('original_text', ''),
        original_box=json.dumps(correction_data.get('original_box', {})),
        original_confidence=correction_data.get('original_confidence'),
        corrected_text=correction_data.get('corrected_text', ''),
        corrected_field=correction_data.get('corrected_field', ''),
        image_path=contact.photo_path,
        ocr_provider=correction_data.get('ocr_provider', 'tesseract'),
        language=correction_data.get('language', 'rus+eng')
    )
    
    db.add(correction)
    db.commit()
    
    logger.info(f"OCR correction saved: {correction_data.get('original_text')} → {correction_data.get('corrected_text')} (field: {correction_data.get('corrected_field')})")
    
    return {
        'success': True,
        'message': 'Correction saved for training',
        'correction_id': correction.id
    }


@app.get('/contacts/uid/{uid}')
def get_contact_by_uid(
    uid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    contact = db.query(Contact).filter(Contact.uid == uid).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    return contact

@app.post('/contacts/')
def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from .phone_utils import format_phone_number
    
    payload = data.dict()
    if not payload.get('uid'):
        payload['uid'] = uuid.uuid4().hex
    
    # Format phone numbers
    if payload.get('phone'):
        payload['phone'] = format_phone_number(payload['phone'])
    if payload.get('phone_mobile'):
        payload['phone_mobile'] = format_phone_number(payload['phone_mobile'])
    if payload.get('phone_work'):
        payload['phone_work'] = format_phone_number(payload['phone_work'])
    if payload.get('phone_additional'):
        payload['phone_additional'] = format_phone_number(payload['phone_additional'])
    
    contact = Contact(**payload)
    db.add(contact)
    db.flush()  # Get ID without committing
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='created',
        entity_type='contact',
        changes=payload
    )
    
    db.commit()
    db.refresh(contact)
    
    # Update contact metrics
    contacts_created_counter.inc()
    contacts_total.set(db.query(Contact).count())
    
    # Auto-detect duplicates if enabled
    try:
        duplicate_enabled = get_system_setting(db, 'duplicate_detection_enabled', 'true')
        if duplicate_enabled.lower() == 'true':
            threshold = float(get_system_setting(db, 'duplicate_similarity_threshold', '0.75'))
            
            # Get existing contacts for comparison
            existing_contacts = db.query(Contact).filter(Contact.id != contact.id).all()
            
            # Convert to dict for comparison
            contact_dict = {
                'id': contact.id,
                'full_name': contact.full_name,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'middle_name': contact.middle_name,
                'email': contact.email,
                'phone': contact.phone,
                'phone_mobile': contact.phone_mobile,
                'phone_work': contact.phone_work,
                'company': contact.company,
                'position': contact.position,
            }
            
            existing_dicts = [{
                'id': c.id,
                'full_name': c.full_name,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'middle_name': c.middle_name,
                'email': c.email,
                'phone': c.phone,
                'phone_mobile': c.phone_mobile,
                'phone_work': c.phone_work,
                'company': c.company,
                'position': c.position,
            } for c in existing_contacts]
            
            # Find duplicates
            duplicates = duplicate_utils.find_duplicates_for_new_contact(contact_dict, existing_dicts, threshold)
            
            # Save duplicates to database
            for existing_contact_dict, score, field_scores in duplicates:
                existing_id = existing_contact_dict['id']
                id1, id2 = sorted([contact.id, existing_id])
                
                # Check if already exists
                existing_dup = db.query(DuplicateContact).filter(
                    (DuplicateContact.contact_id_1 == id1) & (DuplicateContact.contact_id_2 == id2)
                ).first()
                
                if not existing_dup:
                    new_dup = DuplicateContact(
                        contact_id_1=id1,
                        contact_id_2=id2,
                        similarity_score=score,
                        match_fields=field_scores,
                        status='pending',
                        auto_detected=True
                    )
                    db.add(new_dup)
            
            db.commit()
    except Exception as e:
        # Don't fail contact creation if duplicate detection fails
        print(f"Duplicate detection error: {e}")
    
    return contact

@app.put('/contacts/{contact_id}')
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from .phone_utils import format_phone_number
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    
    update_data = data.dict(exclude_unset=True)
    
    # Format phone numbers
    if 'phone' in update_data and update_data['phone']:
        update_data['phone'] = format_phone_number(update_data['phone'])
    if 'phone_mobile' in update_data and update_data['phone_mobile']:
        update_data['phone_mobile'] = format_phone_number(update_data['phone_mobile'])
    if 'phone_work' in update_data and update_data['phone_work']:
        update_data['phone_work'] = format_phone_number(update_data['phone_work'])
    if 'phone_additional' in update_data and update_data['phone_additional']:
        update_data['phone_additional'] = format_phone_number(update_data['phone_additional'])
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='updated',
        entity_type='contact',
        changes=update_data
    )
    
    for k, v in update_data.items():
        if hasattr(contact, k):
            setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    return contact

@app.delete('/contacts/{contact_id}')
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    
    # Audit log (before deletion)
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='deleted',
        entity_type='contact',
        changes={'full_name': contact.full_name, 'company': contact.company}
    )
    
    db.delete(contact)
    db.commit()
    return {'deleted': contact_id}


# ==============================================================================
# Helper function for processing a single business card
# ==============================================================================

def process_single_card(card_bytes: bytes, safe_name: str, thumbnail_name: str, 
                       provider: str, filename: str, db: Session) -> dict:
    """
    Process a single business card image (QR + OCR).
    Returns contact data dict or None on failure.
    """
    try:
        # STEP 1: Try QR code scanning first
        data = None
        raw_json = None
        raw_text = ""
        recognition_method = None
        
        logger.info("Attempting QR code scan...")
        qr_data = qr_utils.process_image_with_qr(card_bytes)
        
        if qr_data and any(qr_data.values()):
            # QR code found
            data = qr_data
            recognition_method = 'qr_code'
            raw_json = json.dumps({
                'method': 'qr_code',
                'data': qr_data
            }, ensure_ascii=False)
            qr_scan_counter.labels(status='success').inc()
            logger.info("QR code extracted successfully")
        else:
            # No QR code - fallback to OCR
            qr_scan_counter.labels(status='not_found').inc()
            logger.info("No QR code found, falling back to OCR...")
            
            # Prepare for OCR
            ocr_input = downscale_image_bytes(card_bytes, max_side=2000)
            preferred = None if provider == 'auto' else provider
            
            try:
                start_time = time.time()
                ocr_result = ocr_manager.recognize(
                    ocr_input,
                    filename=filename,
                    preferred_provider=preferred
                )
                processing_time = time.time() - start_time
                
                # Update metrics
                used_provider = ocr_result['provider']
                ocr_processing_time.labels(provider=used_provider).observe(processing_time)
                ocr_processing_counter.labels(provider=used_provider, status='success').inc()
                
                data = ocr_result['data']
                recognition_method = ocr_result['provider']
                raw_text = ocr_result.get('raw_text', '')  # Get raw text for enhanced parsing
                raw_json = json.dumps({
                    'method': 'ocr',
                    'provider': ocr_result['provider'],
                    'confidence': ocr_result.get('confidence', 0),
                    'raw_data': ocr_result.get('raw_data'),
                    'raw_text': raw_text,
                }, ensure_ascii=False)
                
                logger.info(f"OCR successful with {used_provider}, confidence: {ocr_result.get('confidence', 0)}")
                
            except Exception as e:
                ocr_processing_counter.labels(provider=preferred or 'auto', status='failed').inc()
                logger.error(f"OCR failed: {e}")
                return None
        
        # Validate results
        if not data or not any(data.values()):
            logger.warning("No data extracted from card")
            return None
        
        # Enhance data with improved parsing (pass raw_text for phone/address extraction)
        data = ocr_utils.enhance_ocr_result(data, raw_text=raw_text)
        
        # Attach metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        
        # Save to database
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        logger.info(f"Contact created: {contact.id} ({filename})")
        
        # Return contact data
        return {
            "id": contact.id,
            "uid": contact.uid,
            "full_name": contact.full_name,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "middle_name": contact.middle_name,
            "company": contact.company,
            "position": contact.position,
            "email": contact.email,
            "phone": contact.phone,
            "phone_mobile": contact.phone_mobile,
            "phone_work": contact.phone_work,
            "phone_additional": contact.phone_additional,
            "address": contact.address,
            "address_additional": contact.address_additional,
            "website": contact.website,
            "photo_path": contact.photo_path,
            "thumbnail_path": contact.thumbnail_path,
            "recognition_method": recognition_method,
        }
        
    except Exception as e:
        logger.error(f"Error processing card: {e}")
        return None


# --- Upload OCR ---
@app.post('/upload/')
@limiter.limit("60/minute")  # 60 uploads per minute per IP
def upload_card(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
    auto_crop: bool = Query(True, description="Automatically crop business card boundaries"),
    detect_multi: bool = Query(True, description="Detect multiple cards in single image"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (20MB max)
        limit = 20 * 1024 * 1024
        head = file.file.read(limit + 1)
        if len(head) > limit:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 20MB")
        file.file.seek(0)
        
        # Read image content
        content = file.file.read()
        file.file.seek(0)
        
        # STEP 0: Image preprocessing - crop and detect multiple cards
        logger.info(f"Processing image with auto_crop={auto_crop}, detect_multi={detect_multi}")
        processed_cards = image_processing.process_business_card_image(
            content, 
            auto_crop=auto_crop,
            detect_multi=detect_multi,
            enhance=False  # Keep false to preserve original quality
        )
        
        logger.info(f"Image processing complete: {len(processed_cards)} card(s) detected")
        
        # If multiple cards detected, handle each one
        if len(processed_cards) > 1:
            logger.info(f"Multiple cards detected ({len(processed_cards)}), processing each separately")
            created_contacts = []
            
            for idx, card_bytes in enumerate(processed_cards[:5]):  # Limit to 5 cards
                logger.info(f"Processing card {idx + 1}/{len(processed_cards)}")
                
                # Save card to disk
                card_safe_name = f"{uuid.uuid4().hex}_card{idx+1}_{os.path.basename(file.filename or 'upload')}"
                card_save_path = os.path.join('uploads', card_safe_name)
                with open(card_save_path, 'wb') as f:
                    f.write(card_bytes)
                
                # Create thumbnail
                card_thumbnail_path = create_thumbnail(card_save_path, size=(200, 200), quality=85)
                card_thumbnail_name = os.path.basename(card_thumbnail_path)
                
                # Process card (QR + OCR)
                card_data = process_single_card(
                    card_bytes, 
                    card_safe_name, 
                    card_thumbnail_name,
                    provider, 
                    file.filename,
                    db
                )
                
                if card_data:
                    created_contacts.append(card_data)
            
            # Update metrics
            contacts_created_counter.inc(len(created_contacts))
            contacts_total.set(db.query(Contact).count())
            
            return {
                "message": f"{len(created_contacts)} business cards detected and processed",
                "contacts": created_contacts
            }
        
        # Single card - use processed image
        content = processed_cards[0]
        
        # Save processed file to disk
        safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload')}"
        save_path = os.path.join('uploads', safe_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # Create thumbnail (200x200, quality 85%)
        thumbnail_full_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_full_path)
        
        # Process single card (QR + OCR)
        contact_dict = process_single_card(
            content,
            safe_name,
            thumbnail_name,
            provider,
            file.filename,
            db
        )
        
        if not contact_dict:
            raise HTTPException(status_code=400, detail="No text could be extracted from the image (neither QR nor OCR)")
        
        # Update metrics
        contacts_created_counter.inc()
        contacts_total.set(db.query(Contact).count())
        
        return contact_dict
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# --- Batch Upload (ZIP) ---
@app.post('/batch-upload/')
@limiter.limit("10/hour")  # Limit batch uploads to prevent abuse
def batch_upload(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a ZIP archive containing multiple business card images.
    Returns a task ID for tracking progress.
    """
    try:
        # Validate file type
        if not file.content_type or 'zip' not in file.content_type.lower():
            if not file.filename or not file.filename.lower().endswith('.zip'):
                raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Check file size (100MB max for ZIP)
        limit = 100 * 1024 * 1024
        content = file.file.read(limit + 1)
        if len(content) > limit:
            raise HTTPException(status_code=400, detail="ZIP file too large. Maximum size is 100MB")
        
        # Save ZIP file
        zip_name = f"{uuid.uuid4().hex}_batch.zip"
        zip_path = os.path.join('uploads', zip_name)
        with open(zip_path, 'wb') as f:
            f.write(content)
        
        # Import Celery task
        from .tasks import process_batch_upload
        
        # Queue batch processing task
        task = process_batch_upload.delay(
            zip_path=zip_path,
            provider=provider,
            user_id=current_user.id
        )
        
        logger.info(f"Batch upload queued: {task.id} by user {current_user.username}")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Batch processing started. Use /batch-status/{task_id} to track progress."
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@app.get('/batch-status/{task_id}')
def get_batch_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of a batch processing task.
    """
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Waiting in queue...',
                'progress': 0
            }
        elif task.state == 'PROCESSING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': task.info.get('status', 'Processing...'),
                'progress': task.info.get('progress', 0),
                'total': task.info.get('total', 0),
                'processed': task.info.get('processed', 0),
                'current_file': task.info.get('current_file', '')
            }
        elif task.state == 'SUCCESS':
            result = task.result
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Completed',
                'progress': 100,
                'result': result
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Failed',
                'error': str(task.info)
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': str(task.info)
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


# --- WhatsApp Business API Integration ---
@app.get('/whatsapp/webhook')
def whatsapp_webhook_verify(
    request: Request,
    hub_mode: str = Query(None, alias='hub.mode'),
    hub_challenge: str = Query(None, alias='hub.challenge'),
    hub_verify_token: str = Query(None, alias='hub.verify_token')
):
    """
    Verify WhatsApp webhook.
    This endpoint is called by Meta/Facebook to verify webhook configuration.
    """
    from . import whatsapp_utils
    
    logger.info(f"WhatsApp webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == 'subscribe':
        if whatsapp_utils.verify_webhook_token(hub_verify_token):
            logger.info("WhatsApp webhook verified successfully")
            return int(hub_challenge)
        else:
            logger.warning("WhatsApp webhook verification failed: invalid token")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Invalid request")


@app.post('/whatsapp/webhook')
async def whatsapp_webhook_receive(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive WhatsApp webhook messages.
    Automatically processes business card images sent via WhatsApp.
    """
    from . import whatsapp_utils
    from .tasks import process_single_card
    
    try:
        body = await request.json()
        logger.info(f"WhatsApp webhook received: {json.dumps(body, indent=2)[:500]}")
        
        # Parse incoming message
        message_data = whatsapp_utils.parse_webhook_message(body)
        
        if not message_data:
            # Respond with 200 to acknowledge receipt
            return {"status": "ok", "message": "No processable message"}
        
        # Check message type
        if message_data['type'] == 'image':
            # Download image
            media_id = message_data['image']['id']
            image_data = whatsapp_utils.download_media(media_id)
            
            if image_data:
                # Queue processing task
                task = process_single_card.delay(
                    image_data=image_data,
                    filename=f"whatsapp_{message_data['id']}.jpg",
                    provider='auto',
                    user_id=None  # WhatsApp messages don't have associated user
                )
                
                logger.info(f"WhatsApp image queued for processing: task_id={task.id}")
                
                # Send confirmation message back
                from_number = message_data['from']
                confirmation_text = (
                    "✅ Визитка получена! Обрабатываем...\n"
                    "Контакт будет добавлен автоматически."
                )
                whatsapp_utils.send_text_message(from_number, confirmation_text)
                
                # Update Prometheus metrics
                telegram_messages_counter.labels(status='success').inc()
            else:
                logger.error("Failed to download WhatsApp media")
                telegram_messages_counter.labels(status='failed').inc()
        
        elif message_data['type'] == 'text':
            # Handle text commands
            text = message_data['text'].lower().strip()
            from_number = message_data['from']
            
            if text in ['/start', 'привет', 'hello', 'help']:
                help_text = (
                    "👋 Добро пожаловать в ibbase!\n\n"
                    "📤 Отправьте фото визитки, и я автоматически создам контакт.\n\n"
                    "Команды:\n"
                    "/start - Это сообщение\n"
                    "/help - Помощь\n"
                    "/status - Статус системы"
                )
                whatsapp_utils.send_text_message(from_number, help_text)
            
            elif text == '/status':
                # Get system status
                contacts_count = db.query(Contact).count()
                status_text = (
                    f"📊 Статус системы:\n\n"
                    f"✅ Система работает\n"
                    f"📇 Контактов в базе: {contacts_count}\n"
                    f"🤖 Готов обрабатывать визитки!"
                )
                whatsapp_utils.send_text_message(from_number, status_text)
            
            else:
                whatsapp_utils.send_text_message(
                    from_number,
                    "Отправьте фото визитки для автоматического создания контакта."
                )
        
        # Acknowledge receipt
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        telegram_messages_counter.labels(status='failed').inc()
        # Still return 200 to avoid webhook retry storms
        return {"status": "error", "message": str(e)}


@app.post('/whatsapp/send')
def whatsapp_send_message(
    to: str = Body(..., description="Recipient phone number"),
    message: str = Body(..., description="Message text"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Send a WhatsApp message.
    Admin only.
    """
    from . import whatsapp_utils
    
    result = whatsapp_utils.send_text_message(to, message)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {"status": "sent", "result": result}


# --- Export CSV ---
@app.get('/contacts/export')
def export_csv(
    ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    q = db.query(Contact)
    if ids:
        try:
            id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
            if id_list:
                q = q.filter(Contact.id.in_(id_list))
        except Exception:
            pass
    contacts = q.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','uid','full_name','company','position','email','phone','address','comment','website','photo_path'])
    for c in contacts:
        writer.writerow([c.id, c.uid or '', c.full_name or '', c.company or '', c.position or '', c.email or '', c.phone or '', c.address or '', c.comment or '', c.website or '', c.photo_path or ''])
    output.seek(0)
    return StreamingResponse(output, media_type='text/csv', headers={'Content-Disposition':'attachment; filename=contacts.csv'})

# --- Export XLSX ---
@app.get('/contacts/export/xlsx')
def export_xlsx(
    ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    q = db.query(Contact)
    if ids:
        try:
            id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
            if id_list:
                q = q.filter(Contact.id.in_(id_list))
        except Exception:
            pass
    contacts = q.all()
    df = pd.DataFrame([{
        'id': c.id,
        'uid': c.uid,
        'full_name': c.full_name,
        'company': c.company,
        'position': c.position,
        'email': c.email,
        'phone': c.phone,
        'address': c.address,
        'comment': c.comment,
        'website': c.website,
        'photo_path': c.photo_path,
    } for c in contacts])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    headers = {'Content-Disposition': 'attachment; filename=contacts.xlsx'}
    return StreamingResponse(buffer, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)

# --- Export PDF ---
@app.get('/contacts/{contact_id}/pdf')
def export_contact_pdf(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a PDF business card for a contact."""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    buffer = io.BytesIO()
    
    # Create PDF
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "Business Card")
    
    # Contact Information
    y_position = height - 150
    c.setFont("Helvetica-Bold", 16)
    
    if contact.full_name:
        c.drawString(100, y_position, contact.full_name)
        y_position -= 30
    
    c.setFont("Helvetica", 12)
    
    if contact.position:
        c.drawString(100, y_position, f"Position: {contact.position}")
        y_position -= 20
    
    if contact.company:
        c.drawString(100, y_position, f"Company: {contact.company}")
        y_position -= 20
    
    if contact.email:
        c.drawString(100, y_position, f"Email: {contact.email}")
        y_position -= 20
    
    if contact.phone:
        c.drawString(100, y_position, f"Phone: {contact.phone}")
        y_position -= 20
    
    if contact.website:
        c.drawString(100, y_position, f"Website: {contact.website}")
        y_position -= 20
    
    if contact.address:
        c.setFont("Helvetica", 10)
        c.drawString(100, y_position, f"Address: {contact.address}")
        y_position -= 20
    
    # Photo if available
    if contact.photo_path:
        try:
            photo_full_path = os.path.join('uploads', contact.photo_path)
            if os.path.exists(photo_full_path):
                img = ImageReader(photo_full_path)
                c.drawImage(img, 400, height - 300, width=150, height=150, preserveAspectRatio=True)
        except Exception as e:
            logger.warning(f"Could not add photo to PDF: {e}")
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(100, 50, f"Generated by BizCard CRM - {uuid.uuid4().hex[:8]}")
    
    c.save()
    buffer.seek(0)
    
    filename = f"{contact.full_name or 'contact'}_{contact.id}.pdf".replace(' ', '_')
    headers = {'Content-Disposition': f'attachment; filename={filename}'}
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact.id,
        user=current_user,
        action='pdf_exported',
        entity_type='contact',
        changes={'filename': filename}
    )
    db.commit()
    
    return StreamingResponse(buffer, media_type='application/pdf', headers=headers)

# --- Import CSV/XLSX ---
@app.post('/contacts/import')
def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    ext = (file.filename or '').split('.')[-1].lower()
    if ext == 'csv':
        df = pd.read_csv(file.file)
    elif ext in ('xls','xlsx'):
        df = pd.read_excel(file.file)
    else:
        raise HTTPException(status_code=400, detail='Unsupported file format')
    added = 0
    for _, row in df.iterrows():
        obj = {}
        for k in ['full_name','company','position','email','phone','address','comment']:
            val = row.get(k)
            if pd.isna(val):
                val = None
            obj[k] = val
        db.add(Contact(**obj))
        added += 1
    db.commit()
    return {'imported': added}

# --- Bulk delete ---
@app.post('/contacts/delete_bulk')
def delete_bulk(
    ids: list[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db.query(Contact).filter(Contact.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {'deleted': len(ids)}

# --- Bulk update ---
@app.put('/contacts/update_bulk')
def update_bulk(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    ids = payload.get('ids', [])
    fields = payload.get('fields', {})
    if not ids or not fields:
        raise HTTPException(status_code=400, detail='ids and fields required')
    stmt = update(Contact).where(Contact.id.in_(ids)).values(**fields)
    db.execute(stmt)
    db.commit()
    return {'updated': len(ids)}


# ============================================================================
# TAG ENDPOINTS
# ============================================================================

@app.get('/tags/', response_model=List[schemas.TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tags."""
    from .models import Tag
    return db.query(Tag).order_by(Tag.name).all()


@app.post('/tags/', response_model=schemas.TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new tag."""
    from .models import Tag
    
    # Check if tag with this name already exists
    existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag_data.name}' already exists"
        )
    
    tag = Tag(**tag_data.dict())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    logger.info(f"Tag created by {current_user.username}: {tag.name}")
    return tag


@app.put('/tags/{tag_id}', response_model=schemas.TagResponse)
def update_tag(
    tag_id: int,
    tag_data: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a tag."""
    from .models import Tag
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail='Tag not found')
    
    # Check for duplicate name
    if tag_data.name and tag_data.name != tag.name:
        existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag_data.name}' already exists"
            )
        tag.name = tag_data.name
    
    if tag_data.color is not None:
        tag.color = tag_data.color
    
    db.commit()
    db.refresh(tag)
    
    logger.info(f"Tag updated by {current_user.username}: {tag.name}")
    return tag


@app.delete('/tags/{tag_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Only admins can delete tags
):
    """Delete a tag (admin only)."""
    from .models import Tag
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail='Tag not found')
    
    logger.info(f"Tag deleted by admin {current_user.username}: {tag.name}")
    db.delete(tag)
    db.commit()
    return


@app.post('/contacts/{contact_id}/tags', response_model=schemas.ContactResponse)
def add_tag_to_contact(
    contact_id: int,
    tag_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add tags to a contact."""
    from .models import Tag
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    for tag_id in tag_ids:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if tag and tag not in contact.tags:
            contact.tags.append(tag)
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Tags added to contact {contact.full_name} by {current_user.username}")
    return contact


@app.delete('/contacts/{contact_id}/tags/{tag_id}', response_model=schemas.ContactResponse)
def remove_tag_from_contact(
    contact_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a tag from a contact."""
    from .models import Tag
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag and tag in contact.tags:
        contact.tags.remove(tag)
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Tag removed from contact {contact.full_name} by {current_user.username}")
    return contact


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================

@app.get('/groups/', response_model=List[schemas.GroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all groups."""
    from .models import Group
    return db.query(Group).order_by(Group.name).all()


@app.post('/groups/', response_model=schemas.GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new group."""
    from .models import Group
    
    # Check if group with this name already exists
    existing = db.query(Group).filter(Group.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group '{group_data.name}' already exists"
        )
    
    group = Group(**group_data.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    
    logger.info(f"Group created by {current_user.username}: {group.name}")
    return group


@app.put('/groups/{group_id}', response_model=schemas.GroupResponse)
def update_group(
    group_id: int,
    group_data: schemas.GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a group."""
    from .models import Group
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail='Group not found')
    
    # Check for duplicate name
    if group_data.name and group_data.name != group.name:
        existing = db.query(Group).filter(Group.name == group_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Group '{group_data.name}' already exists"
            )
        group.name = group_data.name
    
    if group_data.description is not None:
        group.description = group_data.description
    
    if group_data.color is not None:
        group.color = group_data.color
    
    db.commit()
    db.refresh(group)
    
    logger.info(f"Group updated by {current_user.username}: {group.name}")
    return group


@app.delete('/groups/{group_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Only admins can delete groups
):
    """Delete a group (admin only)."""
    from .models import Group
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail='Group not found')
    
    logger.info(f"Group deleted by admin {current_user.username}: {group.name}")
    db.delete(group)
    db.commit()
    return


@app.post('/contacts/{contact_id}/groups', response_model=schemas.ContactResponse)
def add_group_to_contact(
    contact_id: int,
    group_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add groups to a contact."""
    from .models import Group
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    for group_id in group_ids:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group and group not in contact.groups:
            contact.groups.append(group)
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Groups added to contact {contact.full_name} by {current_user.username}")
    return contact


@app.delete('/contacts/{contact_id}/groups/{group_id}', response_model=schemas.ContactResponse)
def remove_group_from_contact(
    contact_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a group from a contact."""
    from .models import Group
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if group and group in contact.groups:
        contact.groups.remove(group)
        
        # Audit log
        create_audit_log(
            db=db,
            contact_id=contact.id,
            user=current_user,
            action='group_removed',
            entity_type='contact',
            changes={'group_id': group.id, 'group_name': group.name}
        )
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Group removed from contact {contact.full_name} by {current_user.username}")
    return contact


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@app.get('/contacts/{contact_id}/history', response_model=List[schemas.AuditLogResponse])
def get_contact_history(
    contact_id: int,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit history for a specific contact."""
    from .models import AuditLog
    
    # Check if contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Get audit logs for this contact
    logs = db.query(AuditLog).filter(
        AuditLog.contact_id == contact_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return logs


@app.get('/audit/recent', response_model=List[schemas.AuditLogResponse])
def get_recent_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (contact, tag, group)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Only admins can view all logs
):
    """Get recent audit logs (admin only)."""
    from .models import AuditLog
    
    query = db.query(AuditLog)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return logs


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@app.get('/statistics/overview')
def get_statistics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overall statistics and analytics."""
    from .models import Tag, Group
    from sqlalchemy import func, extract
    
    # Total counts
    total_contacts = db.query(Contact).count()
    total_tags = db.query(Tag).count()
    total_groups = db.query(Group).count()
    total_users = db.query(User).count()
    
    # Contacts with contact info
    with_email = db.query(Contact).filter(Contact.email.isnot(None), Contact.email != '').count()
    with_phone = db.query(Contact).filter(Contact.phone.isnot(None), Contact.phone != '').count()
    with_photo = db.query(Contact).filter(Contact.photo_path.isnot(None), Contact.photo_path != '').count()
    
    # Top companies (limit 10)
    top_companies = db.query(
        Contact.company,
        func.count(Contact.id).label('count')
    ).filter(
        Contact.company.isnot(None),
        Contact.company != ''
    ).group_by(Contact.company).order_by(
        func.count(Contact.id).desc()
    ).limit(10).all()
    
    # Top positions (limit 10)
    top_positions = db.query(
        Contact.position,
        func.count(Contact.id).label('count')
    ).filter(
        Contact.position.isnot(None),
        Contact.position != ''
    ).group_by(Contact.position).order_by(
        func.count(Contact.id).desc()
    ).limit(10).all()
    
    # Tag usage stats
    tag_stats = []
    for tag in db.query(Tag).all():
        count = len(tag.contacts)
        if count > 0:
            tag_stats.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'contacts_count': count
            })
    tag_stats.sort(key=lambda x: x['contacts_count'], reverse=True)
    
    # Group usage stats
    group_stats = []
    for group in db.query(Group).all():
        count = len(group.contacts)
        if count > 0:
            group_stats.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'color': group.color,
                'contacts_count': count
            })
    group_stats.sort(key=lambda x: x['contacts_count'], reverse=True)
    
    # Recent activity (last 7 days)
    from datetime import datetime, timedelta
    from .models import AuditLog
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_activity = db.query(AuditLog).filter(
        AuditLog.timestamp >= seven_days_ago
    ).count()
    
    return {
        'totals': {
            'contacts': total_contacts,
            'tags': total_tags,
            'groups': total_groups,
            'users': total_users,
        },
        'contact_details': {
            'with_email': with_email,
            'with_phone': with_phone,
            'with_photo': with_photo,
            'without_email': total_contacts - with_email,
            'without_phone': total_contacts - with_phone,
        },
        'top_companies': [{'company': c, 'count': cnt} for c, cnt in top_companies],
        'top_positions': [{'position': p, 'count': cnt} for p, cnt in top_positions],
        'tags': tag_stats[:10],  # Top 10 tags
        'groups': group_stats[:10],  # Top 10 groups
        'recent_activity': {
            'last_7_days': recent_activity
        }
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post('/auth/register', response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")  # 10 registrations per hour per IP
async def register(request: Request, user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (alphanumeric, 3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    """
    try:
        # Create user (auth_utils will check for duplicates)
        user = auth_utils.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_admin=False  # Regular users can't self-promote to admin
        )
        logger.info(f"New user registered: {user.username}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post('/auth/login', response_model=schemas.Token)
@limiter.limit("30/minute")  # 30 login attempts per minute per IP
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    Returns JWT access token.
    
    - **username**: Username or email
    - **password**: User password
    """
    user = auth_utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        auth_attempts_counter.labels(status='failed').inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        auth_attempts_counter.labels(status='pending_approval').inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting administrator approval. Please contact the system administrator."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Update auth metrics
    auth_attempts_counter.labels(status='success').inc()
    users_total.set(db.query(User).count())
    
    logger.info(f"User logged in: {user.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get('/auth/me', response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get current authenticated user information.
    Requires valid JWT token.
    """
    return current_user


@app.put('/auth/me', response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: User = Depends(auth_utils.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    Requires valid JWT token.
    
    - **email**: New email (optional)
    - **full_name**: New full name (optional)
    - **password**: New password (optional)
    """
    # Update fields
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing = auth_utils.get_user_by_email(db, user_update.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.hashed_password = auth_utils.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User updated profile: {current_user.username}")
    
    return current_user


@app.get('/auth/users', response_model=List[schemas.UserResponse])
async def list_users(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    Requires valid JWT token with admin privileges.
    """
    users = db.query(User).all()
    return users


@app.get('/auth/users/{user_id}', response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@app.delete('/auth/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID (admin only).
    Requires valid JWT token with admin privileges.
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted by admin {current_user.username}: {user.username}")
    
    return None


@app.patch('/auth/users/{user_id}/admin', response_model=schemas.UserResponse)
async def toggle_admin(
    user_id: int,
    is_admin: bool = Body(..., embed=True),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status for a user (admin only).
    Requires valid JWT token with admin privileges.
    Cannot change your own admin status.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    
    logger.info(f"Admin status changed by {current_user.username}: {user.username} -> {is_admin}")
    
    return user


@app.post('/auth/users/{user_id}/reset-password')
async def reset_user_password(
    user_id: int,
    new_password: str = Body(..., embed=True, min_length=6),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset user password (admin only).
    Sets a new password for the specified user.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the new password
    user.hashed_password = auth_utils.get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password reset by admin {current_user.username} for user: {user.username}")
    
    return {
        "success": True,
        "message": f"Password reset successful for user: {user.username}"
    }


@app.patch('/auth/users/{user_id}/activate', response_model=schemas.UserResponse)
async def activate_user(
    user_id: int,
    is_active: bool = Body(..., embed=True),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a user (admin only).
    Used to approve new user registrations.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    
    action = "activated" if is_active else "deactivated"
    logger.info(f"User {action} by admin {current_user.username}: {user.username}")
    
    return user


@app.put('/auth/users/{user_id}/profile', response_model=schemas.UserResponse)
async def update_user_profile(
    user_id: int,
    update_data: schemas.UserUpdate,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile (admin only).
    Allows updating email, full_name, and password.
    Requires valid JWT token with admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_data.email is not None:
        # Check if email already exists for another user
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another user"
            )
        user.email = update_data.email
    
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    
    if update_data.password is not None:
        user.hashed_password = auth_utils.get_password_hash(update_data.password)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User profile updated by admin {current_user.username}: {user.username}")
    
    return user


# ============================================================================
# SYSTEM SETTINGS ENDPOINTS
# ============================================================================

@app.get('/settings/system')
async def get_system_settings(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system settings (admin only).
    Returns various system configuration parameters.
    """
    return {
        "database": {
            "total_contacts": db.query(Contact).count(),
            "total_users": db.query(User).count(),
            "pending_users": db.query(User).filter(User.is_active == False).count(),
        },
        "ocr": {
            "default_provider": "auto",
            "available_providers": ["tesseract", "parsio", "google", "auto"],
            "tesseract_langs": os.getenv("TESSERACT_LANGS", "rus+eng"),
        },
        "telegram": {
            "bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", ""),
        },
        "authentication": {
            "token_expire_minutes": auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES,
            "require_admin_approval": True,
        },
        "application": {
            "version": os.getenv("APP_VERSION", "1.9"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
    }


@app.get('/settings/pending-users', response_model=list[schemas.UserResponse])
async def get_pending_users(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users pending approval (admin only).
    Returns users with is_active=False.
    """
    pending_users = db.query(User).filter(User.is_active == False).all()
    return pending_users


@app.get('/settings/editable')
async def get_editable_settings(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get editable settings (admin only).
    Returns current environment variables and database settings.
    """
    from .models import AppSetting
    
    # Get database settings
    def get_setting(key: str, default: str = ""):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        return setting.value if setting else default
    
    return {
        "ocr": {
            "tesseract_langs": get_setting("TESSERACT_LANGS", os.getenv("TESSERACT_LANGS", "rus+eng")),
            "parsio_api_key": get_setting("PARSIO_API_KEY", ""),
            "google_vision_api_key": get_setting("GOOGLE_VISION_API_KEY", ""),
        },
        "telegram": {
            "bot_token": get_setting("TELEGRAM_BOT_TOKEN", ""),
            "webhook_url": get_setting("TELEGRAM_WEBHOOK_URL", ""),
        },
        "whatsapp": {
            "api_token": get_setting("WHATSAPP_API_TOKEN", ""),
            "phone_number_id": get_setting("WHATSAPP_PHONE_NUMBER_ID", ""),
            "business_account_id": get_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            "webhook_verify_token": get_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
        },
        "redis": {
            "url": get_setting("REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")),
            "max_connections": int(get_setting("REDIS_MAX_CONNECTIONS", "10")),
        },
        "celery": {
            "broker_url": get_setting("CELERY_BROKER_URL", os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")),
            "result_backend": get_setting("CELERY_RESULT_BACKEND", os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")),
            "worker_concurrency": int(get_setting("CELERY_WORKER_CONCURRENCY", "2")),
            "task_time_limit": int(get_setting("CELERY_TASK_TIME_LIMIT", "300")),
        },
        "backup": {
            "enabled": get_setting("BACKUP_ENABLED", "true") == "true",
            "schedule": get_setting("BACKUP_SCHEDULE", "0 2 * * *"),  # Daily at 2 AM
            "retention_days": int(get_setting("BACKUP_RETENTION_DAYS", "30")),
            "backup_dir": get_setting("BACKUP_DIR", "/home/ubuntu/fastapi-bizcard-crm-ready/backups"),
        },
        "monitoring": {
            "prometheus_enabled": get_setting("PROMETHEUS_ENABLED", "true") == "true",
            "grafana_enabled": get_setting("GRAFANA_ENABLED", "true") == "true",
            "metrics_retention_days": int(get_setting("METRICS_RETENTION_DAYS", "15")),
        },
        "auth": {
            "token_expire_minutes": int(get_setting("TOKEN_EXPIRE_MINUTES", str(auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES))),
            "require_admin_approval": get_setting("REQUIRE_ADMIN_APPROVAL", "true") == "true",
        }
    }


@app.put('/settings/editable')
async def update_editable_settings(
    settings: dict = Body(...),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update editable settings (admin only).
    Saves settings to database.
    """
    from .models import AppSetting
    
    def set_setting(key: str, value: str):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = AppSetting(key=key, value=value)
            db.add(setting)
    
    # Update OCR settings
    if "ocr" in settings:
        if "tesseract_langs" in settings["ocr"]:
            set_setting("TESSERACT_LANGS", settings["ocr"]["tesseract_langs"])
        if "parsio_api_key" in settings["ocr"]:
            set_setting("PARSIO_API_KEY", settings["ocr"]["parsio_api_key"])
        if "google_vision_api_key" in settings["ocr"]:
            set_setting("GOOGLE_VISION_API_KEY", settings["ocr"]["google_vision_api_key"])
    
    # Update Telegram settings
    if "telegram" in settings:
        if "bot_token" in settings["telegram"]:
            set_setting("TELEGRAM_BOT_TOKEN", settings["telegram"]["bot_token"])
        if "webhook_url" in settings["telegram"]:
            set_setting("TELEGRAM_WEBHOOK_URL", settings["telegram"]["webhook_url"])
    
    # Update WhatsApp settings
    if "whatsapp" in settings:
        if "api_token" in settings["whatsapp"]:
            set_setting("WHATSAPP_API_TOKEN", settings["whatsapp"]["api_token"])
        if "phone_number_id" in settings["whatsapp"]:
            set_setting("WHATSAPP_PHONE_NUMBER_ID", settings["whatsapp"]["phone_number_id"])
        if "business_account_id" in settings["whatsapp"]:
            set_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", settings["whatsapp"]["business_account_id"])
        if "webhook_verify_token" in settings["whatsapp"]:
            set_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", settings["whatsapp"]["webhook_verify_token"])
    
    # Update Redis settings
    if "redis" in settings:
        if "url" in settings["redis"]:
            set_setting("REDIS_URL", settings["redis"]["url"])
        if "max_connections" in settings["redis"]:
            set_setting("REDIS_MAX_CONNECTIONS", str(settings["redis"]["max_connections"]))
    
    # Update Celery settings
    if "celery" in settings:
        if "broker_url" in settings["celery"]:
            set_setting("CELERY_BROKER_URL", settings["celery"]["broker_url"])
        if "result_backend" in settings["celery"]:
            set_setting("CELERY_RESULT_BACKEND", settings["celery"]["result_backend"])
        if "worker_concurrency" in settings["celery"]:
            set_setting("CELERY_WORKER_CONCURRENCY", str(settings["celery"]["worker_concurrency"]))
        if "task_time_limit" in settings["celery"]:
            set_setting("CELERY_TASK_TIME_LIMIT", str(settings["celery"]["task_time_limit"]))
    
    # Update Backup settings
    if "backup" in settings:
        if "enabled" in settings["backup"]:
            set_setting("BACKUP_ENABLED", "true" if settings["backup"]["enabled"] else "false")
        if "schedule" in settings["backup"]:
            set_setting("BACKUP_SCHEDULE", settings["backup"]["schedule"])
        if "retention_days" in settings["backup"]:
            set_setting("BACKUP_RETENTION_DAYS", str(settings["backup"]["retention_days"]))
        if "backup_dir" in settings["backup"]:
            set_setting("BACKUP_DIR", settings["backup"]["backup_dir"])
    
    # Update Monitoring settings
    if "monitoring" in settings:
        if "prometheus_enabled" in settings["monitoring"]:
            set_setting("PROMETHEUS_ENABLED", "true" if settings["monitoring"]["prometheus_enabled"] else "false")
        if "grafana_enabled" in settings["monitoring"]:
            set_setting("GRAFANA_ENABLED", "true" if settings["monitoring"]["grafana_enabled"] else "false")
        if "metrics_retention_days" in settings["monitoring"]:
            set_setting("METRICS_RETENTION_DAYS", str(settings["monitoring"]["metrics_retention_days"]))
    
    # Update Auth settings
    if "auth" in settings:
        if "token_expire_minutes" in settings["auth"]:
            set_setting("TOKEN_EXPIRE_MINUTES", str(settings["auth"]["token_expire_minutes"]))
        if "require_admin_approval" in settings["auth"]:
            set_setting("REQUIRE_ADMIN_APPROVAL", "true" if settings["auth"]["require_admin_approval"] else "false")
    
    db.commit()
    
    logger.info(f"Settings updated by admin {current_user.username}")
    
    return {"message": "Settings updated successfully. Restart application for some changes to take effect."}


# ============================================================================
# Integration Management Endpoints (Admin Only)
# ============================================================================

@app.get('/settings/integrations/status')
async def get_integrations_status(
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get status of all system integrations (admin only).
    Returns enabled/disabled status, configuration status, and last check time.
    """
    from .models import AppSetting
    
    def get_setting(key: str, default: str = ""):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        return setting.value if setting else default
    
    def is_configured(keys):
        """Check if all required keys are configured"""
        return all(get_setting(key) != "" for key in keys)
    
    integrations = [
        {
            "id": "ocr",
            "name": "OCR Recognition",
            "description": "Business card text recognition",
            "enabled": get_setting("OCR_ENABLED", "true") == "true",
            "configured": is_configured(["TESSERACT_LANGS"]),
            "connection_ok": True,  # Tesseract is always available locally
            "last_checked": time.time(),
            "config": {
                "tesseract_langs": get_setting("TESSERACT_LANGS", "rus+eng"),
                "parsio_api_key": get_setting("PARSIO_API_KEY", ""),
                "google_vision_api_key": get_setting("GOOGLE_VISION_API_KEY", "")
            },
            "config_summary": {
                "Tesseract": get_setting("TESSERACT_LANGS", "rus+eng"),
                "Parsio": "Configured" if get_setting("PARSIO_API_KEY") else "Not configured",
                "Google Vision": "Configured" if get_setting("GOOGLE_VISION_API_KEY") else "Not configured"
            }
        },
        {
            "id": "telegram",
            "name": "Telegram Integration",
            "description": "Receive business cards via Telegram",
            "enabled": get_setting("TELEGRAM_ENABLED", "false") == "true",
            "configured": is_configured(["TELEGRAM_BOT_TOKEN"]),
            "connection_ok": None,  # Will be checked on demand
            "last_checked": None,
            "config": {
                "bot_token": get_setting("TELEGRAM_BOT_TOKEN", ""),
                "webhook_url": get_setting("TELEGRAM_WEBHOOK_URL", "")
            },
            "config_summary": {
                "Bot Token": "***" + get_setting("TELEGRAM_BOT_TOKEN", "")[-6:] if get_setting("TELEGRAM_BOT_TOKEN") else "Not set",
                "Webhook": get_setting("TELEGRAM_WEBHOOK_URL", "Not set")
            }
        },
        {
            "id": "whatsapp",
            "name": "WhatsApp Business",
            "description": "Receive business cards via WhatsApp",
            "enabled": get_setting("WHATSAPP_ENABLED", "false") == "true",
            "configured": is_configured(["WHATSAPP_API_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"]),
            "connection_ok": None,
            "last_checked": None,
            "config": {
                "api_token": get_setting("WHATSAPP_API_TOKEN", ""),
                "phone_number_id": get_setting("WHATSAPP_PHONE_NUMBER_ID", ""),
                "business_account_id": get_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
                "webhook_verify_token": get_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
            },
            "config_summary": {
                "Phone ID": get_setting("WHATSAPP_PHONE_NUMBER_ID", "Not set"),
                "Business ID": get_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", "Not set")
            }
        },
        {
            "id": "auth",
            "name": "Authentication",
            "description": "User authentication settings",
            "enabled": True,  # Always enabled
            "configured": True,
            "connection_ok": True,
            "last_checked": time.time(),
            "config": {
                "token_expire_minutes": int(get_setting("TOKEN_EXPIRE_MINUTES", "10080")),
                "require_admin_approval": get_setting("REQUIRE_ADMIN_APPROVAL", "true") == "true"
            },
            "config_summary": {
                "Token Expiry": f"{get_setting('TOKEN_EXPIRE_MINUTES', '10080')} min",
                "Admin Approval": "Required" if get_setting("REQUIRE_ADMIN_APPROVAL", "true") == "true" else "Not required"
            }
        },
        {
            "id": "backup",
            "name": "Backup & Recovery",
            "description": "Automatic database backups",
            "enabled": get_setting("BACKUP_ENABLED", "true") == "true",
            "configured": True,
            "connection_ok": True,
            "last_checked": time.time(),
            "config": {
                "enabled": get_setting("BACKUP_ENABLED", "true") == "true",
                "schedule": get_setting("BACKUP_SCHEDULE", "0 2 * * *"),
                "retention_days": int(get_setting("BACKUP_RETENTION_DAYS", "30")),
                "backup_dir": get_setting("BACKUP_DIR", "/home/ubuntu/fastapi-bizcard-crm-ready/backups")
            },
            "config_summary": {
                "Schedule": get_setting("BACKUP_SCHEDULE", "0 2 * * *"),
                "Retention": f"{get_setting('BACKUP_RETENTION_DAYS', '30')} days"
            }
        },
        {
            "id": "monitoring",
            "name": "Monitoring",
            "description": "Prometheus and Grafana",
            "enabled": get_setting("PROMETHEUS_ENABLED", "true") == "true",
            "configured": True,
            "connection_ok": True,
            "last_checked": time.time(),
            "config": {
                "prometheus_enabled": get_setting("PROMETHEUS_ENABLED", "true") == "true",
                "grafana_enabled": get_setting("GRAFANA_ENABLED", "true") == "true",
                "metrics_retention_days": int(get_setting("METRICS_RETENTION_DAYS", "15"))
            },
            "config_summary": {
                "Prometheus": "Enabled" if get_setting("PROMETHEUS_ENABLED", "true") == "true" else "Disabled",
                "Grafana": "Enabled" if get_setting("GRAFANA_ENABLED", "true") == "true" else "Disabled"
            }
        },
        {
            "id": "redis",
            "name": "Redis Cache",
            "description": "Cache and message broker",
            "enabled": True,  # Always enabled
            "configured": True,
            "connection_ok": None,  # Will be checked on demand
            "last_checked": None,
            "config": {
                "url": get_setting("REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")),
                "max_connections": int(get_setting("REDIS_MAX_CONNECTIONS", "10"))
            },
            "config_summary": {
                "URL": get_setting("REDIS_URL", "redis://redis:6379/0"),
                "Max Connections": get_setting("REDIS_MAX_CONNECTIONS", "10")
            }
        },
        {
            "id": "celery",
            "name": "Background Tasks",
            "description": "Asynchronous task processing",
            "enabled": True,  # Always enabled
            "configured": True,
            "connection_ok": None,
            "last_checked": None,
            "config": {
                "broker_url": get_setting("CELERY_BROKER_URL", os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")),
                "result_backend": get_setting("CELERY_RESULT_BACKEND", os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")),
                "worker_concurrency": int(get_setting("CELERY_WORKER_CONCURRENCY", "2")),
                "task_time_limit": int(get_setting("CELERY_TASK_TIME_LIMIT", "300"))
            },
            "config_summary": {
                "Concurrency": get_setting("CELERY_WORKER_CONCURRENCY", "2"),
                "Task Limit": f"{get_setting('CELERY_TASK_TIME_LIMIT', '300')}s"
            }
        }
    ]
    
    return {"integrations": integrations}


@app.post('/settings/integrations/{integration_id}/toggle')
async def toggle_integration(
    integration_id: str,
    data: dict = Body(...),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Enable or disable a specific integration (admin only).
    """
    from .models import AppSetting
    
    enabled = data.get("enabled", False)
    
    def set_setting(key: str, value: str):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = AppSetting(key=key, value=value)
            db.add(setting)
    
    # Map integration IDs to their enable/disable settings
    integration_settings = {
        "ocr": "OCR_ENABLED",
        "telegram": "TELEGRAM_ENABLED",
        "whatsapp": "WHATSAPP_ENABLED",
        "backup": "BACKUP_ENABLED",
        "monitoring": "PROMETHEUS_ENABLED"
    }
    
    setting_key = integration_settings.get(integration_id)
    if not setting_key:
        raise HTTPException(status_code=400, detail=f"Integration {integration_id} cannot be toggled")
    
    set_setting(setting_key, "true" if enabled else "false")
    db.commit()
    
    logger.info(f"Integration {integration_id} {'enabled' if enabled else 'disabled'} by admin {current_user.username}")
    
    return {"success": True, "message": f"Integration {integration_id} {'enabled' if enabled else 'disabled'}"}


@app.post('/settings/integrations/{integration_id}/test')
async def test_integration(
    integration_id: str,
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Test connection to a specific integration (admin only).
    """
    from .models import AppSetting
    
    def get_setting(key: str, default: str = ""):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        return setting.value if setting else default
    
    try:
        if integration_id == "telegram":
            bot_token = get_setting("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                return {"success": False, "error": "Bot token not configured"}
            
            # Test Telegram API
            response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {"success": True, "message": f"Connected to bot: @{data['result']['username']}"}
            return {"success": False, "error": "Invalid bot token"}
        
        elif integration_id == "whatsapp":
            api_token = get_setting("WHATSAPP_API_TOKEN")
            phone_id = get_setting("WHATSAPP_PHONE_NUMBER_ID")
            if not api_token or not phone_id:
                return {"success": False, "error": "WhatsApp credentials not configured"}
            
            # Test WhatsApp API
            api_url = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v18.0")
            response = requests.get(
                f"{api_url}/{phone_id}",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=5
            )
            if response.status_code == 200:
                return {"success": True, "message": "WhatsApp API connection successful"}
            return {"success": False, "error": f"API error: {response.status_code}"}
        
        elif integration_id == "redis":
            import redis
            redis_url = get_setting("REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            return {"success": True, "message": "Redis connection successful"}
        
        elif integration_id == "celery":
            from .celery_app import celery_app
            # Check if celery workers are running
            inspect = celery_app.control.inspect(timeout=2)
            stats = inspect.stats()
            if stats:
                worker_count = len(stats)
                return {"success": True, "message": f"{worker_count} Celery worker(s) active"}
            return {"success": False, "error": "No Celery workers found"}
        
        elif integration_id == "ocr":
            # OCR is always available (Tesseract is local)
            return {"success": True, "message": "Tesseract OCR available"}
        
        else:
            return {"success": False, "error": "Test not implemented for this integration"}
    
    except Exception as e:
        logger.error(f"Error testing integration {integration_id}: {e}")
        return {"success": False, "error": str(e)}


@app.put('/settings/integrations/{integration_id}/config')
async def update_integration_config(
    integration_id: str,
    data: dict = Body(...),
    current_user: User = Depends(auth_utils.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update configuration for a specific integration (admin only).
    """
    from .models import AppSetting
    
    config = data.get("config", {})
    
    def set_setting(key: str, value: str):
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = AppSetting(key=key, value=value)
            db.add(setting)
    
    # Map integration IDs to their configuration keys
    if integration_id == "ocr":
        if "tesseract_langs" in config:
            set_setting("TESSERACT_LANGS", config["tesseract_langs"])
        if "parsio_api_key" in config:
            set_setting("PARSIO_API_KEY", config["parsio_api_key"])
        if "google_vision_api_key" in config:
            set_setting("GOOGLE_VISION_API_KEY", config["google_vision_api_key"])
    
    elif integration_id == "telegram":
        if "bot_token" in config:
            set_setting("TELEGRAM_BOT_TOKEN", config["bot_token"])
        if "webhook_url" in config:
            set_setting("TELEGRAM_WEBHOOK_URL", config["webhook_url"])
    
    elif integration_id == "whatsapp":
        if "api_token" in config:
            set_setting("WHATSAPP_API_TOKEN", config["api_token"])
        if "phone_number_id" in config:
            set_setting("WHATSAPP_PHONE_NUMBER_ID", config["phone_number_id"])
        if "business_account_id" in config:
            set_setting("WHATSAPP_BUSINESS_ACCOUNT_ID", config["business_account_id"])
        if "webhook_verify_token" in config:
            set_setting("WHATSAPP_WEBHOOK_VERIFY_TOKEN", config["webhook_verify_token"])
    
    elif integration_id == "auth":
        if "token_expire_minutes" in config:
            set_setting("TOKEN_EXPIRE_MINUTES", str(config["token_expire_minutes"]))
        if "require_admin_approval" in config:
            set_setting("REQUIRE_ADMIN_APPROVAL", "true" if config["require_admin_approval"] else "false")
    
    elif integration_id == "backup":
        if "enabled" in config:
            set_setting("BACKUP_ENABLED", "true" if config["enabled"] else "false")
        if "schedule" in config:
            set_setting("BACKUP_SCHEDULE", config["schedule"])
        if "retention_days" in config:
            set_setting("BACKUP_RETENTION_DAYS", str(config["retention_days"]))
        if "backup_dir" in config:
            set_setting("BACKUP_DIR", config["backup_dir"])
    
    elif integration_id == "monitoring":
        if "prometheus_enabled" in config:
            set_setting("PROMETHEUS_ENABLED", "true" if config["prometheus_enabled"] else "false")
        if "grafana_enabled" in config:
            set_setting("GRAFANA_ENABLED", "true" if config["grafana_enabled"] else "false")
        if "metrics_retention_days" in config:
            set_setting("METRICS_RETENTION_DAYS", str(config["metrics_retention_days"]))
    
    elif integration_id == "redis":
        if "url" in config:
            set_setting("REDIS_URL", config["url"])
        if "max_connections" in config:
            set_setting("REDIS_MAX_CONNECTIONS", str(config["max_connections"]))
    
    elif integration_id == "celery":
        if "broker_url" in config:
            set_setting("CELERY_BROKER_URL", config["broker_url"])
        if "result_backend" in config:
            set_setting("CELERY_RESULT_BACKEND", config["result_backend"])
        if "worker_concurrency" in config:
            set_setting("CELERY_WORKER_CONCURRENCY", str(config["worker_concurrency"]))
        if "task_time_limit" in config:
            set_setting("CELERY_TASK_TIME_LIMIT", str(config["task_time_limit"]))
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown integration: {integration_id}")
    
    db.commit()
    
    logger.info(f"Configuration updated for integration {integration_id} by admin {current_user.username}")
    
    return {"success": True, "message": "Configuration updated successfully"}


# ============================================================================
# Backup Management Endpoints (Admin Only)
# ============================================================================

@app.get('/backups/')
async def list_backups(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    List all database backups (admin only).
    Returns list of backup files with metadata.
    """
    backup_dir = Path("/home/ubuntu/fastapi-bizcard-crm-ready/backups")
    
    if not backup_dir.exists():
        return {"backups": [], "backup_dir": str(backup_dir)}
    
    backups = []
    for backup_file in sorted(backup_dir.glob("backup_bizcard_crm_*.sql.gz"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "size": stat.st_size,
            "size_human": f"{stat.st_size / 1024:.2f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.2f} MB",
            "created_at": stat.st_mtime,
            "created_at_human": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
        })
    
    return {
        "backups": backups,
        "backup_dir": str(backup_dir),
        "total_count": len(backups),
        "total_size": sum(b["size"] for b in backups),
        "total_size_human": f"{sum(b['size'] for b in backups) / (1024*1024):.2f} MB"
    }


@app.post('/backups/create')
async def create_backup(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Create a manual database backup (admin only).
    Uses pg_dump to create a compressed database backup.
    """
    backup_dir = Path("/home/ubuntu/fastapi-bizcard-crm-ready/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_bizcard_crm_{timestamp}.sql.gz"
    backup_path = backup_dir / backup_filename
    
    # Database connection details
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "bizcard_crm")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    try:
        # Create backup using pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # pg_dump command with gzip compression
        dump_cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "--no-owner",
            "--no-acl"
        ]
        
        # Run pg_dump and compress output
        with open(backup_path, 'wb') as f:
            dump_process = subprocess.Popen(
                dump_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            gzip_process = subprocess.Popen(
                ["gzip"],
                stdin=dump_process.stdout,
                stdout=f,
                stderr=subprocess.PIPE
            )
            
            dump_process.stdout.close()
            gzip_stderr = gzip_process.communicate()[1]
            dump_stderr = dump_process.communicate()[1]
        
        if dump_process.returncode == 0 and gzip_process.returncode == 0:
            backup_size = backup_path.stat().st_size
            size_human = f"{backup_size / 1024:.2f} KB" if backup_size < 1024*1024 else f"{backup_size / (1024*1024):.2f} MB"
            
            return {
                "success": True,
                "message": f"Backup created successfully: {backup_filename}",
                "filename": backup_filename,
                "size": backup_size,
                "size_human": size_human
            }
        else:
            error_msg = dump_stderr.decode() if dump_stderr else gzip_stderr.decode() if gzip_stderr else "Unknown error"
            # Clean up failed backup
            if backup_path.exists():
                backup_path.unlink()
            return {
                "success": False,
                "message": "Backup failed",
                "error": error_msg
            }
    except Exception as e:
        # Clean up on exception
        if backup_path.exists():
            backup_path.unlink()
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@app.delete('/backups/{filename}')
async def delete_backup(
    filename: str,
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Delete a specific backup file (admin only).
    """
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Ensure filename matches expected pattern
    if not filename.startswith("backup_bizcard_crm_") or not filename.endswith(".sql.gz"):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    
    backup_path = Path("/home/ubuntu/fastapi-bizcard-crm-ready/backups") / filename
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    try:
        backup_path.unlink()
        return {
            "success": True,
            "message": f"Backup {filename} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@app.get('/system/resources')
async def get_system_resources(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get system resources and service URLs (admin only).
    Returns URLs for all deployed services.
    """
    # Get server hostname or IP
    server_host = os.getenv("SERVER_HOST", "localhost")
    domain = os.getenv("DOMAIN", "ibbase.ru")
    use_https = os.getenv("USE_HTTPS", "false").lower() == "true"
    protocol = "https" if use_https else "http"
    
    return {
        "services": {
            "frontend": {
                "name": "Frontend (React)",
                "url": f"{protocol}://{domain}",
                "local_url": "http://localhost:3000",
                "description": "Main web interface"
            },
            "backend": {
                "name": "Backend API",
                "url": f"{protocol}://api.{domain}",
                "local_url": "http://localhost:8000",
                "description": "FastAPI REST API"
            },
            "api_docs": {
                "name": "API Documentation",
                "url": f"{protocol}://api.{domain}/docs",
                "local_url": "http://localhost:8000/docs",
                "description": "Swagger UI API docs"
            },
            "api_redoc": {
                "name": "API ReDoc",
                "url": f"{protocol}://api.{domain}/redoc",
                "local_url": "http://localhost:8000/redoc",
                "description": "Alternative API docs"
            },
            "grafana": {
                "name": "Grafana Monitoring",
                "url": f"{protocol}://monitoring.{domain}",
                "local_url": "http://localhost:3001",
                "description": "System monitoring dashboards"
            },
            "prometheus": {
                "name": "Prometheus",
                "url": None,  # Not exposed publicly
                "local_url": "http://localhost:9090",
                "description": "Metrics collection (internal only)"
            },
            "metrics": {
                "name": "Application Metrics",
                "url": f"{protocol}://api.{domain}/metrics",
                "local_url": "http://localhost:8000/metrics",
                "description": "Prometheus metrics endpoint"
            }
        },
        "environment": {
            "domain": domain,
            "protocol": protocol,
            "server_host": server_host
        }
    }


# ============================================================================
# Documentation Endpoints (Admin Only)
# ============================================================================

@app.get('/documentation/{doc_name}')
async def get_documentation(
    doc_name: str,
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get documentation content (admin only).
    Supports all markdown files from project root.
    """
    # Security: ensure doc_name doesn't contain path traversal
    if ".." in doc_name or "/" in doc_name or "\\" in doc_name:
        raise HTTPException(status_code=400, detail="Invalid document name")
    
    # Only allow .md files
    if not doc_name.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown files are allowed")
    
    docs_root = Path("/home/ubuntu/fastapi-bizcard-crm-ready")
    doc_path = docs_root / doc_name
    
    # Verify the file exists and is actually in the project root (not in subdirectories)
    if not doc_path.exists() or doc_path.parent != docs_root:
        raise HTTPException(status_code=404, detail="Documentation file not found")
    
    try:
        content = doc_path.read_text(encoding='utf-8')
        return {
            "filename": doc_name,
            "content": content,
            "size": len(content),
            "last_modified": doc_path.stat().st_mtime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read documentation: {str(e)}")


@app.get('/documentation')
async def list_documentation(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    List available documentation files (admin only).
    Automatically scans for all .md files in project root.
    """
    docs_root = Path("/home/ubuntu/fastapi-bizcard-crm-ready")
    
    # Mapping of filenames to descriptions and categories
    doc_metadata = {
        "PRODUCTION_DEPLOYMENT.md": ("Руководство по Production Deployment", "production"),
        "README.md": ("Основная документация проекта", "readme"),
        "TELEGRAM_SETUP.md": ("Настройка Telegram интеграции", "telegram"),
        "TELEGRAM_CONFIGURATION.md": ("Конфигурация Telegram бота", "telegram"),
        "WHATSAPP_SETUP.md": ("Настройка WhatsApp интеграции", "whatsapp"),
        "MONITORING_SETUP.md": ("Настройка мониторинга", "monitoring"),
        "SSL_SETUP.md": ("Настройка SSL/HTTPS", "production"),
        "SSL_SETUP_QUICK.md": ("Быстрая настройка SSL", "production"),
        "SYSTEM_SETTINGS_GUIDE.md": ("Руководство по системным настройкам", "settings"),
        "GITHUB_WORKFLOWS_GUIDE.md": ("Руководство по GitHub Actions", "development"),
        "GITHUB_ACTIONS_ANALYSIS.md": ("Анализ GitHub Actions", "development"),
        "WORKFLOWS_EXPLAINED_RU.md": ("Workflows - объяснение простыми словами", "development"),
        "OCR_TRAINING_GUIDE.md": ("Руководство по обучению OCR", "ocr"),
        "OCR_MULTISELECT_GUIDE.md": ("Мультивыбор в OCR редакторе", "ocr"),
        "CELERY_FIX_LOG.md": ("Лог исправления Celery", "development"),
        "GIT_STRUCTURE_ANALYSIS.md": ("Анализ структуры Git репозитория", "development"),
        "GIT_CLEANUP_SUCCESS.md": ("Очистка Git репозитория", "development"),
    }
    
    # Auto-detect for RELEASE_NOTES_*.md files
    available_docs = []
    
    # Scan all .md files in project root
    for md_file in sorted(docs_root.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        filename = md_file.name
        
        # Get metadata if available, otherwise generate generic
        if filename in doc_metadata:
            description, category = doc_metadata[filename]
        elif filename.startswith("RELEASE_NOTES_"):
            # Auto-detect release notes
            version = filename.replace("RELEASE_NOTES_", "").replace(".md", "")
            description = f"Release Notes {version}"
            category = "releases"
        elif filename.startswith("TEST_RESULTS_"):
            # Auto-detect test results
            version = filename.replace("TEST_RESULTS_", "").replace(".md", "")
            description = f"Test Results {version}"
            category = "testing"
        elif filename.startswith("DEPLOYMENT_"):
            # Auto-detect deployment docs
            version = filename.replace("DEPLOYMENT_", "").replace(".md", "")
            description = f"Deployment {version}"
            category = "production"
        else:
            # Generic document
            description = filename.replace("_", " ").replace(".md", "")
            category = "other"
        
        stat = md_file.stat()
        available_docs.append({
            "filename": filename,
            "description": description,
            "category": category,
            "size": stat.st_size,
            "last_modified": stat.st_mtime,
            "last_modified_human": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
        })
    
    return {
        "documents": available_docs,
        "total_count": len(available_docs)
    }


# ============================================================================
# Service Management Endpoints (Admin Only)
# ============================================================================

@app.get('/services/status')
async def get_services_status(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get status of all Docker services (admin only).
    """
    try:
        # Run docker compose ps to get service status
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready',
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to get service status: {result.stderr}")
        
        # Parse JSON output (one JSON object per line)
        services = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    service_info = json.loads(line)
                    services.append({
                        "name": service_info.get("Service", "unknown"),
                        "container": service_info.get("Name", "unknown"),
                        "state": service_info.get("State", "unknown"),
                        "status": service_info.get("Status", "unknown"),
                        "health": service_info.get("Health", "unknown"),
                        "ports": service_info.get("Publishers", [])
                    })
                except json.JSONDecodeError:
                    continue
        
        # Group services by category
        service_categories = {
            "core": ["backend", "frontend", "db"],
            "processing": ["celery-worker", "redis"],
            "monitoring": ["prometheus", "grafana", "node-exporter", "postgres-exporter", "cadvisor"]
        }
        
        categorized_services = {}
        for category, service_names in service_categories.items():
            categorized_services[category] = [
                svc for svc in services 
                if any(name in svc["name"].lower() for name in service_names)
            ]
        
        # Add uncategorized services
        categorized_names = [svc["name"] for cat_services in categorized_services.values() for svc in cat_services]
        categorized_services["other"] = [
            svc for svc in services if svc["name"] not in categorized_names
        ]
        
        return {
            "services": services,
            "categorized": categorized_services,
            "total_count": len(services),
            "running_count": len([s for s in services if s["state"].lower() == "running"]),
            "timestamp": time.time()
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Service status check timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@app.post('/services/{service_name}/restart')
async def restart_service(
    service_name: str,
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Restart a specific Docker service (admin only).
    """
    # Security: validate service name
    allowed_services = [
        "backend", "frontend", "db", "celery-worker", "redis",
        "prometheus", "grafana", "node-exporter", "postgres-exporter", "cadvisor"
    ]
    
    if service_name not in allowed_services:
        raise HTTPException(status_code=400, detail="Invalid service name")
    
    try:
        # Restart the service
        result = subprocess.run(
            ['docker', 'compose', 'restart', service_name],
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to restart service: {result.stderr}")
        
        logger.info(f"Service {service_name} restarted by admin {current_user.username}")
        
        return {
            "success": True,
            "message": f"Service {service_name} restarted successfully",
            "service": service_name,
            "restarted_by": current_user.username,
            "timestamp": time.time()
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Service restart timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart service: {str(e)}")


@app.get('/services/logs/{service_name}')
async def get_service_logs(
    service_name: str,
    lines: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get logs for a specific service (admin only).
    """
    # Security: validate service name
    allowed_services = [
        "backend", "frontend", "db", "celery-worker", "redis",
        "prometheus", "grafana", "node-exporter", "postgres-exporter", "cadvisor"
    ]
    
    if service_name not in allowed_services:
        raise HTTPException(status_code=400, detail="Invalid service name")
    
    try:
        # Get service logs
        result = subprocess.run(
            ['docker', 'compose', 'logs', '--tail', str(lines), service_name],
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to get logs: {result.stderr}")
        
        return {
            "service": service_name,
            "logs": result.stdout,
            "lines": lines,
            "timestamp": time.time()
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Log retrieval timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

# ============================================================================
# Duplicate Detection & Merging Endpoints
# ============================================================================

@app.get('/api/duplicates')
def get_duplicates(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of detected duplicate contacts.
    Optional filter by status: pending, reviewed, merged, ignored
    """
    from .models import DuplicateContact
    
    query = db.query(DuplicateContact)
    
    if status:
        query = query.filter(DuplicateContact.status == status)
    
    duplicates = query.order_by(
        DuplicateContact.similarity_score.desc(),
        DuplicateContact.detected_at.desc()
    ).limit(limit).all()
    
    result = []
    for dup in duplicates:
        result.append({
            'id': dup.id,
            'contact_id_1': dup.contact_id_1,
            'contact_id_2': dup.contact_id_2,
            'contact_1': {
                'id': dup.contact_1.id,
                'full_name': dup.contact_1.full_name or f"{dup.contact_1.first_name or ''} {dup.contact_1.last_name or ''}".strip(),
                'email': dup.contact_1.email,
                'phone': dup.contact_1.phone,
                'company': dup.contact_1.company,
            },
            'contact_2': {
                'id': dup.contact_2.id,
                'full_name': dup.contact_2.full_name or f"{dup.contact_2.first_name or ''} {dup.contact_2.last_name or ''}".strip(),
                'email': dup.contact_2.email,
                'phone': dup.contact_2.phone,
                'company': dup.contact_2.company,
            },
            'similarity_score': dup.similarity_score,
            'match_fields': dup.match_fields if dup.match_fields else {},  # Already a dict from jsonb
            'status': dup.status,
            'auto_detected': dup.auto_detected,
            'detected_at': dup.detected_at.isoformat() if dup.detected_at else None,
        })
    
    return {
        'duplicates': result,
        'total': len(result)
    }


@app.get('/api/contacts/{contact_id}/duplicates')
def get_contact_duplicates(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get duplicates for a specific contact.
    Returns list of potential duplicates with similarity scores.
    """
    from .models import DuplicateContact
    
    # Get duplicates where this contact is involved
    duplicates = db.query(DuplicateContact).filter(
        ((DuplicateContact.contact_id_1 == contact_id) | (DuplicateContact.contact_id_2 == contact_id)) &
        (DuplicateContact.status == 'pending')
    ).order_by(DuplicateContact.similarity_score.desc()).all()
    
    result = []
    for dup in duplicates:
        other_contact = dup.contact_2 if dup.contact_id_1 == contact_id else dup.contact_1
        result.append({
            'duplicate_id': dup.id,
            'contact': {
                'id': other_contact.id,
                'full_name': other_contact.full_name or f"{other_contact.first_name or ''} {other_contact.last_name or ''}".strip(),
                'email': other_contact.email,
                'phone': other_contact.phone,
                'company': other_contact.company,
            },
            'similarity_score': dup.similarity_score,
            'match_fields': dup.match_fields,
            'auto_detected': dup.auto_detected,
            'detected_at': dup.detected_at.isoformat() if dup.detected_at else None
        })
    
    return {'duplicates': result, 'total': len(result)}


@app.post('/api/duplicates/find')
def find_duplicates_manual(
    threshold: float = 0.75,
    contact_ids: List[int] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger duplicate detection.
    If contact_ids provided, check only those contacts.
    Otherwise, check all contacts.
    """
    from .models import DuplicateContact
    
    # Get contacts to check
    if contact_ids:
        contacts = db.query(Contact).filter(Contact.id.in_(contact_ids)).all()
    else:
        contacts = db.query(Contact).all()
    
    if len(contacts) < 2:
        return {'message': 'Need at least 2 contacts to find duplicates', 'found': 0}
    
    # Convert to dicts for comparison
    contact_dicts = []
    for c in contacts:
        contact_dicts.append({
            'id': c.id,
            'full_name': c.full_name,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'phone': c.phone,
            'company': c.company,
            'position': c.position,
        })
    
    # Find duplicates
    duplicates = duplicate_utils.find_duplicate_contacts(contact_dicts, threshold)
    
    # Save to database
    saved_count = 0
    for contact1, contact2, score, field_scores in duplicates:
        # Check if already exists
        existing = db.query(DuplicateContact).filter(
            DuplicateContact.contact_id_1 == min(contact1['id'], contact2['id']),
            DuplicateContact.contact_id_2 == max(contact1['id'], contact2['id'])
        ).first()
        
        if not existing:
            dup = DuplicateContact(
                contact_id_1=min(contact1['id'], contact2['id']),
                contact_id_2=max(contact1['id'], contact2['id']),
                similarity_score=score,
                match_fields=field_scores,  # SQLAlchemy will auto-serialize to jsonb
                status='pending',
                auto_detected=False
            )
            db.add(dup)
            saved_count += 1
    
    db.commit()
    
    return {
        'message': f'Found {len(duplicates)} potential duplicates',
        'found': len(duplicates),
        'saved': saved_count,
        'threshold': threshold
    }


@app.post('/api/contacts/{contact_id_1}/merge/{contact_id_2}')
def merge_contacts_endpoint(
    contact_id_1: int,
    contact_id_2: int,
    selected_fields: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Merge two contacts.
    selected_fields: dict mapping field_name -> 'primary' or 'secondary'
    Example: {'email': 'primary', 'phone': 'secondary', 'company': 'keep_both'}
    """
    from .models import DuplicateContact
    
    # Get contacts
    contact1 = db.query(Contact).filter(Contact.id == contact_id_1).first()
    contact2 = db.query(Contact).filter(Contact.id == contact_id_2).first()
    
    if not contact1 or not contact2:
        raise HTTPException(status_code=404, detail='One or both contacts not found')
    
    # Convert to dicts
    c1_dict = {
        'full_name': contact1.full_name,
        'first_name': contact1.first_name,
        'last_name': contact1.last_name,
        'middle_name': contact1.middle_name,
        'email': contact1.email,
        'phone': contact1.phone,
        'phone_mobile': contact1.phone_mobile,
        'phone_work': contact1.phone_work,
        'company': contact1.company,
        'position': contact1.position,
        'department': contact1.department,
        'address': contact1.address,
        'address_additional': contact1.address_additional,
        'website': contact1.website,
        'birthday': contact1.birthday,
        'comment': contact1.comment,
        'source': contact1.source,
        'status': contact1.status,
        'priority': contact1.priority,
    }
    
    c2_dict = {
        'full_name': contact2.full_name,
        'first_name': contact2.first_name,
        'last_name': contact2.last_name,
        'middle_name': contact2.middle_name,
        'email': contact2.email,
        'phone': contact2.phone,
        'phone_mobile': contact2.phone_mobile,
        'phone_work': contact2.phone_work,
        'company': contact2.company,
        'position': contact2.position,
        'department': contact2.department,
        'address': contact2.address,
        'address_additional': contact2.address_additional,
        'website': contact2.website,
        'birthday': contact2.birthday,
        'comment': contact2.comment,
        'source': contact2.source,
        'status': contact2.status,
        'priority': contact2.priority,
    }
    
    # Merge
    merged = duplicate_utils.merge_contacts(c1_dict, c2_dict, selected_fields)
    
    # Update primary contact
    for field, value in merged.items():
        if hasattr(contact1, field):
            setattr(contact1, field, value)
    
    # Update duplicate record
    dup = db.query(DuplicateContact).filter(
        DuplicateContact.contact_id_1 == min(contact_id_1, contact_id_2),
        DuplicateContact.contact_id_2 == max(contact_id_1, contact_id_2)
    ).first()
    
    if dup:
        dup.status = 'merged'
        dup.reviewed_at = func.now()
        dup.reviewed_by = current_user.id
        dup.merged_into = contact_id_1
    
    # Audit log
    create_audit_log(
        db=db,
        contact_id=contact_id_1,
        user=current_user,
        action='merged',
        entity_type='contact',
        changes={'merged_from': contact_id_2, 'selected_fields': selected_fields}
    )
    
    # Delete secondary contact
    db.delete(contact2)
    
    db.commit()
    db.refresh(contact1)
    
    return {
        'message': 'Contacts merged successfully',
        'merged_contact_id': contact_id_1,
        'deleted_contact_id': contact_id_2
    }


@app.put('/api/duplicates/{duplicate_id}/status')
def update_duplicate_status(
    duplicate_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update duplicate status: pending, reviewed, ignored
    """
    from .models import DuplicateContact
    
    if status not in ['pending', 'reviewed', 'ignored']:
        raise HTTPException(status_code=400, detail='Invalid status')
    
    dup = db.query(DuplicateContact).filter(DuplicateContact.id == duplicate_id).first()
    if not dup:
        raise HTTPException(status_code=404, detail='Duplicate not found')
    
    dup.status = status
    dup.reviewed_at = func.now()
    dup.reviewed_by = current_user.id
    
    db.commit()
    
    return {'message': 'Status updated', 'duplicate_id': duplicate_id, 'status': status}


@app.get('/api/contacts/{contact_id}/duplicates')
def get_contact_duplicates(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all potential duplicates for a specific contact.
    """
    from .models import DuplicateContact
    
    # Check contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    # Find duplicates where this contact is involved
    duplicates = db.query(DuplicateContact).filter(
        (DuplicateContact.contact_id_1 == contact_id) | 
        (DuplicateContact.contact_id_2 == contact_id)
    ).filter(
        DuplicateContact.status.in_(['pending', 'reviewed'])
    ).all()
    
    result = []
    for dup in duplicates:
        # Get the other contact
        other_id = dup.contact_id_2 if dup.contact_id_1 == contact_id else dup.contact_id_1
        other = db.query(Contact).filter(Contact.id == other_id).first()
        
        if other:
            result.append({
                'duplicate_id': dup.id,
                'other_contact': {
                    'id': other.id,
                    'full_name': other.full_name or f"{other.first_name or ''} {other.last_name or ''}".strip(),
                    'email': other.email,
                    'phone': other.phone,
                    'company': other.company,
                },
                'similarity_score': dup.similarity_score,
                'match_fields': json.loads(dup.match_fields) if dup.match_fields else {},
                'status': dup.status,
            })
    
    return {
        'contact_id': contact_id,
        'duplicates': result,
        'count': len(result)
    }


@app.post('/api/duplicates/{duplicate_id}/ignore')
def ignore_duplicate(
    duplicate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark a duplicate as ignored (convenience endpoint for marking false positives).
    """
    from .models import DuplicateContact
    
    dup = db.query(DuplicateContact).filter(DuplicateContact.id == duplicate_id).first()
    if not dup:
        raise HTTPException(status_code=404, detail='Duplicate not found')
    
    dup.status = 'ignored'
    dup.reviewed_at = func.now()
    dup.reviewed_by = current_user.id
    
    db.commit()
    
    return {'message': 'Duplicate marked as ignored', 'duplicate_id': duplicate_id}
