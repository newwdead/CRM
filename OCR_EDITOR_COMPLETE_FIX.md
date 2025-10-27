# ✅ OCR Editor Complete Fix - Scaling & Drag-and-Drop

**Date:** 2025-10-27  
**Issue:** Blocks misaligned + drag-and-drop not working  
**Status:** ✅ **FIXED** (Backend + Frontend)

---

## 🔴 Problems Reported

User reported two issues with Contact 123 OCR editor:

1. **❌ Block Positioning:** Blocks displayed in wrong positions (scale issue)
2. **❌ Drag-and-Drop:** Unable to move blocks when editing

---

## 🔍 Root Cause Analysis

### Problem 1: Image Scaling Mismatch

**Backend Issue:**
- PaddleOCR auto-resizes images by default (`det_limit_side_len=960`)
- Contact 123: 4744x2672 → resized to 2000x1126 for OCR processing
- Block coordinates stored based on resized dimensions
- Database stored wrong dimensions: `image_width: 2000, image_height: 1126`

**Frontend Issue:**
- OCREditorWithBlocks.js used DB dimensions for display:
  ```javascript
  width: `${ocrBlocks.image_width * imageScale}px`  // 2000px from DB
  ```
- But browser loaded original image: 4744x2672
- Scale mismatch: 2.372x difference!

**Result:**
- Image displayed at wrong size
- Blocks positioned based on wrong scale
- Visual misalignment between blocks and text

### Problem 2: Drag-and-Drop Broken

**Cause:**
- Drag-and-drop code assumed correct scaling
- With wrong imageScale, mouse calculations were incorrect
- Blocks "jumped" or didn't move properly

---

## ✅ Solutions Applied

### Solution 1: Backend - Prevent PaddleOCR Auto-Resize

**File:** `backend/app/integrations/ocr/providers_v2/paddle_provider.py`

**Change:**
```python
self.ocr = PaddleOCR(
    # ... existing parameters ...
    
    # Image size limits - prevent auto-resize for high-res business cards
    det_limit_side_len=6000,  # Increased from default 960
    det_limit_type='max',     # Limit type
)
```

**Impact:**
- **New uploads:** Images up to 6000px won't be resized
- **New uploads:** Correct dimensions stored in DB
- **Old contacts:** Still have wrong dimensions (need frontend fix)

**Commit:** `6f0a76b` - "fix: prevent PaddleOCR auto-resize causing OCR editor misalignment"

### Solution 2: Frontend - Dynamic Image Scaling

**File:** `frontend/src/components/OCREditorWithBlocks.js`

**Changes:**

#### 1. Added State Variables
```javascript
const [realImageSize, setRealImageSize] = useState(null);
const [blockScaleFactor, setBlockScaleFactor] = useState(1);
```

#### 2. Image Load Handler
```javascript
const handleImageLoad = () => {
  const img = imageRef.current;
  const realWidth = img.naturalWidth;   // 4744
  const realHeight = img.naturalHeight; // 2672
  
  setRealImageSize({ width: realWidth, height: realHeight });
  
  // Calculate scale factor between real and DB dimensions
  const scaleX = realWidth / ocrBlocks.image_width;   // 4744 / 2000 = 2.372
  const scaleY = realHeight / ocrBlocks.image_height; // 2672 / 1126 = 2.373
  const scaleFactor = (scaleX + scaleY) / 2;          // 2.372
  
  setBlockScaleFactor(scaleFactor);
  
  // Recalculate display scale based on real dimensions
  calculateImageScale(realWidth, realHeight);
};
```

#### 3. Image Display
```javascript
<img
  ref={imageRef}
  src={imageUrl}
  onLoad={handleImageLoad}  // ← Added
  style={{
    // Use real dimensions instead of DB dimensions
    width: realImageSize 
      ? `${realImageSize.width * imageScale}px`  // Real: 4744px
      : `${ocrBlocks.image_width * imageScale}px`, // Fallback: 2000px
    height: realImageSize 
      ? `${realImageSize.height * imageScale}px`
      : `${ocrBlocks.image_height * imageScale}px`
  }}
/>
```

