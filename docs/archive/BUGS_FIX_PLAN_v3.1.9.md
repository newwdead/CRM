# Bug Fixes Plan v3.1.9

## 3 New Bugs Found After Testing

### Bug #1: OCR Upload - "No text could be extracted from the image"
**Priority:** P1 (Critical)  
**Component:** Backend OCR Processing  
**Root Cause:** OCR providers configuration or file upload issue

**Diagnosis Needed:**
- Check if file uploads correctly
- Check OCR provider availability (only Tesseract available)
- Test with different image types

### Bug #2: OCR Editor - Image not displaying, window too narrow
**Priority:** P2 (High)  
**Component:** Frontend UI  
**Root Cause:** CSS styling issues in ImageViewer and OCREditorContainer

**Fixed:**
- Changed `maxWidth: '1200px'` → `maxWidth: '100%', width: '100%'` in OCREditorContainer
- Changed `maxHeight: '600px'` → `maxHeight: '80vh', minHeight: '400px'` in ImageViewer

### Bug #3: Admin Panel Services - "Unexpected token '<', is not valid JSON"
**Priority:** P1 (Critical)  
**Component:** Frontend/Backend API  
**Root Cause:** Frontend receives HTML instead of JSON (likely 404 or auth error)

**Diagnosis:**
- Endpoint exists: `/services/status` (requires admin auth)
- Frontend calls: `/api/services/status`
- Nginx proxies: `/api/` → backend `/`
- Result: Should be `/services/status` on backend

**Issue:** Frontend might be receiving HTML error page instead of JSON error response.

**Possible Causes:**
1. Token not sent correctly
2. Nginx returns HTML 404
3. CORS or redirect issue

## Action Plan

1. ✅ Fix OCR Editor UI (CSS)
2. ⏳ Investigate Services API error
3. ⏳ Test OCR upload with logs
4. ⏳ Deploy all fixes

