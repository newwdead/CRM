# OCREditorWithBlocks.js Refactoring Plan

**Current:** 1151 lines - God Component  
**Target:** 5-6 files (~200 lines each)  
**Status:** 🔄 In Progress

## Current Structure Analysis

### State Management (15 useState)
```javascript
- editedData, setEditedData
- ocrBlocks, setOcrBlocks
- loading, setLoading
- saving, setSaving
- selectedBlocks, setSelectedBlocks
- assigningToField, setAssigningToField
- language, setLanguage
- multiSelectMode, setMultiSelectMode
- editBlockMode, setEditBlockMode
- draggingBlock, setDraggingBlock
- resizingBlock, setResizingBlock
- reprocessing, setReprocessing
- editingBlockText, setEditingBlockText
- isAddingBlock, setIsAddingBlock
- newBlockStart, setNewBlockStart
- imageScale, setImageScale
- imageOffset, setImageOffset
```

### Functions (~20)
```javascript
- loadOCRBlocks() - API call
- calculateImageScale() - image utility
- handleBlockClick() - block selection
- handleAssignBlock() - field assignment  
- handleFieldChange() - form input
- handleReprocessOCR() - API call
- handleBlockDragStart/Drag/DragEnd() - drag & drop
- handleDeleteBlock() - block manipulation
- handleAddBlock() - block manipulation
- handleImageMouseDown/Up() - adding new blocks
- handleEditBlockText() - block text editing
- handleSaveBlockText() - save edited text
- handleSplitBlock() - split block
- handleSave() - save all changes
```

### Render Components
```javascript
- Loading overlay
- Image container with blocks overlay
- Block elements (visual + interactive)
- Fields sidebar
- Toolbar (edit mode, reprocess, multi-select)
- Assignment panel
- Text editing modal
```

## Proposed Structure

### Directory Layout
```
frontend/src/modules/ocr/
├── components/
│   ├── OCREditorContainer.js (main, ~150 lines)
│   ├── ImageCanvas.js (image + blocks overlay, ~200 lines)
│   ├── BlockOverlay.js (individual block rendering, ~150 lines)
│   ├── FieldsSidebar.js (fields panel, ~200 lines)
│   ├── OCRToolbar.js (toolbar controls, ~150 lines)
│   ├── BlockTextEditor.js (text editing modal, ~100 lines)
│   └── AssignmentPanel.js (block assignment UI, ~100 lines)
├── hooks/
│   ├── useOCRBlocks.js (OCR state & API, ~150 lines)
│   ├── useBlockSelection.js (selection logic, ~100 lines)
│   ├── useBlockManipulation.js (drag/resize/delete, ~150 lines)
│   ├── useImageControls.js (zoom/pan, ~80 lines)
│   └── useFieldAssignment.js (field assignment logic, ~80 lines)
├── utils/
│   ├── blockUtils.js (block calculations, ~100 lines)
│   ├── imageUtils.js (image scaling, ~50 lines)
│   └── ocrApi.js (API calls, ~100 lines)
└── constants/
    ├── translations.js (i18n, ~150 lines)
    └── fieldConfig.js (field colors, names, ~50 lines)
```

## Step-by-Step Refactoring

### Phase 1: Extract Hooks (Non-breaking)
Create custom hooks without changing main component

1. **useOCRBlocks.js** - OCR data management
   ```javascript
   export const useOCRBlocks = (contactId) => {
     const [ocrBlocks, setOcrBlocks] = useState(null);
     const [loading, setLoading] = useState(true);
     const [reprocessing, setReprocessing] = useState(false);
     
     const loadBlocks = async () => { ... };
     const reprocess = async () => { ... };
     
     return { ocrBlocks, setOcrBlocks, loading, reprocessing, loadBlocks, reprocess };
   };
   ```

2. **useBlockSelection.js** - Selection state & logic
   ```javascript
   export const useBlockSelection = () => {
     const [selectedBlocks, setSelectedBlocks] = useState([]);
     const [multiSelectMode, setMultiSelectMode] = useState(false);
     
     const selectBlock = (block, ctrlKey) => { ... };
     const clearSelection = () => { ... };
     
     return { selectedBlocks, multiSelectMode, selectBlock, clearSelection };
   };
   ```

