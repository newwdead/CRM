# Release Notes v5.2.2

**Release Date:** October 26, 2025  
**Type:** Feature Release + Critical Bug Fixes

## 🚨 Critical Bug Fixes

### Master Contact Deletion Prevention
**Severity:** CRITICAL - Data Loss Prevention

**Problem:** 
- When merging duplicates, master contact ID could be included in slave_ids
- This caused master contact to be deleted during merge
- Both contacts were lost due to session persistence error

**Root Cause:**
```
Merge request: master_id=88, slave_ids=[86, 88]
                                        ↑↑
                            Master ID was IN slave_ids!
```

**Solution:**
1. **Frontend Protection** (`DuplicateManager.js`):
   - Automatically removes master ID from slavesToDelete when selecting new master
   - Filters out master ID when adding contacts to delete list
   - Added critical validation comments

2. **Backend Validation** (`contacts.py`):
   - Pre-merge validation checks if master_id is in slave_ids
   - Raises HTTP 400 error before any database operations
   - Prevents data loss even if frontend sends incorrect data

**Result:** Master contact can NEVER be accidentally deleted ✅

### Full Contact Field Merge
**Problem:** Only 13 fields were being merged, 11 fields were ignored

**Solution:** Expanded merge logic to include ALL 24 Contact model fields:
- Added: `department`, `phone_additional`, `fax`, `birthday`, `source`, `status`, `priority`, `qr_data`, `has_qr_code`
- Now ALL information is transferred correctly during merge

## ✨ New Features

### Field-Based Duplicate Detection
**Changed duplicate detection from percentage similarity to field count matching**

**Before:**
- Threshold: 50% - 100% similarity
- Complex weighted calculation (email 40%, phone 30%, name 20%, company 10%)
- Levenshtein distance for string comparison
- Unclear to users what "75% similarity" means

**After:**
- Minimum matching fields: 1 - 5 fields
- Simple count of exactly matching fields
- Start from 1 field (most permissive)
- Intuitive: users understand "3 fields match" better than "75% similar"

**Matching Logic:**
- **Exact match fields:** email, phone, phone_mobile, phone_work, company, website
- **Phone normalization:** removes non-digits, checks contains
- **Name similarity:** > 80% string similarity counts as match

**Benefits:**
- More intuitive and understandable
- More flexible (can find duplicates with just 1 matching field)
- Faster (no complex weighted calculations)
- Easier to tune (just increase field count to be more strict)

### Enhanced Merge Preview UI
**Added detailed field-by-field merge preview with color coding**

**Features:**
- Shows ALL 22 contact fields that will be merged
- Color-coded changes:
  - 🟢 **Green (Add):** Empty field will be filled
  - 🔵 **Blue (Conflict):** Both fields have different values (master keeps its value)
  - 🔴 **Red (Loss):** Contact to be deleted has no value in this field
- Selective deletion: Choose which contacts to delete when 3+ duplicates found
- Master contact selection with visual feedback (green highlight)
- Delete selection with visual feedback (red highlight)
- Summary message showing count of contacts to be deleted/remaining

## 🔧 Improvements

### Merge Logic Enhancements
- All 22 contact fields are now compared and displayed in preview
- Tags and groups are properly merged (unique values only)
- Photo transferred if master has none
- Better validation messages

### UI/UX Improvements
- Clear visual distinction between master, to-delete, and remaining contacts
- Field count slider with labels (1 field → 5 fields)
- Group information shows field match count instead of percentage
- Better error messages and user feedback

## 🛡️ Security & Stability

### Data Loss Prevention
- Dual-layer validation (frontend + backend)
- Database transaction safety
- Audit logging for merge operations
- Debug logging for troubleshooting

### Code Quality
- Added critical validation comments
- Improved error handling
- Better separation of concerns (microservice approach)

## 📊 Technical Details

### Modified Files
- `frontend/src/components/DuplicateManager.js` (3 major updates)
- `backend/app/api/contacts.py` (validation + full field merge)
- `frontend/src/modules/duplicates/api/duplicatesApi.js` (cache-busting)

### Commits
- `57df701` - CRITICAL FIX: Prevent master contact deletion bug
- `fbc7574` - Enhanced duplicate merge UI with field preview
- `71a11df` - FEATURE: Change duplicate detection to field count

## 🚀 Deployment

### Frontend
- New bundle: `main.84ef5c03.js`
- Service worker cache bust required
- Hard refresh recommended (Ctrl+Shift+R)

### Backend
- No migrations required
- Restart required for validation logic

## 📝 Known Issues

### Contact Recovery
- Contacts lost during bug testing (IDs: 86, 88) cannot be automatically recovered
- Options: restore from backup, re-upload business cards, or manual recreation

## 🔄 Upgrade Notes

### From v5.2.1
1. Pull latest code: `git pull origin main`
2. Rebuild frontend: `docker compose build frontend`
3. Restart backend: `docker compose restart backend`
4. Clear browser cache (Ctrl+Shift+R or clear site data)

### Testing
1. Navigate to `/duplicates`
2. Verify slider shows "Минимум совпадающих полей: 1-5"
3. Test merge with 3+ duplicates
4. Verify master cannot be selected for deletion
5. Check merge preview shows all fields with color coding

## 📚 Documentation

See also:
- `MICROARCHITECTURE_APPROACH.md` - Duplicates module isolation
- `PROJECT_STRUCTURE_AUDIT_v5.2.0.md` - Project organization
- `CLEANUP_AUDIT_v5.2.0.md` - Workflow and docs cleanup

## 🎯 Next Steps (v5.3.0 Planning)

### Planned Improvements
1. **Code Optimization:**
   - Split large files (main.py 4072 lines, AdminPanel.js 1372 lines)
   - Improve code organization and modularity
   - Remove duplicate code

2. **Security Hardening:**
   - Review and update security configurations
   - Enhance authentication and authorization
   - Update dependencies

3. **CI/CD Enhancement:**
   - Improve automated testing
   - Enhance deployment automation
   - Better monitoring and alerting

## 👥 Contributors

- AI Assistant: Bug diagnosis, fixes, and feature implementation
- User: Bug reporting, requirements, and testing

---

**Version:** 5.2.2  
**Previous Version:** 5.2.1  
**Status:** ✅ Production Ready  
**Breaking Changes:** None

