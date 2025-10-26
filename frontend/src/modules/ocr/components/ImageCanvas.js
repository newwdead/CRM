import React from 'react';
import BlockOverlay from './BlockOverlay';

/**
 * Image Canvas Component
 * 
 * Displays business card image with OCR block overlays
 * Handles mouse interactions for block selection and addition
 * 
 * @param {object} props - Component props
 * @param {string} props.imageUrl - Image URL
 * @param {object} props.imageRef - Ref for image element
 * @param {number} props.imageScale - Image scale factor
 * @param {object} props.ocrBlocks - OCR blocks data
 * @param {array} props.selectedBlocks - Selected blocks
 * @param {boolean} props.editMode - Whether edit mode is enabled
 * @param {boolean} props.isAddingBlock - Whether adding new block
 * @param {function} props.onBlockClick - Block click handler
 * @param {function} props.onBlockDragStart - Block drag start handler
 * @param {function} props.onMouseDown - Image mouse down handler
 * @param {function} props.onMouseUp - Image mouse up handler
 * @param {object} props.translations - Translation object
 */
const ImageCanvas = ({
  imageUrl,
  imageRef,
  imageScale = 1,
  ocrBlocks,
  selectedBlocks = [],
  editMode,
  isAddingBlock,
  onBlockClick,
  onBlockDragStart,
  onMouseDown,
  onMouseUp,
  translations
}) => {
  const t = translations || {};

  if (!imageUrl || !ocrBlocks) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000',
        borderRadius: '8px',
        color: '#666',
        fontSize: '14px'
      }}>
        {t.noBlocks || 'No image or OCR data'}
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      position: 'relative',
      overflow: 'auto',
      backgroundColor: '#000',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px'
    }}>
      {/* Image container */}
      <div style={{
        position: 'relative',
        display: 'inline-block'
      }}>
        {/* Business card image */}
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Business Card"
          style={{
            display: 'block',
            maxWidth: '100%',
            maxHeight: '100%',
            transform: `scale(${imageScale})`,
            transformOrigin: 'top left',
            userSelect: 'none'
          }}
          draggable={false}
        />
        
        {/* SVG overlay for blocks */}
        <svg
          onMouseDown={onMouseDown}
          onMouseUp={onMouseUp}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: `${(ocrBlocks.image_width || 0) * imageScale}px`,
            height: `${(ocrBlocks.image_height || 0) * imageScale}px`,
            pointerEvents: 'auto',
            cursor: isAddingBlock ? 'crosshair' : 'default'
          }}
        >
          {/* Render all OCR blocks */}
          {ocrBlocks.lines && ocrBlocks.lines.map((line, idx) => {
            const isSelected = selectedBlocks.includes(line);
            const selectionIndex = selectedBlocks.indexOf(line);
            
            return (
              <BlockOverlay
                key={idx}
                block={line}
                index={idx}
                isSelected={isSelected}
                selectionIndex={selectionIndex}
                editMode={editMode}
                imageScale={imageScale}
                onClick={(e) => !editMode && onBlockClick && onBlockClick(line, e)}
                onDragStart={(e) => editMode && onBlockDragStart && onBlockDragStart(line, e)}
              />
            );
          })}
        </svg>

        {/* Adding block hint */}
        {isAddingBlock && (
          <div style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(59, 130, 246, 0.9)',
            color: '#fff',
            padding: '8px 16px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '600',
            pointerEvents: 'none',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
          }}>
            ✏️ {t.newBlock || 'Draw area for new block'}
          </div>
        )}
      </div>

      {/* Scale indicator */}
      {imageScale !== 1 && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          color: '#fff',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: '600'
        }}>
          {Math.round(imageScale * 100)}%
        </div>
      )}
    </div>
  );
};

export default ImageCanvas;