#### 4. Block Rendering with Scale Factor
```javascript
{ocrBlocks.lines.map((line, idx) => {
  const box = line.box;
  
  // Apply blockScaleFactor to coordinates
  const scaledX = box.x * blockScaleFactor;       // Original * 2.372
  const scaledY = box.y * blockScaleFactor;
  const scaledWidth = box.width * blockScaleFactor;
  const scaledHeight = box.height * blockScaleFactor;
  
  return (
    <rect
      x={scaledX * imageScale}       // Apply both scales
      y={scaledY * imageScale}
      width={scaledWidth * imageScale}
      height={scaledHeight * imageScale}
      // ...
    />
  );
})}
```

#### 5. Drag-and-Drop Fix
```javascript
// Start drag: Account for blockScaleFactor
const handleBlockDragStart = (block, event) => {
  const mouseX = (event.clientX - rect.left) / imageScale;
  const mouseY = (event.clientY - rect.top) / imageScale;
  
  const scaledBlockX = block.box.x * blockScaleFactor;
  const scaledBlockY = block.box.y * blockScaleFactor;
  
  setDragOffset({
    x: mouseX - scaledBlockX,
    y: mouseY - scaledBlockY
  });
};

// During drag: Convert back to original coordinate space
const handleBlockDrag = (event) => {
  const mouseX = (event.clientX - rect.left) / imageScale;
  const mouseY = (event.clientY - rect.top) / imageScale;
  
  const newScaledX = mouseX - dragOffset.x;
  const newScaledY = mouseY - dragOffset.y;
  
  // Convert back (undo blockScaleFactor)
  const newX = newScaledX / blockScaleFactor;  // Divide by 2.372
  const newY = newScaledY / blockScaleFactor;
  
  // Update block position in original coordinate space
  setOcrBlocks(prev => ({
    ...prev,
    lines: prev.lines.map(line => 
      line === draggingBlock ? { ...line, box: { ...line.box, x: newX, y: newY } } : line
    )
  }));
};
```

**Commit:** `f13ecf0` - "fix: OCR editor image scaling and block positioning"

---

## 📊 How It Works

### For Old Contacts (like Contact 123)

1. **Image loads:** Browser gets real dimensions (4744x2672)
2. **Compare with DB:** DB has wrong dimensions (2000x1126)
3. **Calculate scale:** `blockScaleFactor = 4744/2000 = 2.372`
4. **Display image:** Use real dimensions (4744x2672)
5. **Render blocks:** Multiply coordinates by 2.372
   - DB block at (137, 128) → Display at (325, 304)
6. **Drag block:** Divide new position by 2.372 before saving
7. **Result:** ✅ Blocks perfectly aligned!

### For New Contacts (after backend fix)

1. **Upload:** PaddleOCR processes without resize (up to 6000px)
2. **DB stores:** Real dimensions (e.g., 4744x2672)
3. **Calculate scale:** `blockScaleFactor = 4744/4744 = 1.0`
4. **Display:** No scaling needed (coordinates already correct)
5. **Result:** ✅ Works perfectly from the start!

---

## 🎯 Technical Details

### Coordinate Systems

**Three coordinate spaces:**
1. **Original Image:** Real file dimensions (e.g., 4744x2672)
2. **OCR Processing:** May be resized (e.g., 2000x1126)
3. **Display:** Scaled to fit container (e.g., 800x450)

**Transformations:**
```
DB coordinates → Real coordinates → Display coordinates
    (x)      →   (x * scaleFactor) →  (x * scaleFactor * imageScale)
```

**Example:**
```
DB block: x=137, y=128
Real:     x=137*2.372=325, y=128*2.372=304
Display:  x=325*0.4=130,   y=304*0.4=122 (if imageScale=0.4)
```

### SVG Overlay

**Old code (broken):**
```javascript
<svg
  width={`${ocrBlocks.image_width * imageScale}px`}  // Wrong: 2000 * 0.4 = 800px
  height={`${ocrBlocks.image_height * imageScale}px`}
>
  <rect
    x={box.x * imageScale}  // Wrong: uses DB coordinates directly
    y={box.y * imageScale}
  />
</svg>
```

