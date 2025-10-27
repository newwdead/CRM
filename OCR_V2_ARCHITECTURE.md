# 🚀 OCR v2.0 Architecture & Current Implementation

## 📋 Current System Overview

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    OCR v2.0 Pipeline                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │        1. Image Input (6000px max)        │
    └───────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │   2. PaddleOCR Text Detection + OCR       │
    │      - Cyrillic language support          │
    │      - Bounding boxes for each text block │
    │      - Confidence scores                  │
    └───────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │   3. LayoutLMv3 Classification (AI)       │
    │      - Identifies field types:            │
    │        • name, company, position          │
    │        • email, phone, address            │
    │      - Based on position + context        │
    └───────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │   4. Validator Service (Auto-correct)     │
    │      - Email format validation            │
    │      - Phone number normalization         │
    │      - Name capitalization                │
    └───────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │   5. Storage to Database + MinIO          │
    │      - contacts.ocr_raw (JSON)            │
    │      - MinIO: images + OCR results        │
    └───────────────────────────────────────────┘
```

## 📦 Data Structure

### TextBlock (OCR v2.0)

```python
@dataclass
class TextBlock:
    text: str              # Recognized text
    bbox: BoundingBox      # Position on image
    confidence: float      # 0.0 - 1.0
    block_id: int         # Unique identifier
    field_type: str       # AI classification: "name", "email", etc.
```

### BoundingBox

```python
@dataclass
class BoundingBox:
    x: float              # Top-left X coordinate
    y: float              # Top-left Y coordinate
    width: float          # Block width
    height: float         # Block height
    
    @property
    def x2(self) -> float:
        return self.x + self.width
    
    @property
    def y2(self) -> float:
        return self.y + self.height
```

### Saved in Database (contacts.ocr_raw)

```json
{
  "provider": "PaddleOCR",
  "blocks": [
    {
      "text": "Иван Иванов",
      "box": {
        "x": 120.5,
        "y": 45.2,
        "width": 250.0,
        "height": 30.0,
        "x2": 370.5,
        "y2": 75.2
      },
      "confidence": 0.95,
      "block_id": 0,
      "field_type": "name"
    },
    ...
  ],
  "image_width": 2964,
  "image_height": 2088,
  "layoutlm_used": true,
  "validation_applied": true
}
```

## 🔧 Current Implementation Files

### Backend

```
backend/app/integrations/ocr/
├── providers_v2/
│   ├── base.py              # Base classes: TextBlock, BoundingBox, OCRProviderV2
│   ├── manager.py           # OCRManagerV2: orchestration + LayoutLMv3 integration
│   └── paddle_provider.py   # PaddleOCR implementation
│
├── layoutlm/
│   ├── classifier.py        # LayoutLMv3Classifier for field classification
│   └── config.py            # LayoutLM configuration
│
└── validators/
    └── validator_service.py # Auto-correction (email, phone, etc.)
```

### Frontend (Current Visual Editor - ПРОБЛЕМНЫЙ)

```
frontend/src/modules/ocr/
├── components/
│   ├── OCREditorContainer.js    # Main container (СЛОЖНЫЙ)
│   ├── ImageCanvas.js           # Image + SVG overlay (ПРОБЛЕМЫ С МАСШТАБОМ)
│   ├── BlockOverlay.js          # Individual block rendering (ПРОБЛЕМЫ С КООРДИНАТАМИ)
│   └── ...
│
└── hooks/
    ├── useOCRBlocks.js          # Block data management
    ├── useBlockManipulation.js  # Drag'n'drop + resize (БАГИ С КООРДИНАТАМИ)
    └── useImageControls.js      # Image scaling
