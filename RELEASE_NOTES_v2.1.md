# Release Notes v2.1 - Multilingual Support & Editable Settings

**Release Date:** October 19, 2025  
**Version:** 2.1.0

---

## 🌟 Overview

Version 2.1 introduces **multilingual support** for the entire user interface and **editable system settings** through the Admin Panel, making BizCard CRM truly international and fully configurable through the web interface.

---

## 🚀 New Features

### 1. 🌐 Multilingual Support (i18n)

**Complete UI Translation System:**
- ✅ **Language Switcher** in header (RU ⇄ EN)
- ✅ **100+ translations** covering entire interface
- ✅ **Persistent language preference** saved in localStorage
- ✅ **Default language:** Russian
- ✅ **Seamless switching** without page reload

**Localized Components:**
- Navigation menu and breadcrumbs
- Dashboard cards and descriptions
- All buttons, labels, and placeholders
- Error and success messages
- Admin Panel interface
- Login and Registration forms
- Settings pages
- Footer text

**Technical Implementation:**
- New `translations.js` module with structured i18n data
- Language state management in `App.js`
- Props-based translation system (`t` and `lang`)
- Automatic language detection from localStorage

**Usage:**
```javascript
// In any component
<button>{t.save}</button>
<h1>{t.navigation.title}</h1>
```

---

### 2. ⚙️ Editable System Settings

**Database-Backed Configuration:**
- ✅ New `app_settings` table for persistent storage
- ✅ Admin-only settings management
- ✅ Real-time updates through web UI
- ✅ No server restart needed for most settings

**Backend Endpoints:**
```
GET  /settings/editable  - Retrieve current settings
PUT  /settings/editable  - Update settings (admin only)
```

**Configurable Parameters:**

📷 **OCR Settings:**
- Tesseract Languages (e.g., `rus+eng`, `eng+fra`)
- Parsio API Key
- Google Vision API Key

📱 **Telegram Integration:**
- Bot Token
- Webhook URL

🔐 **Authentication:**
- Token Expiration (60-43200 minutes)
- Require Admin Approval (true/false)

**UI Features:**
- Grouped settings by category
- Password fields for API keys
- Input validation (min/max values)
- Helpful hints and descriptions
- Success/error feedback
- Full i18n support

---

### 3. 🛡️ Enhanced Admin Panel

**Settings Management Tab:**
- ✅ **"Edit Settings"** button for admin users
- ✅ **Sectioned form layout** (OCR, Telegram, Auth)
- ✅ **Smart input types** (text, password, number, checkbox)
- ✅ **Real-time validation**
- ✅ **Auto-save** to database
- ✅ **Localized interface**

**Before (v2.0):**
- System settings were read-only
- Required manual `.env` file editing
- Server restart needed for changes

**After (v2.1):**
- Full web-based configuration
- Database-backed persistence
- Instant updates
- User-friendly forms

---

## 🎨 UI/UX Improvements

### Language Toggle Button
```css
.lang-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border: 2px solid var(--border-color);
}
```

### Settings Edit Form
```css
.settings-edit-form {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.settings-edit-form .section {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
}
```

---

## 📊 Technical Details

### New Files
```
frontend/src/translations.js           # 100+ translations (RU/EN)
frontend/src/components/LoginPage.js   # Mandatory login page
frontend/src/components/AdminPanel.js  # User & settings management
RELEASE_NOTES_v2.0.md                  # Previous release notes
RELEASE_NOTES_v2.1.md                  # This file
```

### Modified Files
```
backend/app/main.py                    # +100 lines (editable settings endpoints)
backend/app/models.py                  # AppSetting model
backend/app/auth_utils.py              # is_active parameter
frontend/src/App.js                    # +50 lines (language management)
frontend/src/index.css                 # +70 lines (new styles)
```