**New code (fixed):**
```javascript
<svg
  width={`${realImageSize.width * imageScale}px`}  // Correct: 4744 * 0.4 = 1898px
  height={`${realImageSize.height * imageScale}px`}
>
  <rect
    x={box.x * blockScaleFactor * imageScale}  // Correct: apply both scales
    y={box.y * blockScaleFactor * imageScale}
  />
</svg>
```

---

## ✅ Testing Results

### Contact 123 (Old, Wrong DB Dimensions)

**Before Fix:**
- ❌ Blocks scattered across image
- ❌ Can't drag blocks
- ❌ Scale mismatch visible

**After Fix:**
- ✅ Blocks perfectly aligned with text
- ✅ Drag-and-drop works smoothly
- ✅ Console shows: `scaleFactor: 2.372`

### New Uploads (After Backend Fix)

**Expected:**
- ✅ DB dimensions match real dimensions
- ✅ `scaleFactor: 1.000`
- ✅ No scaling issues from the start

---

## 🚀 Deployment

### Backend
1. ✅ Modified `paddle_provider.py`
2. ✅ Restarted `bizcard-backend` container
3. ✅ Committed: `6f0a76b`

### Frontend
1. ✅ Modified `OCREditorWithBlocks.js`
2. ✅ Rebuilt Docker image: `docker compose build frontend`
3. ✅ Restarted container: `docker compose up -d frontend`
4. ✅ Committed: `f13ecf0`

### Documentation
1. ✅ Created `OCR_EDITOR_FIX_ALIGNMENT.md`
2. ✅ Created `OCR_EDITOR_COMPLETE_FIX.md`
3. ✅ Committed: `a1cff54`

---

## 📝 User Instructions

### For Existing Contacts (like 123)

1. Open editor: `https://ibbase.ru/contacts/123/ocr-editor`
2. **Check console:** Should see log with `scaleFactor: 2.372`
3. **Verify blocks:** Should align perfectly with text
4. **Test drag:** Click "Edit Blocks", drag should work smoothly

### For New Uploads

1. Upload new card: `https://ibbase.ru/upload`
2. Select "PaddleOCR (AI + Cyrillic)" or "Auto"
3. Open editor: Blocks should be perfect from the start
4. **Check console:** Should see `scaleFactor: 1.000` (no resize)

### Troubleshooting

**If blocks still misaligned:**
1. Clear browser cache (Ctrl+Shift+R)
2. Check console for scale factor
3. Verify image dimensions in console log

**If drag-and-drop doesn't work:**
1. Click "Edit Blocks" button first
2. Check browser console for errors
3. Verify mouse events are firing

---

## 🎉 Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Backend Resize** | Auto 960px | Up to 6000px ✅ |
| **DB Dimensions** | Wrong (resized) | Correct (original) ✅ |
| **Frontend Display** | Used DB size ❌ | Uses real size ✅ |
| **Block Coordinates** | Wrong scale ❌ | Scaled correctly ✅ |
| **Drag-and-Drop** | Broken ❌ | Working ✅ |
| **Old Contacts** | Broken ❌ | Fixed with scaling ✅ |
| **New Contacts** | Would be broken | Perfect from start ✅ |

---

## 💡 Key Innovations

1. **Dynamic Scaling:** Frontend adapts to any size mismatch
2. **Backward Compatible:** Fixes old contacts without reprocessing
3. **Future Proof:** Works with new high-res uploads
4. **Transparent:** Console logs show what's happening
5. **Robust:** Handles edge cases gracefully

---

## 🔗 Related Issues

- Contact 123 OCR editor alignment
- PaddleOCR auto-resize behavior
- OCR v2.0 integration

---

## 📚 Commits

1. `6f0a76b` - Backend: Prevent PaddleOCR auto-resize
2. `a1cff54` - Docs: OCR editor alignment diagnosis
3. `f13ecf0` - Frontend: Dynamic image scaling fix

---

**Status:** ✅ **COMPLETE AND DEPLOYED**

**Version:** v6.1.6

**Verified:** Contact 123 editor now works correctly!

