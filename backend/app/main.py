from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update, text
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from .database import engine, Base, get_db
from .models import Contact
from .ocr_utils import ocr_image_fileobj, ocr_parsio
import io, csv, tempfile, pandas as pd, os, uuid, json

# Create tables if they don't exist
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Database connection failed: {e}")
    # Don't exit, let the application start and retry on first request
    
# Ensure new columns exist (lightweight migration)
try:
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
    print("Schema ensured: comment, uid, website, photo_path, ocr_raw columns present")
except Exception as e:
    print(f"Schema ensure failed: {e}")

# Backfill UID for existing contacts without one
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

# --- Health ---
@app.get('/health')
def health():
    return {'status':'ok'}

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
    provider: str = Query('tesseract', enum=['tesseract','parsio']),
    db: Session = Depends(get_db)
):
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size
        # v1.2: allow up to 20MB for Parsio, 10MB for Tesseract
        limit = 20 * 1024 * 1024 if provider == 'parsio' else 10 * 1024 * 1024
        # Read up to limit + 1 byte to detect overflow, then reset pointer before OCR
        head = file.file.read(limit + 1)
        if len(head) > limit:
            raise HTTPException(status_code=400, detail=(
                "File too large. Maximum size is 20MB for Parsio" if provider == 'parsio'
                else "File too large. Maximum size is 10MB"
            ))
        file.file.seek(0)
        # Save a copy of the uploaded file to disk
        content = file.file.read()
        file.file.seek(0)
        safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload')}"
        save_path = os.path.join('uploads', safe_name)
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # Run OCR via selected provider
        if provider == 'parsio':
            try:
                ocr_data = ocr_parsio(io.BytesIO(content), filename=file.filename)
                raw_json = json.dumps(ocr_data, ensure_ascii=False)
                data = ocr_data
            except Exception as e:
                # fallback to Tesseract on Parsio failure
                ocr_text = ocr_image_fileobj(io.BytesIO(content))
                raw_json = json.dumps(ocr_text, ensure_ascii=False)
                data = ocr_text
        else:
            ocr_text = ocr_image_fileobj(io.BytesIO(content))
            raw_json = json.dumps(ocr_text, ensure_ascii=False)
            data = ocr_text
        
        # Validate OCR results
        if not any(data.values()):
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # attach stored metadata
        data['uid'] = uuid.uuid4().hex
        data['photo_path'] = safe_name
        data['ocr_raw'] = raw_json
        contact = Contact(**data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

# --- Export CSV ---
@app.get('/contacts/export')
def export_csv(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','uid','full_name','company','position','email','phone','address','comment','website','photo_path'])
    for c in contacts:
        writer.writerow([c.id, c.uid or '', c.full_name or '', c.company or '', c.position or '', c.email or '', c.phone or '', c.address or '', c.comment or '', c.website or '', c.photo_path or ''])
    output.seek(0)
    return StreamingResponse(output, media_type='text/csv', headers={'Content-Disposition':'attachment; filename=contacts.csv'})

# --- Export XLSX ---
@app.get('/contacts/export/xlsx')
def export_xlsx(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
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
