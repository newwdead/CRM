# Release Notes v2.2 - Advanced Features & Analytics

**Release Date:** October 19, 2025  
**Version:** 2.2.0

---

## 🌟 Overview

Version 2.2 introduces **advanced contact management features**, including powerful search and filtering, organizational tools (tags and groups), comprehensive audit logging, PDF export capabilities, and detailed analytics. This release transforms BizCard CRM into a feature-rich, enterprise-ready contact management solution.

---

## 🚀 Major New Features

### 1. 🔍 Advanced Search & Filtering

**Server-Side Search:**
- ✅ **Full-text search** across all contact fields
- ✅ **Field-specific filters**: company, position
- ✅ **Multi-field sorting**: id, full_name, company, position
- ✅ **Sort order control**: ascending/descending
- ✅ **Real-time filtering** with auto-refresh

**Backend API:**
```
GET /contacts/?q=search&company=acme&position=ceo&sort_by=full_name&sort_order=asc
```

**Frontend UI:**
- Advanced filters panel with toggle
- Clear filters button
- Search input with instant results
- Company and position filter inputs
- Sorting controls (field + direction)

**Performance:**
- Server-side filtering for better scalability
- Database-level queries (no client-side filtering)
- Optimized for large contact lists

---

### 2. 🏷️ Tags System

**Flexible Contact Labeling:**
- ✅ **Create custom tags** with names and colors
- ✅ **Many-to-many relationship** (contacts ↔ tags)
- ✅ **Assign multiple tags** to contacts
- ✅ **Filter contacts by tags**
- ✅ **Tag management** (create, update, delete)

**Backend Endpoints:**
```
GET    /tags/                     # List all tags
POST   /tags/                     # Create tag
PUT    /tags/{id}                 # Update tag
DELETE /tags/{id}                 # Delete tag (admin only)
POST   /contacts/{id}/tags        # Add tags to contact
DELETE /contacts/{id}/tags/{id}   # Remove tag from contact
GET    /contacts/?tags=vip,client # Filter by tags
```

**Data Model:**
- Tag: name (unique), color (hex), created_at
- Association table: contact_tags (many-to-many)
- Cascade deletion support

**Use Cases:**
- Mark VIP contacts
- Categorize by industry
- Flag for follow-up
- Group by event/campaign

---

### 3. 📁 Groups System

**Organizational Structure:**
- ✅ **Create contact groups** with descriptions
- ✅ **Many-to-many relationship** (contacts ↔ groups)
- ✅ **Assign contacts to groups**
- ✅ **Filter contacts by groups**
- ✅ **Group management** (create, update, delete)

**Backend Endpoints:**
```
GET    /groups/                        # List all groups
POST   /groups/                        # Create group
PUT    /groups/{id}                    # Update group
DELETE /groups/{id}                    # Delete group (admin only)
POST   /contacts/{id}/groups           # Add groups to contact
DELETE /contacts/{id}/groups/{id}      # Remove group from contact
GET    /contacts/?groups=partners,leads # Filter by groups
```

**Data Model:**
- Group: name (unique), description, color (hex), created_at
- Association table: contact_groups (many-to-many)
- Cascade deletion support

**Use Cases:**
- Organize by department
- Separate customers vs. partners
- Group by region/location
- Segment by project

---

### 4. 📜 Audit Log System

**Comprehensive Change Tracking:**
- ✅ **Automatic logging** of all contact changes
- ✅ **User attribution** (who made the change)
- ✅ **Timestamp tracking** (when it happened)
- ✅ **Change details** (JSON storage of modifications)
- ✅ **Multiple action types** (created, updated, deleted, tag_added, etc.)

**Backend Endpoints:**
```
GET /contacts/{id}/history  # View contact change history
GET /audit/recent           # View recent logs (admin only)
```

**Logged Actions:**
- Contact created
- Contact updated
- Contact deleted
- Tag added/removed
- Group added/removed
- PDF exported

**Data Model:**
- AuditLog: contact_id, user_id, username, action, entity_type, changes (JSON), timestamp
- Preserved username even if user is deleted
- Indexed for fast queries

**Use Cases:**
- Track who modified a contact
- View change history
- Compliance and auditing
- Rollback information
- Activity monitoring

---

### 5. 📄 PDF Export

**Business Card Generation:**
- ✅ **Generate PDF business cards** for contacts
- ✅ **Professional layout** with contact information
- ✅ **Photo embedding** (if available)
- ✅ **Downloadable format**
- ✅ **Audit logging** for exports

**Backend Endpoint:**
```
GET /contacts/{id}/pdf  # Download PDF business card
```

**PDF Contents:**
- Contact name (bold, large)
- Position and company
- Email, phone, website
- Address
- Embedded photo (150x150, preserves aspect ratio)
- Footer with generation ID

**Technical Details:**
- Uses ReportLab library
- Letter page size (8.5" x 11")
- Professional fonts (Helvetica)
- Auto-filename based on contact name