3. **useBlockManipulation.js** - Drag, resize, delete
   ```javascript
   export const useBlockManipulation = (ocrBlocks, setOcrBlocks) => {
     const [draggingBlock, setDraggingBlock] = useState(null);
     const [resizingBlock, setResizingBlock] = useState(null);
     
     const startDrag = (block, event) => { ... };
     const drag = (event) => { ... };
     const endDrag = () => { ... };
     const deleteBlock = (block) => { ... };
     
     return { draggingBlock, resizingBlock, startDrag, drag, endDrag, deleteBlock };
   };
   ```

4. **useImageControls.js** - Zoom & pan
   ```javascript
   export const useImageControls = () => {
     const [imageScale, setImageScale] = useState(1);
     const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });
     const imageRef = useRef(null);
     
     const calculateScale = (imgWidth, imgHeight) => { ... };
     
     return { imageScale, imageOffset, imageRef, calculateScale };
   };
   ```

5. **useFieldAssignment.js** - Field assignment logic
   ```javascript
   export const useFieldAssignment = (selectedBlocks, clearSelection) => {
     const [assigningToField, setAssigningToField] = useState(null);
     
     const startAssignment = () => { ... };
     const assignToField = async (fieldName) => { ... };
     const cancelAssignment = () => { ... };
     
     return { assigningToField, startAssignment, assignToField, cancelAssignment };
   };
   ```

### Phase 2: Extract Utilities (Non-breaking)
Pure functions with no dependencies

1. **blockUtils.js**
   ```javascript
   export const calculateBlockPosition = (block, imageScale, imageOffset) => { ... };
   export const isBlockIntersecting = (block1, block2) => { ... };
   export const mergeBlocks = (blocks) => { ... };
   export const splitBlock = (block, splitY) => { ... };
   ```

2. **imageUtils.js**
   ```javascript
   export const calculateImageScale = (imgWidth, imgHeight, containerWidth, containerHeight) => { ... };
   export const getMousePosition = (event, imageRef) => { ... };
   ```

3. **ocrApi.js**
   ```javascript
   export const loadOCRBlocks = async (contactId) => { ... };
   export const reprocessOCR = async (contactId) => { ... };
   export const updateContact = async (contactId, data) => { ... };
   ```

### Phase 3: Extract Constants (Non-breaking)
Static data

1. **translations.js** (already large, move to separate file)
2. **fieldConfig.js**
   ```javascript
   export const editableFields = [...];
   export const fieldColors = {...};
   export const fieldNames = {...};
   ```

### Phase 4: Extract Components (Breaking changes)
Split rendering logic into smaller components

1. **OCRToolbar.js**
   ```javascript
   export const OCRToolbar = ({ 
     editBlockMode, setEditBlockMode,
     multiSelectMode, setMultiSelectMode,
     onReprocess, reprocessing,
     language
   }) => { ... };
   ```

2. **FieldsSidebar.js**
   ```javascript
   export const FieldsSidebar = ({
     editedData,
     editableFields,
     fieldColors,
     onFieldChange,
     language
   }) => { ... };
   ```

3. **ImageCanvas.js**
   ```javascript
   export const ImageCanvas = ({
     imageUrl,
     imageRef,
     imageScale,
     imageOffset,
     ocrBlocks,
     selectedBlocks,
     onBlockClick,
     onImageMouseDown,
     onImageMouseUp,
     editBlockMode,
     isAddingBlock
   }) => { ... };
   ```

4. **BlockOverlay.js**
   ```javascript
   export const BlockOverlay = ({
     block,
     isSelected,
     fieldColor,
     editMode,
     onDragStart,
     onDelete,
     onEditText,
     imageScale,
     imageOffset
   }) => { ... };
   ```

5. **AssignmentPanel.js**
   ```javascript
   export const AssignmentPanel = ({
     selectedBlocks,
     assigningToField,
     editableFields,
     onAssign,
     onCancel,
     onClearSelection,
     language
   }) => { ... };
   ```

6. **BlockTextEditor.js**
   ```javascript
   export const BlockTextEditor = ({
     block,
     onSave,
     onCancel,
     language
   }) => { ... };
   ```

