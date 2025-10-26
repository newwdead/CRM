# ContactList Refactoring Plan

**Started:** October 26, 2025  
**Target File:** `frontend/src/components/ContactList.js` (1076 lines)  
**Goal:** Break down God Component into modular architecture

## 📊 Current Analysis

### File Statistics
- **Total Lines:** 1076
- **Functions/Constants:** 41+
- **State Variables:** 20+
- **Main Concerns:**
  - Data fetching & management
  - Pagination
  - Search & filtering
  - Sorting
  - Table settings & columns
  - Bulk operations (edit, delete)
  - Export (CSV, XLSX)
  - Duplicate detection
  - Image viewing
  - OCR editing
  - Contact card modal
  - Table zoom

### Key Features
1. **Data Management**
   - Load contacts with pagination
   - Search contacts
   - Filter by company, position
   - Sort by any field
   - Refresh data

2. **Table Display**
   - Customizable columns
   - Column visibility toggle
   - Column width adjustment
   - Table zoom (0.5x - 2.0x)
   - Responsive layout

3. **Bulk Operations**
   - Select all/deselect all
   - Bulk edit (tags, groups, fields)
   - Bulk delete
   - Export selected (CSV, XLSX)

4. **Individual Actions**
   - View contact card
   - Edit contact
   - Delete contact
   - Copy UID
   - View photo
   - OCR edit
   - Duplicate detection

5. **Statistics**
   - Total contacts
   - With email count
   - With phone count

## 🎯 Refactoring Strategy

Similar to OCREditor refactoring, break into:

### Phase 1: Custom Hooks (~500 lines)
Extract stateful logic:

1. **useContactsData.js** (~150 lines)
   - Load contacts with pagination
   - Search, filter, sort
   - Refresh logic
   - Stats calculation
   - API calls

2. **useContactSelection.js** (~80 lines)
   - Multi-select state
   - Select all/deselect all
   - Selected IDs management

3. **useTableSettings.js** (~120 lines)
   - Column configuration (visibility, order, width)
   - Table zoom (in/out/reset)
   - Save/load from localStorage
   - Column drag & drop order

4. **useBulkOperations.js** (~100 lines)
   - Bulk edit state & logic
   - Bulk delete with confirmation
   - Apply bulk changes
   - Validation

5. **useContactModals.js** (~50 lines)
   - Image viewer modal
   - Contact card modal
   - OCR editor modal
   - New contact modal

### Phase 2: Utils & Constants (~300 lines)

1. **translations.js** (~150 lines)
   - EN/RU translations
   - Field names
   - Button labels
   - Messages

2. **tableConfig.js** (~80 lines)
   - Default columns configuration
   - Column definitions
   - Sort options
   - Filter options

3. **exportUtils.js** (~70 lines)
   - Export to CSV logic
   - Export to XLSX logic
   - Data formatting

### Phase 3: UI Components (~600 lines)

1. **ContactsToolbar.js** (~150 lines)
   - Search bar
   - Add contact button
   - Bulk action buttons
   - Export buttons
   - Filter toggle
   - Stats display

2. **ContactsFilters.js** (~120 lines)
   - Advanced filters panel
   - Company filter
   - Position filter
   - Sort dropdown
   - Clear filters button

3. **ContactsTable.js** (~200 lines)
   - Table header with sortable columns
   - Table rows with contact data
   - Selection checkboxes
   - Action buttons per row
   - Empty state
   - Loading skeleton

4. **ContactsPagination.js** (~80 lines)
   - Page navigation
   - Page size selector
   - Total count display
   - Jump to page

5. **BulkEditPanel.js** (~150 lines)
   - Bulk edit form
   - Field inputs
   - Apply/Cancel buttons
   - Selected count

6. **TableSettingsModal.js** (~100 lines)
   - Column visibility checkboxes
   - Column order drag & drop
   - Column width inputs
   - Zoom controls
   - Save/Reset buttons

### Phase 4: Main Container (~150 lines)

**ContactListContainer.js**:
- Import all hooks
- Compose all components
- Handle modals
- Minimal local state

### Phase 5: Integration & Testing

- Replace old ContactList.js
- Test all features
- Deploy

## 📁 Proposed File Structure

```
frontend/src/modules/contacts/
├── hooks/
│   ├── useContactsData.js
│   ├── useContactSelection.js
│   ├── useTableSettings.js
│   ├── useBulkOperations.js
│   └── useContactModals.js
├── utils/
│   ├── exportUtils.js
│   └── apiUtils.js
├── constants/
│   ├── translations.js
│   └── tableConfig.js
└── components/
    ├── ContactListContainer.js (main)
    ├── ContactsToolbar.js
    ├── ContactsFilters.js
    ├── ContactsTable.js
    ├── ContactsPagination.js
    ├── BulkEditPanel.js
    └── TableSettingsModal.js
```

## 📈 Expected Outcome

**Before:**
- 1 file: 1076 lines
- Mixed concerns
- Hard to test
- Difficult to maintain

**After:**
- ~15 files: ~1550 lines total
- Clear separation of concerns
- Reusable hooks
- Testable components
- Easy to maintain

## 🚀 Execution Plan

1. ✅ Analyze current structure
2. ⏳ Create hooks (Phase 1)
3. ⏳ Create utils/constants (Phase 2)
4. ⏳ Create UI components (Phase 3)
5. ⏳ Create main container (Phase 4)
6. ⏳ Integration & testing (Phase 5)

---

**Status:** Planning Complete - Ready to Execute  
**Next:** Phase 1 - Extract Custom Hooks

