# 🤖 OCR Training System - Setup & Configuration Guide

**Version:** 2.17.0  
**Date:** October 21, 2025

---

## 📊 System Overview

The OCR Training System collects manual corrections from users to improve OCR accuracy over time. Each correction is stored in the database for future training/fine-tuning of OCR models.

---

## 🏗️ Architecture

### Database Model: `OCRCorrection`

**Location:** `backend/app/models/ocr.py`

```python
class OCRCorrection(Base):
    """Store OCR corrections for training and improving accuracy"""
    __tablename__ = "ocr_corrections"
    
    # IDs
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Original OCR Data
    original_text = Column(String)          # What OCR recognized
    original_box = Column(String)           # Bounding box JSON
    original_confidence = Column(Integer)   # 0-100
    
    # Corrected Data
    corrected_text = Column(String)         # User's correction
    corrected_field = Column(String)        # Field name (first_name, company, etc.)
    
    # Training Metadata
    image_path = Column(String)             # Path to image
    ocr_provider = Column(String)           # tesseract/parsio/google
    language = Column(String)               # rus/eng/rus+eng
    
    # Timestamp
    created_at = Column(DateTime)
```

### API Endpoint

**POST** `/api/contacts/{contact_id}/ocr-corrections`

```json
{
  "original_text": "Иван Иваноs",           // OCR mistake
  "corrected_text": "Иван Иванов",          // User correction
  "field_name": "first_name",                // Which field
  "original_box": "{\"x\":10,\"y\":20}",    // Optional: bounding box
  "original_confidence": 85,                 // Optional: OCR confidence
  "ocr_provider": "tesseract",               // Optional: which OCR
  "language": "rus+eng"                      // Optional: language
}
```

---

## ✅ Current Status

### Implementation Status
- ✅ **Database Model:** Implemented (`OCRCorrection`)
- ✅ **API Endpoint:** Implemented (`POST /ocr-corrections`)
- ✅ **Frontend Component:** Implemented (`OCREditorWithBlocks.js`)
- ✅ **Data Collection:** Active
- ❌ **Training Pipeline:** NOT IMPLEMENTED YET

### Bug Fixed in v2.17.0
- 🐛 **Issue:** Field name mismatch (`field_name` vs `corrected_field`)
- ✅ **Fixed:** Aligned API with database model
- ✅ **Added:** Additional metadata fields (box, confidence, provider, language)

---

## 📝 TODO: Training Pipeline Implementation

### Priority: MEDIUM (Future Release)

The current system **COLLECTS** corrections but doesn't **TRAIN** models yet.

### Steps to Implement Training:

#### 1. Export Corrections (HIGH PRIORITY)

```python
# backend/app/api/admin.py

@router.get('/ocr-corrections/export')
def export_ocr_corrections(
    limit: int = 1000,
    provider: str = None,
    language: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Export OCR corrections for training.
    Returns CSV/JSON with all corrections.
    """
    query = db.query(OCRCorrection)
    
    if provider:
        query = query.filter(OCRCorrection.ocr_provider == provider)
    if language:
        query = query.filter(OCRCorrection.language == language)
    
    corrections = query.limit(limit).all()
    
    # Convert to training format
    training_data = []
    for corr in corrections:
        training_data.append({
            'image_path': corr.image_path,
            'original': corr.original_text,
            'corrected': corr.corrected_text,
            'field': corr.corrected_field,
            'box': corr.original_box,
            'provider': corr.ocr_provider,
            'language': corr.language
        })
    
    return {
        'total': len(training_data),
        'corrections': training_data
    }
```

#### 2. Tesseract Fine-Tuning (MEDIUM PRIORITY)

**Option A: Custom Dictionary**
```python
# backend/app/ocr_utils.py

def build_custom_dictionary():
    """Build custom dictionary from corrections"""
    corrections = db.query(OCRCorrection).all()
    
    custom_words = set()
    for corr in corrections:
        # Add corrected words to dictionary
        custom_words.add(corr.corrected_text)
    
    # Write to Tesseract user-words file
    with open('/usr/share/tessdata/rus.user-words', 'w') as f:
        for word in custom_words:
            f.write(f"{word}\n")
```

**Option B: Pattern Correction**
```python
# backend/app/ocr_utils.py

def build_correction_patterns():
    """Build common OCR mistake patterns"""
    corrections = db.query(OCRCorrection).all()
    
    patterns = {}
    for corr in corrections:
        # Track: original -> corrected mappings
        patterns[corr.original_text] = corr.corrected_text
    
    # Save patterns
    import json
    with open('ocr_patterns.json', 'w') as f:
        json.dump(patterns, f, ensure_ascii=False)
```

#### 3. Post-Processing Layer (HIGH PRIORITY - EASIEST)

```python
# backend/app/ocr_utils.py

def apply_learned_corrections(text: str, field: str = None) -> str:
    """
    Apply learned corrections from database.
    This is the EASIEST and MOST PRACTICAL approach.
    """
    # Load patterns from database
    patterns = load_correction_patterns(field=field)
    
    corrected = text
    for original, corrected_version in patterns.items():
        # Apply common corrections
        corrected = corrected.replace(original, corrected_version)
    
    return corrected

def load_correction_patterns(field: str = None, min_count: int = 3):
    """
    Load common correction patterns.
    Only use patterns that appear 3+ times (confidence).
    """
    from collections import Counter
    
    query = db.query(
        OCRCorrection.original_text,
        OCRCorrection.corrected_text
    )
    
    if field:
        query = query.filter(OCRCorrection.corrected_field == field)
    
    corrections = query.all()
    
    # Count occurrences
    pattern_counts = Counter()
    pattern_map = {}
    
    for orig, corr in corrections:
        key = (orig, corr)
        pattern_counts[key] += 1
        pattern_map[orig] = corr
    
    # Only return patterns that appear multiple times
    reliable_patterns = {}
    for (orig, corr), count in pattern_counts.items():
        if count >= min_count:
            reliable_patterns[orig] = corr
    
    return reliable_patterns
```

