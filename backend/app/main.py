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
from .ocr_utils import ocr_image_fileobj, ocr_parsio  # Legacy support
from .ocr_providers import OCRManager
from . import auth_utils
from .auth_utils import get_current_active_user, get_current_admin_user
from . import schemas
import io, csv, tempfile, pandas as pd, os, uuid, json, requests, time
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

        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
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
@app.get('/contacts/', response_model=List[schemas.ContactResponse])
def list_contacts(
    q: str = Query(None, description="Search query (full-text search across all fields)"),
    company: str = Query(None, description="Filter by company"),
    position: str = Query(None, description="Filter by position"),
    tags: str = Query(None, description="Filter by tag names (comma-separated)"),
    sort_by: str = Query('id', description="Sort field: id, full_name, company, position"),
    sort_order: str = Query('desc', description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of contacts with advanced search and filtering.
    
    Parameters:
    - q: Full-text search across all fields (name, company, position, email, phone)
    - company: Filter by company (case-insensitive partial match)
    - position: Filter by position (case-insensitive partial match)
    - tags: Filter by tag names (comma-separated, e.g., "vip,client")
    - sort_by: Field to sort by (id, full_name, company, position)
    - sort_order: Sort direction (asc, desc)
    """
    from .models import Tag
    
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
    
    # Sorting
    sort_field = getattr(Contact, sort_by, Contact.id)
    if sort_order.lower() == 'asc':
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    return query.all()

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
            raw_json = json.dumps({
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
            raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
        
        # Validate OCR results
        if not any(data.values()):
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Attach stored metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['ocr_raw'] = raw_json
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        # Update contact metrics
        contacts_created_counter.inc()
        contacts_total.set(db.query(Contact).count())
        
        # Add provider info to response
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
            "ocr_provider": ocr_result['provider'],
            "ocr_confidence": ocr_result.get('confidence', 0),
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
