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
  draggingBlock,
  dragPosition,
  resizingBlock,
  resizeBox,
  isAddingBlock,
  onBlockClick,
  onBlockDragStart,
  onBlockResizeStart,
  onMouseDown,
  onMouseUp,
  onBlockScaleFactorChange,
  translations
}) => {
  const t = translations || {};
  const [realImageSize, setRealImageSize] = React.useState(null);
  const [blockScaleFactor, setBlockScaleFactor] = React.useState(1);

  console.log('🔵 ImageCanvas render:', {
    hasImage: !!imageUrl,
    hasBlocks: !!ocrBlocks,
    imageScale,
    blocksCount: ocrBlocks?.lines?.length,
    realImageSize,
    blockScaleFactor
  });

  const handleImageLoad = (e) => {
    const img = e.target;
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;
    
    // Get ACTUAL displayed size (after browser applies maxWidth/maxHeight)
    const displayedWidth = img.clientWidth;
    const displayedHeight = img.clientHeight;
    
    setRealImageSize({ width: displayedWidth, height: displayedHeight });
    
    // Calculate block scale factor based on displayed size vs OCR coordinates
    if (ocrBlocks && ocrBlocks.image_width && ocrBlocks.image_height) {
      const scaleX = displayedWidth / ocrBlocks.image_width;
      const scaleY = displayedHeight / ocrBlocks.image_height;
      const scaleFactor = (scaleX + scaleY) / 2;
      setBlockScaleFactor(scaleFactor);
      
      // Notify parent component
      if (onBlockScaleFactorChange) {
        onBlockScaleFactorChange(scaleFactor);
      }
      
      console.log('📸 Image loaded in Canvas:', {
        naturalSize: `${naturalWidth}x${naturalHeight}`,
        displayedSize: `${displayedWidth}x${displayedHeight}`,
        dbSize: `${ocrBlocks.image_width}x${ocrBlocks.image_height}`,
        displayScale: imageScale,
        blockScaleFactor: scaleFactor.toFixed(3),
        mismatch: (naturalWidth !== ocrBlocks.image_width || naturalHeight !== ocrBlocks.image_height) ? '⚠️ SIZE MISMATCH!' : '✅ MATCH'
      });
    }
  };

  if (!imageUrl || !ocrBlocks) {
    console.log('⚠️ ImageCanvas: Missing data', { imageUrl: !!imageUrl, ocrBlocks: !!ocrBlocks });
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
          onLoad={handleImageLoad}
          style={{
            display: 'block',
            maxWidth: '100%',
            maxHeight: '100%',
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
            width: realImageSize ? `${realImageSize.width * imageScale}px` : `${(ocrBlocks?.image_width || 0) * imageScale}px`,
            height: realImageSize ? `${realImageSize.height * imageScale}px` : `${(ocrBlocks?.image_height || 0) * imageScale}px`,
            pointerEvents: 'auto',
            cursor: isAddingBlock ? 'crosshair' : 'default'
          }}
        >
          {/* Render all OCR blocks */}
          {ocrBlocks.lines && ocrBlocks.lines.map((line, idx) => {
            const isSelected = selectedBlocks.includes(line);
            const selectionIndex = selectedBlocks.indexOf(line);
            const isDragging = draggingBlock === line;
            const tempPosition = isDragging ? dragPosition : null;
            const isResizing = resizingBlock === line;
            const tempBox = isResizing ? resizeBox : null;
            
            return (
              <BlockOverlay
                key={idx}
                block={line}
                index={idx}
                isSelected={isSelected}
                selectionIndex={selectionIndex}
                editMode={editMode}
                imageScale={imageScale}
                blockScaleFactor={blockScaleFactor}
                isDragging={isDragging}
                tempPosition={tempPosition}
                isResizing={isResizing}
                tempBox={tempBox}
                onClick={(e) => !editMode && onBlockClick && onBlockClick(line, e)}
                onDragStart={(e) => editMode && onBlockDragStart && onBlockDragStart(line, e)}
                onResizeStart={(handle, e) => editMode && onBlockResizeStart && onBlockResizeStart(line, handle, e)}
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