```

## ❌ Identified Problems with Visual Editor

### 1. **Coordinate Transformation Issues**
- Frontend image scales dynamically (maxWidth/maxHeight)
- OCR coordinates are in original image space
- `blockScaleFactor` calculation is inconsistent
- Drag'n'drop causes coordinate corruption

### 2. **Deep Copy Issues**
- `box.copy()` doesn't create deep copies
- `x2`, `y2` not recalculated after move
- Blocks "fly away" or disappear after save

### 3. **Complexity**
- 8 resize handles per block
- Complex state management (drag, resize, select, edit)
- Hard to debug coordinate transformations
- Performance issues with many blocks (24+)

### 4. **UX Issues**
- Slow drag'n'drop
- Blocks hard to click on small screens
- No visual feedback for coordinate errors
- "Repeat OCR" overwrites manual edits

## 💡 RECOMMENDED ALTERNATIVE APPROACH

### Option 1: **Table-Based Editor** (SIMPLE & RELIABLE)

Instead of visual drag'n'drop, show blocks as a table:

```
┌─────────────────────────────────────────────────────────────┐
│  📋 OCR Blocks Editor                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Image Preview]                                            │
│   - Show image with block overlays (READ-ONLY)             │
│   - Highlight block on hover                                │
│                                                             │
│  📊 Blocks Table:                                           │
│  ┌──────┬────────────────┬───────────┬──────────────┐      │
│  │ ID   │ Text           │ Field     │ Confidence   │      │
│  ├──────┼────────────────┼───────────┼──────────────┤      │
│  │ 0    │ Иван Иванов    │ name ▼    │ 95%          │ ✏️ 🗑️│
│  │ 1    │ ivan@mail.ru   │ email ▼   │ 98%          │ ✏️ 🗑️│
│  │ 2    │ +79001234567   │ phone ▼   │ 92%          │ ✏️ 🗑️│
│  └──────┴────────────────┴───────────┴──────────────┘      │
│                                                             │
│  Actions:                                                   │
│  [🔄 Reprocess OCR] [💾 Save Changes] [❌ Cancel]          │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Simple, no coordinate transformations
- ✅ Edit text directly in input fields
- ✅ Assign blocks to fields via dropdown
- ✅ Delete unwanted blocks
- ✅ No visual bugs
- ✅ Works on all screen sizes

### Option 2: **Hybrid Approach** (BETTER)

```
┌─────────────────────────────────────────────────────────────┐
│  Left Panel: Image (READ-ONLY)       Right Panel: Editor   │
├───────────────────────────┬─────────────────────────────────┤
│                           │                                 │
│  [Business Card Image]    │  Block #3 (Selected)            │
│   - Show all blocks       │  ┌─────────────────────────┐    │
│   - Highlight on hover    │  │ Text:                   │    │
│   - Click to select       │  │ [Иван Иванов        ]   │    │
│   - NO drag'n'drop        │  │                         │    │
│                           │  │ Assign to:              │    │
│                           │  │ [name           ▼]      │    │
│                           │  │                         │    │
│                           │  │ Confidence: 95%         │    │
│                           │  └─────────────────────────┘    │
│                           │                                 │
│                           │  [💾 Save] [🗑️ Delete Block]    │
│                           │                                 │
│                           │  All Blocks:                    │
│                           │  • Block 0: HACK                │
│                           │  • Block 1: Терентьева          │
│                           │  • Block 2: ivan@mail.ru        │
│                           │  ...                            │
└───────────────────────────┴─────────────────────────────────┘
```

**Benefits:**
- ✅ Visual context (see image)
- ✅ No coordinate editing
- ✅ Click to select block
- ✅ Edit in right panel
- ✅ Simple & reliable

## 🎯 PROPOSED: Simple Table Editor

Create NEW component: `OCRBlocksTableEditor.js`

### Features:
1. **Read-only image preview** with block overlays
2. **Editable table** with columns:
   - Text (editable input)
   - Field assignment (dropdown)
   - Confidence (read-only)
   - Actions (edit, delete)
3. **No coordinate editing** - coordinates are READ-ONLY from OCR
4. **Reprocess OCR button** - runs PaddleOCR again if needed
5. **Save button** - saves only text + field assignments

### Implementation:
- 1 component (~200 lines)
- No coordinate transformations
- No drag'n'drop bugs
- Works reliably

## 📌 Next Steps

1. **Keep current visual editor** for reference
2. **Create new table-based editor**
3. **Add toggle** in admin settings: "Use table editor"
4. **Test both approaches**
5. **Deprecate problematic visual editor**