### Phase 5: Refactor Main Component
Use all extracted pieces

```javascript
// OCREditorContainer.js (~150 lines)
import { useOCRBlocks } from '../hooks/useOCRBlocks';
import { useBlockSelection } from '../hooks/useBlockSelection';
import { useBlockManipulation } from '../hooks/useBlockManipulation';
import { useImageControls } from '../hooks/useImageControls';
import { useFieldAssignment } from '../hooks/useFieldAssignment';

import { OCRToolbar } from './OCRToolbar';
import { FieldsSidebar } from './FieldsSidebar';
import { ImageCanvas } from './ImageCanvas';
import { AssignmentPanel } from './AssignmentPanel';
import { BlockTextEditor } from './BlockTextEditor';

export const OCREditorContainer = ({ contact, onSave, onClose }) => {
  // Use custom hooks
  const { ocrBlocks, setOcrBlocks, loading, reprocessing, loadBlocks, reprocess } = useOCRBlocks(contact.id);
  const { selectedBlocks, multiSelectMode, selectBlock, clearSelection } = useBlockSelection();
  const { draggingBlock, startDrag, drag, endDrag, deleteBlock } = useBlockManipulation(ocrBlocks, setOcrBlocks);
  const { imageScale, imageOffset, imageRef, calculateScale } = useImageControls();
  const { assigningToField, startAssignment, assignToField, cancelAssignment } = useFieldAssignment(selectedBlocks, clearSelection);
  
  // Minimal local state
  const [editedData, setEditedData] = useState({});
  const [editBlockMode, setEditBlockMode] = useState(false);
  
  // Render sub-components
  return (
    <div className="ocr-editor">
      <OCRToolbar ... />
      <div className="ocr-content">
        <ImageCanvas ... />
        <FieldsSidebar ... />
      </div>
      {assigningToField && <AssignmentPanel ... />}
      {editingBlock && <BlockTextEditor ... />}
    </div>
  );
};
```

## Benefits

### Before
- ❌ 1151 lines - hard to understand
- ❌ 15 useState - state management hell
- ❌ 20+ functions - hard to find anything
- ❌ Mixed concerns - API, UI, state, utils
- ❌ Hard to test
- ❌ Hard to reuse logic

### After
- ✅ 6 components (~150 lines each) - easy to understand
- ✅ 5 custom hooks - reusable logic
- ✅ 3 utility files - pure functions, easy to test
- ✅ Separated concerns - clear responsibility
- ✅ Easy to test each piece
- ✅ Reusable hooks for other OCR features

## Testing Strategy

After refactoring:

```javascript
// hooks/useOCRBlocks.test.js
test('loads OCR blocks successfully', async () => { ... });
test('handles reprocess OCR', async () => { ... });

// hooks/useBlockSelection.test.js
test('selects single block', () => { ... });
test('multi-select with Ctrl key', () => { ... });

// utils/blockUtils.test.js
test('calculates block position correctly', () => { ... });
test('splits block at Y position', () => { ... });

// components/BlockOverlay.test.js
test('renders block with correct position', () => { ... });
test('handles drag start', () => { ... });
```

## Migration Plan

1. ✅ Create new directory structure
2. ✅ Extract hooks (one by one, test each)
3. ✅ Extract utilities (test each)
4. ✅ Extract constants
5. ✅ Extract components (one by one)
6. ✅ Refactor main component to use new pieces
7. ✅ Test entire flow
8. ✅ Update imports in parent components
9. ✅ Delete old file
10. ✅ Commit & deploy

## Timeline

- **Phase 1 (Hooks):** 2-3 hours
- **Phase 2 (Utils):** 1 hour
- **Phase 3 (Constants):** 30 minutes
- **Phase 4 (Components):** 3-4 hours
- **Phase 5 (Main):** 1 hour
- **Testing:** 1-2 hours
- **Total:** 8-12 hours work time

## Risk Mitigation

- Keep old file until fully tested
- Create feature branch for refactoring
- Test each extracted piece individually
- Manual testing of full OCR flow
- Rollback plan if issues found

---

**Status:** 📝 Plan Ready  
**Next Step:** Start Phase 1 - Extract first hook (useOCRBlocks)