**Use Cases:**
- Print business cards
- Share contact information
- Archive contact details
- Professional presentations

---

### 6. 📊 Statistics & Analytics

**Comprehensive Insights:**
- ✅ **Total counts**: contacts, tags, groups, users
- ✅ **Contact details**: with email, phone, photo
- ✅ **Top companies** by contact count
- ✅ **Top positions** by contact count
- ✅ **Tag usage statistics**
- ✅ **Group usage statistics**
- ✅ **Recent activity** (last 7 days)

**Backend Endpoint:**
```
GET /statistics/overview  # Get comprehensive statistics
```

**Response Structure:**
```json
{
  "totals": {
    "contacts": 150,
    "tags": 12,
    "groups": 8,
    "users": 5
  },
  "contact_details": {
    "with_email": 120,
    "with_phone": 135,
    "with_photo": 80,
    "without_email": 30,
    "without_phone": 15
  },
  "top_companies": [
    {"company": "Acme Corp", "count": 25},
    {"company": "Tech Inc", "count": 18}
  ],
  "top_positions": [
    {"position": "CEO", "count": 15},
    {"position": "Manager", "count": 12}
  ],
  "tags": [
    {"id": 1, "name": "VIP", "color": "#2563eb", "contacts_count": 45}
  ],
  "groups": [
    {"id": 1, "name": "Partners", "color": "#10b981", "contacts_count": 30}
  ],
  "recent_activity": {
    "last_7_days": 87
  }
}
```

**Use Cases:**
- Dashboard visualization
- Business intelligence
- Contact database health
- Usage patterns
- Data quality monitoring

---

## 📊 Technical Details

### New Dependencies
```
reportlab  # PDF generation library
```

### New Database Models

**Tag:**
```python
id: Integer (PK)
name: String (unique, indexed)
color: String (hex, default: #2563eb)
created_at: DateTime
# Relationship: contacts (many-to-many via contact_tags)
```

**Group:**
```python
id: Integer (PK)
name: String (unique, indexed)
description: String (optional)
color: String (hex, default: #10b981)
created_at: DateTime
# Relationship: contacts (many-to-many via contact_groups)
```

**AuditLog:**
```python
id: Integer (PK)
contact_id: Integer (FK, indexed, cascade delete)
user_id: Integer (FK, SET NULL on delete)
username: String (preserved)
action: String (created/updated/deleted/etc)
entity_type: String (contact/tag/group)
changes: String (JSON)
timestamp: DateTime (indexed)
```

**Association Tables:**
- `contact_tags`: (contact_id, tag_id) - both PKs, cascade delete
- `contact_groups`: (contact_id, group_id) - both PKs, cascade delete

### Updated Models

**Contact:**
```python
# Added relationships
tags: relationship('Tag', secondary=contact_tags)
groups: relationship('Group', secondary=contact_groups)
```

### New Pydantic Schemas
- `TagBase`, `TagCreate`, `TagUpdate`, `TagResponse`
- `GroupBase`, `GroupCreate`, `GroupUpdate`, `GroupResponse`
- `AuditLogResponse`
- Updated `ContactResponse` to include `tags` and `groups`

### API Endpoints Summary

**Total New Endpoints: 18**

**Tags (6 endpoints):**
- GET /tags/
- POST /tags/
- PUT /tags/{id}
- DELETE /tags/{id}
- POST /contacts/{id}/tags
- DELETE /contacts/{id}/tags/{tag_id}

**Groups (6 endpoints):**
- GET /groups/
- POST /groups/
- PUT /groups/{id}
- DELETE /groups/{id}
- POST /contacts/{id}/groups
- DELETE /contacts/{id}/groups/{group_id}

**Audit Log (2 endpoints):**
- GET /contacts/{id}/history
- GET /audit/recent

**PDF Export (1 endpoint):**
- GET /contacts/{id}/pdf

**Statistics (1 endpoint):**
- GET /statistics/overview

**Enhanced Endpoints:**
- GET /contacts/ - now supports tags and groups filters

---

## 🎨 Frontend Changes

### ContactList Component
- Removed client-side filtering (now server-side)
- Added Advanced Filters panel
- Company and position filter inputs
- Sorting controls (field + order)
- Clear filters button
- Real-time auto-refresh on filter changes

### State Management
- `search`: Full-text search query
- `companyFilter`: Company filter
- `positionFilter`: Position filter
- `sortBy`: Sort field (id, full_name, company, position)
- `sortOrder`: Sort direction (asc, desc)
- `showFilters`: Toggle for advanced filters panel

### UI Features
- Filter panel with toggle button
- Clear filters button (shows when filters active)
- Professional styling with form groups
- Select dropdowns for sorting
- Responsive grid layout

---

## 🐛 Bug Fixes

- Fixed client-side filtering performance issues on large datasets
- Fixed `toggleAll` checkbox state with filtered lists
- Fixed contact count display after filtering
- Fixed empty result messages for different filter combinations

