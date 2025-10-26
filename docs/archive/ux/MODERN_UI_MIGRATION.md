# Modern UI Migration Guide - v4.5.0

## Quick Start

All pages should now use the **Modern UI System** classes from `frontend/src/styles/modern-ui.css`.

## Before & After Examples

### Page Structure

**Before:**
```jsx
<div>
  <div className="card">
    <h2>Title</h2>
    <p>Description</p>
  </div>
</div>
```

**After:**
```jsx
<div className="modern-page">
  <div className="modern-page-header">
    <h1 className="modern-page-title">
      🎯 Title
    </h1>
    <p className="modern-page-subtitle">Description</p>
  </div>
  
  <div className="modern-card">
    <h3 className="modern-card-title">Card Title</h3>
    {/* Content */}
  </div>
</div>
```

### Buttons

Replace all buttons with `.modern-btn` variants:

```jsx
<button className="modern-btn">Primary Action</button>
<button className="modern-btn modern-btn-secondary">Secondary</button>
<button className="modern-btn modern-btn-success">Success</button>
<button className="modern-btn modern-btn-danger">Danger</button>
```

### Inputs

```jsx
<label className="modern-label">Field Name</label>
<input className="modern-input" type="text" />

<select className="modern-select">
  <option>Option 1</option>
</select>

<textarea className="modern-textarea"></textarea>
```

### Alerts

```jsx
<div className="modern-alert modern-alert-info">
  ℹ️ Information message
</div>
<div className="modern-alert modern-alert-success">
  ✅ Success message
</div>
<div className="modern-alert modern-alert-warning">
  ⚠️ Warning message
</div>
<div className="modern-alert modern-alert-danger">
  ❌ Error message
</div>
```

### Grids

```jsx
<div className="modern-grid">
  <div className="modern-card">Card 1</div>
  <div className="modern-card">Card 2</div>
  <div className="modern-card">Card 3</div>
</div>
```

## Migration Checklist

- [ ] Replace page `<div>` with `.modern-page`
- [ ] Add `.modern-page-header` with `.modern-page-title` and `.modern-page-subtitle`
- [ ] Replace all `.card` with `.modern-card`
- [ ] Update all buttons to `.modern-btn` variants
- [ ] Update all inputs to `.modern-input`, `.modern-select`, `.modern-textarea`
- [ ] Replace alerts/notifications with `.modern-alert-*`
- [ ] Use `.modern-grid` for responsive layouts
- [ ] Add loading states with `.modern-spinner`
- [ ] Use `.modern-badge-*` for status badges

## Components to Update

1. ✅ Settings.js - Already modernized
2. ✅ MainLayout.js - Already has dropdowns
3. ⏳ HomePage.js - In progress
4. ⏳ UploadCard.js - Needs update
5. ⏳ BatchUpload.js - Needs update
6. ⏳ ImportExport.js - Needs update
7. ⏳ DuplicateFinder.js - Needs update
8. ⏳ Companies.js - Needs update
9. ⏳ AdminPanel.js - Needs update

## Design Tokens

- **Primary Color:** #2563eb
- **Page Background:** #f5f7fa
- **Card Background:** #fff
- **Border Color:** #e1e4e8
- **Text Primary:** #333
- **Text Secondary:** #666
- **Border Radius:** 6px (small), 12px (cards)
- **Spacing:** 8px/12px/16px/20px/24px
- **Transitions:** 0.2s-0.3s ease

## Next Steps

After all components are migrated:
1. Remove old CSS classes
2. Test responsiveness
3. Verify accessibility
4. Deploy v4.5.0