**Integration:**
```python
# backend/app/ocr_providers.py - OCRManager.recognize()

def recognize(self, image_bytes, ...):
    # ... existing OCR code ...
    
    result = provider.recognize(image_bytes)
    
    # ✅ NEW: Apply learned corrections
    if result['data']:
        for field in ['first_name', 'last_name', 'company', 'position']:
            if field in result['data'] and result['data'][field]:
                result['data'][field] = apply_learned_corrections(
                    result['data'][field],
                    field=field
                )
    
    return result
```

#### 4. Analytics Dashboard (MEDIUM PRIORITY)

```python
# backend/app/api/admin.py

@router.get('/ocr-corrections/stats')
def get_ocr_correction_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get OCR correction statistics"""
    from sqlalchemy import func
    
    total = db.query(func.count(OCRCorrection.id)).scalar()
    
    # By provider
    by_provider = db.query(
        OCRCorrection.ocr_provider,
        func.count(OCRCorrection.id)
    ).group_by(OCRCorrection.ocr_provider).all()
    
    # By field
    by_field = db.query(
        OCRCorrection.corrected_field,
        func.count(OCRCorrection.id)
    ).group_by(OCRCorrection.corrected_field).all()
    
    # Top mistakes
    top_mistakes = db.query(
        OCRCorrection.original_text,
        OCRCorrection.corrected_text,
        func.count(OCRCorrection.id)
    ).group_by(
        OCRCorrection.original_text,
        OCRCorrection.corrected_text
    ).order_by(
        func.count(OCRCorrection.id).desc()
    ).limit(20).all()
    
    return {
        'total_corrections': total,
        'by_provider': dict(by_provider),
        'by_field': dict(by_field),
        'top_mistakes': [
            {
                'original': orig,
                'corrected': corr,
                'count': count
            }
            for orig, corr, count in top_mistakes
        ]
    }
```

---

## 🚀 Quick Start (Recommended Approach)

### Step 1: Implement Post-Processing (1-2 hours)

**This is the EASIEST and MOST EFFECTIVE approach!**

```bash
# 1. Add function to ocr_utils.py
# 2. Integrate into OCRManager
# 3. Test with existing corrections
# 4. Deploy
```

**Benefits:**
- ✅ No model retraining needed
- ✅ Works immediately
- ✅ Easy to implement
- ✅ Improves accuracy instantly
- ✅ Can be updated in real-time

### Step 2: Add Analytics Dashboard (2-3 hours)

```bash
# 1. Add stats endpoint to admin.py
# 2. Create frontend dashboard
# 3. Show correction trends
```

### Step 3: Export Function (30 minutes)

```bash
# 1. Add export endpoint
# 2. Test CSV/JSON export
```

### Step 4: Advanced Training (Future)

- Tesseract fine-tuning (requires expertise)
- ML model training (requires data science)
- Custom model development (long-term project)

---

## 📊 Expected Results

### Current State (v2.17.0)
- ✅ Corrections are being collected
- ✅ Stored in database
- ❌ Not being used for improvement

### After Post-Processing Implementation
- ✅ Corrections applied automatically
- ✅ Common mistakes fixed instantly
- ✅ Accuracy improves over time
- ✅ No manual intervention needed

### Estimated Improvement
- 📈 **5-15% accuracy gain** from post-processing
- 📈 **Compound effect** as more corrections accumulate
- 📈 **Field-specific** improvements (company names, positions)

---

## 🧪 Testing

### Manual Test

1. **Create a correction:**
```bash
curl -X POST http://localhost:8000/api/contacts/1/ocr-corrections \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "Иваноs",
    "corrected_text": "Иванов",
    "field_name": "last_name"
  }'
```

2. **Check database:**
```sql
SELECT * FROM ocr_corrections ORDER BY created_at DESC LIMIT 10;
```

3. **View stats:**
```bash
curl http://localhost:8000/api/ocr-corrections/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📋 Action Items

### Immediate (v2.17.0)
- [x] Fix field name bug (`field_name` → `corrected_field`)
- [x] Add metadata fields
- [x] Document system
- [ ] Test correction endpoint

### Short-term (v2.18.0)
- [ ] Implement post-processing layer (HIGH PRIORITY) ⭐
- [ ] Add analytics dashboard
- [ ] Add export endpoint
- [ ] Test with real corrections

### Long-term (Future)
- [ ] Tesseract fine-tuning
- [ ] ML model integration
- [ ] Automated training pipeline
- [ ] A/B testing for improvements

---

## 📞 Support

For questions about OCR training:
1. Check this document
2. Review `backend/app/models/ocr.py`
3. Check `backend/app/api/contacts.py` (OCR endpoints)
4. Review `OCREditorWithBlocks.js` (frontend)

---

**Status:** ✅ Foundation Ready, Training Pipeline TODO  
**Priority:** Medium (not blocking production)  
**Estimated Implementation:** 4-6 hours for full pipeline
