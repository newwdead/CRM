"""
Export and Import API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
import csv
import pandas as pd
import uuid
import os
import logging

from ..database import get_db
from ..models import User, Contact
from ..auth_utils import get_current_active_user
from ..utils import create_audit_log

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/contacts/export')
def export_csv(
    ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export contacts to CSV"""
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
    writer.writerow(['id', 'uid', 'full_name', 'company', 'position', 'email', 'phone', 'address', 'comment', 'website', 'photo_path'])
    
    for c in contacts:
        writer.writerow([
            c.id,
            c.uid or '',
            c.full_name or '',
            c.company or '',
            c.position or '',
            c.email or '',
            c.phone or '',
            c.address or '',
            c.comment or '',
            c.website or '',
            c.photo_path or ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=contacts.csv'}
    )


@router.get('/contacts/export/xlsx')
def export_xlsx(
    ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export contacts to Excel (XLSX)"""
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
    return StreamingResponse(
        buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )


@router.get('/contacts/{contact_id}/pdf')
def export_contact_pdf(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a PDF business card for a contact"""
    from reportlab.lib.pagesizes import letter
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


@router.post('/contacts/import')
def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import contacts from CSV or Excel file"""
    ext = (file.filename or '').split('.')[-1].lower()
    
    if ext == 'csv':
        df = pd.read_csv(file.file)
    elif ext in ('xls', 'xlsx'):
        df = pd.read_excel(file.file)
    else:
        raise HTTPException(status_code=400, detail='Unsupported file format')
    
    added = 0
    for _, row in df.iterrows():
        obj = {}
        for k in ['full_name', 'company', 'position', 'email', 'phone', 'address', 'comment']:
            val = row.get(k)
            if pd.isna(val):
                val = None
            obj[k] = val
        
        db.add(Contact(**obj))
        added += 1
    
    db.commit()
    return {'imported': added}


@router.post('/contacts/delete_bulk')
def delete_bulk(
    ids: list[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete multiple contacts at once"""
    db.query(Contact).filter(Contact.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {'deleted': len(ids)}


@router.put('/contacts/update_bulk')
def update_bulk(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update multiple contacts at once"""
    ids = payload.get('ids', [])
    fields = payload.get('fields', {})
    
    if not ids or not fields:
        raise HTTPException(status_code=400, detail='ids and fields required')
    
    db.query(Contact).filter(Contact.id.in_(ids)).update(fields, synchronize_session=False)
    db.commit()
    
    return {'updated': len(ids)}