---

## 🔒 Security

- Admin-only endpoints for tag/group deletion
- Admin-only access to audit logs (recent)
- User attribution for all changes
- Audit logging for sensitive operations
- Protected PDF generation endpoint

---

## 📈 Performance Improvements

- **Server-side filtering**: Moved from client-side to database queries
- **Indexed columns**: contact_id and timestamp in audit_logs
- **Efficient queries**: SQLAlchemy ORM with proper joins
- **Lazy loading**: Relationship data loaded on-demand
- **Pagination ready**: Limit parameters in audit endpoints

---

## 🔄 Migration Guide

### From v2.1 to v2.2

**No breaking changes!** This is a backward-compatible release.

**Database Migration:**
```bash
# Tables will be created automatically on first startup
# SQLAlchemy will create:
# - tags table
# - groups table
# - audit_logs table
# - contact_tags association table
# - contact_groups association table

# Verify migration
docker exec -it bizcard-backend python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('All tables created successfully!')
"
```

**Dependency Installation:**
```bash
# Rebuild backend container to install reportlab
docker compose down
docker compose up -d --build
```

**No Data Loss:**
- Existing contacts remain unchanged
- New relationships are optional
- Audit logging starts from upgrade time
- Tags and groups are empty initially

---

## 📚 Usage Examples

### 1. Advanced Search

**Find all CEOs at tech companies:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/contacts/?position=ceo&company=tech&sort_by=full_name&sort_order=asc"
```

### 2. Tags Management

**Create a VIP tag:**
```bash
curl -X POST http://localhost:8000/tags/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "VIP", "color": "#FFD700"}'
```

**Add tags to contact:**
```bash
curl -X POST http://localhost:8000/contacts/123/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [1, 2, 3]}'
```

**Filter by tags:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/contacts/?tags=vip,client"
```

### 3. Groups Management

**Create a partners group:**
```bash
curl -X POST http://localhost:8000/groups/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Partners", "description": "Business partners", "color": "#10b981"}'
```

### 4. Audit Log

**View contact history:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/contacts/123/history?limit=50"
```

### 5. PDF Export

**Download business card PDF:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/contacts/123/pdf" \
  -o business_card.pdf
```

### 6. Statistics

**Get dashboard data:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/statistics/overview"
```

---

## 🌍 Internationalization

All new features support the existing i18n system (Russian/English). Future frontend updates will include:
- Tag management UI
- Group management UI
- Audit log viewer
- Statistics dashboard
- PDF export button

---

## 🚀 What's Next?

**Planned for v2.3:**
- 🎨 Frontend UI for tags and groups
- 📊 Interactive statistics dashboard
- 📅 Activity timeline view
- 🔔 Notification system
- 📱 Mobile-responsive improvements
- 🌐 Additional language support

---

## 📝 Statistics

```
Version:         2.2.0
Commits:         3 new commits (729b1dc, 65f9575, bc72618)
Files Modified:  5 files
Lines Added:     +765
Lines Removed:   -2
New Endpoints:   +18
New Models:      +3 (Tag, Group, AuditLog)
New Features:    +6 (Search, Tags, Groups, Audit, PDF, Stats)
Dependencies:    +1 (reportlab)
```

---

## 🆘 Support

**Documentation:**
- See `README.md` for general information
- See `README.ru.md` for Russian documentation
- Check `/api/docs` for interactive API documentation

**Issues:** https://github.com/newwdead/CRM/issues  
**GitHub:** https://github.com/newwdead/CRM

---

## 📜 Full Changelog

### [2.2.0] - 2025-10-19

#### Added
- Advanced search with full-text search across all fields
- Filter by company and position
- Sorting by multiple fields (id, name, company, position)
- Sort order control (ascending/descending)
- Tags system with CRUD operations
- Many-to-many relationship between contacts and tags
- Groups system with CRUD operations
- Many-to-many relationship between contacts and groups
- Comprehensive audit log system
- Automatic change tracking for all contact operations
- PDF export for business cards
- Statistics and analytics endpoint
- Tag usage statistics
- Group usage statistics
- Recent activity tracking (last 7 days)
- Top companies and positions analytics
- `reportlab` dependency for PDF generation

#### Changed
- Contacts list endpoint now supports advanced filtering
- Moved from client-side to server-side filtering
- ContactList component refactored for server-side queries
- Contact response now includes tags and groups
- Improved performance for large contact lists

#### Fixed
- Client-side filtering performance issues
- Checkbox state synchronization with filters
- Empty result messages for different filter scenarios

---

**Full Diff:** https://github.com/newwdead/CRM/compare/v2.1...v2.2  
**Release:** https://github.com/newwdead/CRM/releases/tag/v2.2

---

## 🎉 Credits

**Developed by:** BizCard CRM Team  
**Special Thanks:** To all contributors and testers  
**License:** MIT

---

**Enjoy the new features! 🚀**

