import React from 'react';

/**
 * OCR Editor Toolbar Component
 * 
 * Provides controls for OCR editing:
 * - Edit mode toggle
 * - Reprocess OCR
 * - Add block
 * - Edit block text
 * - Split block
 * - Delete block
 * 
 * @param {object} props - Component props
 * @param {boolean} props.editBlockMode - Whether edit mode is enabled
 * @param {function} props.onToggleEditMode - Toggle edit mode handler
 * @param {boolean} props.reprocessing - Whether OCR is reprocessing
 * @param {function} props.onReprocess - Reprocess OCR handler
 * @param {boolean} props.isAddingBlock - Whether user is adding a block
 * @param {function} props.onAddBlock - Add block handler
 * @param {array} props.selectedBlocks - Currently selected blocks
 * @param {function} props.onEditBlockText - Edit block text handler
 * @param {function} props.onSplitBlock - Split block handler
 * @param {function} props.onDeleteBlock - Delete block handler
 * @param {object} props.translations - Translation object
 */
const OCRToolbar = ({
  editBlockMode,
  onToggleEditMode,
  reprocessing,
  onReprocess,
  isAddingBlock,
  onAddBlock,
  selectedBlocks = [],
  onEditBlockText,
  onSplitBlock,
  onDeleteBlock,
  translations
}) => {
  const t = translations || {};

  // Button base style
  const buttonStyle = {
    padding: '8px 12px',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '600',
    transition: 'all 0.2s',
    cursor: 'pointer'
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '8px',
      marginBottom: '15px'
    }}>
      {/* Edit Mode Toggle */}
      <button
        onClick={onToggleEditMode}
        style={{
          ...buttonStyle,
          backgroundColor: editBlockMode ? '#10b981' : '#3b82f6'
        }}
        title={editBlockMode ? 'Exit edit mode' : 'Enter edit mode'}
      >
        {editBlockMode ? '✅ ' : '✏️ '}{t.editBlocks || 'Edit Blocks'}
      </button>

      {/* Reprocess OCR */}
      <button
        onClick={onReprocess}
        disabled={reprocessing}
        style={{
          ...buttonStyle,
          backgroundColor: reprocessing ? '#9ca3af' : '#f59e0b',
          cursor: reprocessing ? 'not-allowed' : 'pointer',
          opacity: reprocessing ? 0.6 : 1
        }}
        title="Re-run OCR processing"
      >
        {reprocessing 
          ? '⏳ ' + (t.reprocessing || 'Processing...') 
          : '🔄 ' + (t.reprocessOCR || 'Re-run OCR')}
      </button>

      {/* Add Block */}
      <button
        onClick={onAddBlock}
        disabled={!editBlockMode}
        style={{
          ...buttonStyle,
          backgroundColor: isAddingBlock ? '#10b981' : '#8b5cf6',
          cursor: !editBlockMode ? 'not-allowed' : 'pointer',
          opacity: !editBlockMode ? 0.5 : 1
        }}
        title={editBlockMode ? 'Add new text block' : 'Enable edit mode first'}
      >
        {isAddingBlock ? '✏️ ' : '➕ '}{t.addBlock || 'Add Block'}
      </button>

      {/* Edit Block Text (only when 1 block selected in edit mode) */}
      {selectedBlocks.length === 1 && editBlockMode && (
        <>
          <button
            onClick={() => onEditBlockText && onEditBlockText(selectedBlocks[0])}
            style={{
              ...buttonStyle,
              backgroundColor: '#06b6d4'
            }}
            title="Edit block text"
          >
            📝 {t.editText || 'Edit Text'}
          </button>

          <button
            onClick={() => onSplitBlock && onSplitBlock(selectedBlocks[0])}
            style={{
              ...buttonStyle,
              backgroundColor: '#14b8a6'
            }}
            title="Split block into two"
          >
            ✂️ {t.splitBlock || 'Split Block'}
          </button>

          <button
            onClick={() => onDeleteBlock && onDeleteBlock(selectedBlocks[0])}
            style={{
              ...buttonStyle,
              backgroundColor: '#ef4444'
            }}
            title="Delete block"
          >
            🗑️ {t.deleteBlock || 'Delete Block'}
          </button>
        </>
      )}

      {/* Multi-block actions */}
      {selectedBlocks.length > 1 && editBlockMode && (
        <button
          onClick={() => {
            if (onDeleteBlock && window.confirm(
              translations?.deleteConfirm || 'Delete all selected blocks?'
            )) {
              selectedBlocks.forEach(block => onDeleteBlock(block));
            }
          }}
          style={{
            ...buttonStyle,
            backgroundColor: '#ef4444',
            gridColumn: 'span 2'
          }}
          title="Delete all selected blocks"
        >
          🗑️ {t.deleteBlock || 'Delete'} ({selectedBlocks.length})
        </button>
      )}

      {/* Edit Mode Hint */}
      {editBlockMode && (
        <div style={{
          gridColumn: 'span 2',
          padding: '8px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #3b82f6',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#1e40af',
          textAlign: 'center'
        }}>
          💡 {t.editModeHint || 'Drag blocks to move, drag corners to resize'}
        </div>
      )}
    </div>
  );
};

export default OCRToolbar;

