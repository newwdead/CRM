import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

// Hooks
import { useOCRBlocks } from '../hooks/useOCRBlocks';
import { useBlockSelection } from '../hooks/useBlockSelection';
import { useImageControls } from '../hooks/useImageControls';
import { useFieldAssignment } from '../hooks/useFieldAssignment';
import { useBlockManipulation } from '../hooks/useBlockManipulation';

// Components
import OCRToolbar from './OCRToolbar';
import ImageCanvas from './ImageCanvas';
import FieldsSidebar from './FieldsSidebar';
import BlockTextEditor from './BlockTextEditor';
import AssignmentPanel from './AssignmentPanel';

// Constants & Utils
import { getOCRTranslations } from '../constants/translations';
import { editableFields } from '../constants/fieldConfig';

/**
 * OCR Editor Container (Refactored)
 * 
 * Main container component that composes all OCR editing functionality
 * Replaces the monolithic OCREditorWithBlocks component
 * 
 * @param {object} props - Component props
 * @param {object} props.contact - Contact object with photo_path and fields
 * @param {function} props.onSave - Save handler (editedData) => Promise
 * @param {function} props.onClose - Close handler () => void
 */
const OCREditorContainer = ({ contact, onSave, onClose }) => {
  // Language and translations
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');
  const translations = getOCRTranslations(language);

  // Local state for edited data
  const [editedData, setEditedData] = useState({});
  const [saving, setSaving] = useState(false);

  // Image controls hook
  const { imageRef, imageScale, calculateImageScale } = useImageControls();
  
  // Block scale factor state (for coordinate transformation)
  const [blockScaleFactor, setBlockScaleFactor] = useState(1);

  // OCR blocks hook
  const {
    ocrBlocks,
    setOcrBlocks,
    loading,
    reprocessing,
    reprocessOCR,
    saveOCRBlocks,
    saveOCRCorrections
  } = useOCRBlocks(
    contact.id,
    calculateImageScale,
    editableFields,
    setEditedData,
    translations
  );

  // Block selection hook
  const {
    selectedBlocks,
    handleBlockClick,
    clearSelection
  } = useBlockSelection();

  // Field assignment hook
  const {
    assigningToField,
    setAssigningToField,
    assignToField
  } = useFieldAssignment(
    selectedBlocks,
    clearSelection,
    setEditedData,
    saveOCRCorrections,
    translations
  );

  // Block manipulation hook
  const {
    editBlockMode,
    setEditBlockMode,
    draggingBlock,
    dragPosition,
    resizingBlock,
    resizeBox,
    isAddingBlock,
    editingBlockText,
    startBlockDrag,
    handleBlockDrag,
    endBlockDrag,
    startBlockResize,
    handleBlockResize,
    endBlockResize,
    deleteBlock,
    startAddingBlock,
    handleNewBlockMouseDown,
    handleNewBlockMouseUp,
    startEditBlockText,
    saveBlockText,
    cancelEditBlockText,
    splitBlock
  } = useBlockManipulation(
    ocrBlocks,
    setOcrBlocks,
    imageRef,
    imageScale,
    blockScaleFactor,
    language
  );

  // Initialize edited data from contact
  useEffect(() => {
    console.log('🟢 OCREditorContainer mounted for contact:', contact.id);
    const initial = {};
    editableFields.forEach(field => {
      initial[field] = contact[field] || '';
    });
    setEditedData(initial);
  }, [contact]);

  // Handle dragging and resizing
  useEffect(() => {
    const isDragging = draggingBlock && editBlockMode;
    const isResizing = resizingBlock && editBlockMode;
    
    if (!isDragging && !isResizing) return;

    const handleMouseMove = (e) => {
      if (isDragging) {
        handleBlockDrag(e);
      } else if (isResizing) {
        handleBlockResize(e);
      }
    };
    
    const handleMouseUp = () => {
      if (isDragging) {
        endBlockDrag();
      } else if (isResizing) {
        endBlockResize();
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggingBlock, resizingBlock, editBlockMode, handleBlockDrag, endBlockDrag, handleBlockResize, endBlockResize]);

  // Handle save
  const handleSave = async () => {
    setSaving(true);
    
    try {
      // Step 1: Save OCR blocks (positions and sizes) if they exist
      if (ocrBlocks && ocrBlocks.lines && ocrBlocks.lines.length > 0) {
        console.log('💾 Saving OCR blocks before contact save...');
        try {
          await saveOCRBlocks(ocrBlocks);
          console.log('✅ OCR blocks saved successfully');
        } catch (blockError) {
          console.error('❌ Failed to save OCR blocks:', blockError);
          toast.error('Failed to save block changes');
          setSaving(false);
          return;
        }
      }
      
      // Step 2: Check for contact field changes
      const hasFieldChanges = editableFields.some(
        field => editedData[field] !== (contact[field] || '')
      );

      // Step 3: Save contact data if there are changes
      if (hasFieldChanges) {
        await onSave(editedData);
        // Success handled by parent
      } else {
        // No field changes, but blocks were saved
        toast.success('Changes saved successfully');
        setSaving(false);
      }
      
    } catch (error) {
      console.error('Save error:', error);
      toast.error(translations.messages?.error || 'Failed to save');
      setSaving(false);
    }
  };

  // Handle field change
  const handleFieldChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Image URL
  const imageUrl = contact.photo_path 
    ? `/api/files/${contact.photo_path}`
    : null;

  // Loading state
  if (loading) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000
      }}>
        <div style={{
          backgroundColor: '#fff',
          padding: '40px',
          borderRadius: '16px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '18px', color: '#333', marginBottom: '15px' }}>
            {translations.loadingBlocks || 'Loading OCR blocks...'}
          </div>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #e2e8f0',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto'
          }} />
        </div>
      </div>
    );
  }

  // Main UI
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      zIndex: 10000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#1a1a1a',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '1400px',
        height: '90vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 30px',
          borderBottom: '1px solid #333',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, color: '#fff', fontSize: '20px' }}>
              {translations.title || 'OCR Editor'}
            </h2>
            <p style={{ margin: '5px 0 0 0', color: '#999', fontSize: '13px' }}>
              {translations.subtitle || 'Edit OCR results'}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#999',
              fontSize: '32px',
              cursor: 'pointer',
              padding: '0',
              lineHeight: 1
            }}
          >
            ×
          </button>
        </div>

        {/* Main content */}
        <div style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          gap: '20px',
          padding: '20px'
        }}>
          {/* Left panel - Image and blocks */}
          <div style={{
            flex: '1 1 60%',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px'
          }}>
            {/* Toolbar */}
            <OCRToolbar
              editBlockMode={editBlockMode}
              onToggleEditMode={() => setEditBlockMode(!editBlockMode)}
              reprocessing={reprocessing}
              onReprocess={reprocessOCR}
              isAddingBlock={isAddingBlock}
              onAddBlock={startAddingBlock}
              selectedBlocks={selectedBlocks}
              onEditBlockText={startEditBlockText}
              onSplitBlock={splitBlock}
              onDeleteBlock={deleteBlock}
              translations={translations}
            />

            {/* Image Canvas */}
            <ImageCanvas
              imageUrl={imageUrl}
              imageRef={imageRef}
              imageScale={imageScale}
              ocrBlocks={ocrBlocks}
              selectedBlocks={selectedBlocks}
              editMode={editBlockMode}
              draggingBlock={draggingBlock}
              dragPosition={dragPosition}
              resizingBlock={resizingBlock}
              resizeBox={resizeBox}
              isAddingBlock={isAddingBlock}
              onBlockClick={handleBlockClick}
              onBlockDragStart={startBlockDrag}
              onBlockResizeStart={startBlockResize}
              onMouseDown={handleNewBlockMouseDown}
              onMouseUp={handleNewBlockMouseUp}
              onBlockScaleFactorChange={setBlockScaleFactor}
              translations={translations}
            />

            {/* Selected blocks info */}
            {selectedBlocks.length > 0 && !assigningToField && (
              <div style={{
                padding: '15px',
                backgroundColor: '#2a2a2a',
                borderRadius: '8px',
                border: '2px solid #fbbf24'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    {translations.selectedBlocks || 'Selected blocks'}: {selectedBlocks.length}
                  </div>
                  <button
                    onClick={() => setAssigningToField(true)}
                    style={{
                      padding: '6px 12px',
                      fontSize: '13px',
                      backgroundColor: '#3b82f6',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    {translations.assignTo || 'Assign to field'} →
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right panel - Fields */}
          <FieldsSidebar
            editedData={editedData}
            selectedBlocks={selectedBlocks}
            onFieldChange={handleFieldChange}
            onAssignToField={assignToField}
            onSave={handleSave}
            onCancel={onClose}
            onReset={() => {
              const initial = {};
              editableFields.forEach(field => {
                initial[field] = contact[field] || '';
              });
              setEditedData(initial);
            }}
            saving={saving}
            translations={translations}
          />
        </div>
      </div>

      {/* Block Text Editor Modal */}
      {editingBlockText && (
        <BlockTextEditor
          block={editingBlockText}
          onSave={saveBlockText}
          onCancel={cancelEditBlockText}
          translations={translations}
        />
      )}

      {/* Assignment Panel */}
      {assigningToField && selectedBlocks.length > 0 && (
        <AssignmentPanel
          selectedBlocks={selectedBlocks}
          onAssign={assignToField}
          onCancel={() => setAssigningToField(false)}
          onClearSelection={clearSelection}
          translations={translations}
        />
      )}

      {/* Global styles for animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default OCREditorContainer;

