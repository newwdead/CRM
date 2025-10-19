from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update, text
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from .database import engine, Base, get_db
from .models import Contact, AppSetting
from .ocr_utils import ocr_image_fileobj, ocr_parsio  # Legacy support
from .ocr_providers import OCRManager
import io, csv, tempfile, pandas as pd, os, uuid, json, requests, time
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация OCR Manager
ocr_manager = OCRManager()

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

backfill_uids_safe()

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
def get_telegram_settings(db: Session = Depends(get_db)):
    return {
        'enabled': get_setting(db, 'tg.enabled', 'false') == 'true',
        'token': get_setting(db, 'tg.token', None),
        'allowed_chats': get_setting(db, 'tg.allowed_chats', ''),
        'provider': get_setting(db, 'tg.provider', 'auto') or 'auto',
    }

@app.put('/settings/telegram')
def put_telegram_settings(data: TelegramSettings, db: Session = Depends(get_db)):
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
@app.get('/contacts/')
def list_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).order_by(Contact.id.desc()).all()

@app.get('/contacts/uid/{uid}')
def get_contact_by_uid(uid: str, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.uid == uid).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    return contact

@app.post('/contacts/')
def create_contact(data: ContactCreate, db: Session = Depends(get_db)):
    payload = data.dict()
    if not payload.get('uid'):
        payload['uid'] = uuid.uuid4().hex
    contact = Contact(**payload)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

@app.put('/contacts/{contact_id}')
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db)):
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
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Not found')
    db.delete(contact)
    db.commit()
    return {'deleted': contact_id}

# --- Upload OCR ---
@app.post('/upload/')
def upload_card(
    file: UploadFile = File(...),
    provider: str = Query('auto', enum=['auto', 'tesseract', 'parsio', 'google']),
    db: Session = Depends(get_db)
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
            ocr_result = ocr_manager.recognize(
                ocr_input,
                filename=file.filename,
                preferred_provider=preferred
            )
            
            data = ocr_result['data']
            raw_json = json.dumps({
                'provider': ocr_result['provider'],
                'confidence': ocr_result.get('confidence', 0),
                'raw_data': ocr_result.get('raw_data'),
                'raw_text': ocr_result.get('raw_text'),
            }, ensure_ascii=False)
            
            logger.info(f"OCR successful with {ocr_result['provider']}, confidence: {ocr_result.get('confidence', 0)}")
            
        except Exception as e:
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
def export_csv(ids: Optional[str] = Query(None), db: Session = Depends(get_db)):
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
def export_xlsx(ids: Optional[str] = Query(None), db: Session = Depends(get_db)):
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
def import_contacts(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
def delete_bulk(ids: list[int] = Body(...), db: Session = Depends(get_db)):
    db.query(Contact).filter(Contact.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {'deleted': len(ids)}

# --- Bulk update ---
@app.put('/contacts/update_bulk')
def update_bulk(payload: dict, db: Session = Depends(get_db)):
    ids = payload.get('ids', [])
    fields = payload.get('fields', {})
    if not ids or not fields:
        raise HTTPException(status_code=400, detail='ids and fields required')
    stmt = update(Contact).where(Contact.id.in_(ids)).values(**fields)
    db.execute(stmt)
    db.commit()
    return {'updated': len(ids)}
