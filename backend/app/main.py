from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update, text
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
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

# Prometheus metrics
ocr_processing_counter = Counter('ocr_processing_total', 'Total OCR processing requests', ['provider', 'status'])
ocr_processing_time = Histogram('ocr_processing_seconds', 'OCR processing time', ['provider'])
qr_scan_counter = Counter('qr_scan_total', 'QR code scans', ['status'])
contacts_total = Gauge('contacts_total', 'Total number of contacts')
contacts_created_counter = Counter('contacts_created_total', 'Total contacts created')
users_total = Gauge('users_total', 'Total number of users')
auth_attempts_counter = Counter('auth_attempts_total', 'Authentication attempts', ['status'])
telegram_messages_counter = Counter('telegram_messages_total', 'Telegram messages processed', ['status'])

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

        # Save to uploads
        safe_name = f"{uuid.uuid4().hex}_tg_{os.path.basename(file_path)}"
        save_path = os.path.join('uploads', safe_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # Create thumbnail
        thumbnail_full_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_full_path)

        # OCR (downscale first to reduce memory footprint)
        provider = get_setting(db, 'tg.provider', 'auto') or 'auto'
        ocr_input = downscale_image_bytes(content, max_side=2000)
        
        # Use OCRManager with automatic fallback
        preferred = None if provider == 'auto' else provider
        try:
            ocr_result = ocr_manager.recognize(
                ocr_input,
                filename=os.path.basename(file_path),
                preferred_provider=preferred
            )
            
            data = ocr_result['data']
            raw_json = json.dumps({
                'provider': ocr_result['provider'],
                'confidence': ocr_result.get('confidence', 0),
                'raw_data': ocr_result.get('raw_data'),
                'raw_text': ocr_result.get('raw_text'),
            }, ensure_ascii=False)
            
            logger.info(f"Telegram OCR successful with {ocr_result['provider']}")
            
        except Exception as e:
            logger.error(f"Telegram OCR failed: {e}")
            raise HTTPException(status_code=500, detail=f'OCR failed: {str(e)}')

        if not any(data.values()):
            raise HTTPException(status_code=400, detail='OCR extracted no data')

        # Enhance OCR data: parse names, detect company/position swap
        data = ocr_utils.enhance_ocr_result(data)
        
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return {'created_id': contact.id}
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
    payload = data.dict()
    if not payload.get('uid'):
        payload['uid'] = uuid.uuid4().hex
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
    
    return contact

@app.put('/contacts/{contact_id}')
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    
    update_data = data.dict(exclude_unset=True)
    
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

# --- Upload OCR ---
@app.post('/upload/')
@limiter.limit("60/minute")  # 60 uploads per minute per IP
def upload_card(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
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
        
        # Save uploaded file to disk
        content = file.file.read()
        file.file.seek(0)
        safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload')}"
        save_path = os.path.join('uploads', safe_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # Create thumbnail (200x200, quality 85%)
        thumbnail_full_path = create_thumbnail(save_path, size=(200, 200), quality=85)
        thumbnail_name = os.path.basename(thumbnail_full_path)
        
        # STEP 1: Try QR code scanning first (priority)
        data = None
        raw_json = None
        recognition_method = None
        
        logger.info("Attempting QR code scan...")
        qr_data = qr_utils.process_image_with_qr(content)
        
        if qr_data and any(qr_data.values()):
            # QR code found and parsed successfully
            data = qr_data
            recognition_method = 'qr_code'
            raw_json = json.dumps({
                'method': 'qr_code',
                'data': qr_data
            }, ensure_ascii=False)
            qr_scan_counter.labels(status='success').inc()
            logger.info(f"QR code extracted successfully: {list(data.keys())}")
        else:
            # No QR code or empty data - fallback to OCR
            qr_scan_counter.labels(status='not_found').inc()
            logger.info("No QR code found, falling back to OCR...")
            
            # Prepare data for OCR (downscale to reduce memory footprint)
            ocr_input = downscale_image_bytes(content, max_side=2000)

            # Run OCR via OCRManager with automatic fallback
            preferred = None if provider == 'auto' else provider
            
            try:
                # Track OCR processing time
                start_time = time.time()
                ocr_result = ocr_manager.recognize(
                    ocr_input,
                    filename=file.filename,
                    preferred_provider=preferred
                )
                processing_time = time.time() - start_time
                
                # Update Prometheus metrics
                used_provider = ocr_result['provider']
                ocr_processing_time.labels(provider=used_provider).observe(processing_time)
                ocr_processing_counter.labels(provider=used_provider, status='success').inc()
                
                data = ocr_result['data']
                recognition_method = ocr_result['provider']
                raw_json = json.dumps({
                    'method': 'ocr',
                    'provider': ocr_result['provider'],
                    'confidence': ocr_result.get('confidence', 0),
                    'raw_data': ocr_result.get('raw_data'),
                    'raw_text': ocr_result.get('raw_text'),
                }, ensure_ascii=False)
                
                logger.info(f"OCR successful with {ocr_result['provider']}, confidence: {ocr_result.get('confidence', 0)}, time: {processing_time:.2f}s")
                
            except Exception as e:
                # Track OCR failure
                ocr_processing_counter.labels(provider=preferred or 'auto', status='failed').inc()
                logger.error(f"OCR failed: {e}")
                raise HTTPException(status_code=500, detail=f"OCR/QR extraction failed: {str(e)}")
        
        # Validate results
        if not data or not any(data.values()):
            raise HTTPException(status_code=400, detail="No text could be extracted from the image (neither QR nor OCR)")
        
        # Enhance data: parse names, detect company/position swap
        data = ocr_utils.enhance_ocr_result(data)
        
        # Attach stored metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['thumbnail_path'] = thumbnail_name
        data['ocr_raw'] = raw_json
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        # Update contact metrics
        contacts_created_counter.inc()
        contacts_total.set(db.query(Contact).count())
        
        # Add recognition method info to response
        contact_dict = {
            "id": contact.id,
            "uid": contact.uid,
            "full_name": contact.full_name,
            "company": contact.company,
            "position": contact.position,
            "email": contact.email,
            "phone": contact.phone,
            "address": contact.address,
            "comment": contact.comment,
            "website": contact.website,
            "photo_path": contact.photo_path,
            "thumbnail_path": contact.thumbnail_path,
            "recognition_method": recognition_method,
        }
        
        return contact_dict
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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