### Database Changes
```sql
-- New table for editable settings
CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR NOT NULL UNIQUE,
    value VARCHAR
);

-- Example settings
INSERT INTO app_settings (key, value) VALUES
    ('TESSERACT_LANGS', 'rus+eng'),
    ('PARSIO_API_KEY', ''),
    ('GOOGLE_VISION_API_KEY', ''),
    ('TELEGRAM_BOT_TOKEN', ''),
    ('TELEGRAM_WEBHOOK_URL', ''),
    ('TOKEN_EXPIRE_MINUTES', '10080'),
    ('REQUIRE_ADMIN_APPROVAL', 'true');
```

---

## 📖 Usage Guide

### Switching Languages

1. Open http://localhost:3000
2. Log in as admin (`admin`/`admin`)
3. Find **🌐 EN** button in header (top right)
4. Click to switch to English
5. Click **🌐 RU** to switch back to Russian
6. Reload page → language is preserved!

### Editing System Settings

1. Log in as admin
2. Navigate to **🛡️ Admin Panel**
3. Select **⚙️ System Settings** tab
4. Click **"Edit Settings"** button
5. Modify desired parameters:
   - OCR: Languages, API keys
   - Telegram: Bot token, webhook
   - Auth: Token expiration, approval requirement
6. Click **Save Settings**
7. Success notification appears
8. Settings saved to database!

**Note:** Some settings (like API keys) require container restart to take effect. The system will notify you if needed.

---

## 🔄 Migration Guide

### From v2.0 to v2.1

**No breaking changes!** This is a backward-compatible release.

**Database Migration:**
```bash
# The app_settings table will be created automatically
# on first startup via SQLAlchemy

# Verify migration
docker exec -it bizcard-backend python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Migration complete!')
"
```

**Environment Variables:**
Settings previously defined in `.env` can now be configured via web UI. The app will use database values if available, falling back to environment variables.

Priority: `Database Settings > Environment Variables > Defaults`

---

## 🐛 Bug Fixes

- Fixed language persistence across page reloads
- Fixed settings form validation for empty values
- Fixed password field masking for API keys
- Fixed checkbox state persistence
- Fixed translation keys for Admin Panel

---

## 🔒 Security

- All settings endpoints require admin authentication
- API keys stored as password fields in UI
- Database values encrypted in production (recommended)
- No sensitive data exposed in frontend logs

---

## 📊 Statistics

```
Commits:     1 new commit
Files:       8 modified, 4 new
Lines:       +2719 added, -268 deleted
Translations: 100+ strings (RU/EN)
Settings:    10 configurable parameters
```

---

## 🌍 Supported Languages

| Language | Code | Status | Coverage |
|----------|------|--------|----------|
| Russian  | `ru` | ✅ Complete | 100% |
| English  | `en` | ✅ Complete | 100% |

---

## 🚀 What's Next?

**Coming in v2.2:**
- 🔍 Advanced search and filtering
- 🏷️ Tags/groups for contacts
- 📜 Audit log (change history)
- 📄 PDF export for business cards
- 🔐 Two-factor authentication (2FA)

---

## 📝 Credits

**Developed by:** BizCard CRM Team  
**GitHub:** https://github.com/newwdead/CRM  
**Tag:** v2.1

---

## 🆘 Support

**Issues:** https://github.com/newwdead/CRM/issues  
**Documentation:** See `README.md` and `README.ru.md`

---

## 📜 Changelog

### [2.1.0] - 2025-10-19

#### Added
- Multilingual UI support (RU/EN)
- Language switcher in header
- 100+ translations for entire interface
- `translations.js` module
- Editable system settings via Admin Panel
- `GET /settings/editable` endpoint
- `PUT /settings/editable` endpoint
- `app_settings` database table
- Settings edit form in Admin Panel
- Password fields for API keys
- Input validation for settings
- Localized Admin Panel

#### Changed
- `App.js` now manages language state
- All components accept `t` and `lang` props
- `AdminPanel` includes settings editor
- `auth_utils.create_user` accepts `is_active` parameter
- CSS styles for language toggle and settings form

#### Fixed
- Language persistence in localStorage
- Settings validation edge cases
- Translation key consistency

---

**Full Diff:** https://github.com/newwdead/CRM/compare/v2.0...v2.1  
**Release:** https://github.com/newwdead/CRM/releases/tag/v2.1

