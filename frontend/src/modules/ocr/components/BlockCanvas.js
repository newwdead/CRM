/**
 * BlockCanvas Component
 * Отображение и взаимодействие с блоками OCR на изображении
 */

import React from 'react';

export const BlockCanvas = ({
  blocks,
  imageScale,
  selectedBlocks,
  editMode,
  draggingBlock,
  resizingBlock,
  onBlockClick,
  onBlockDragStart,
  onBlockResizeStart
}) => {
  if (!blocks || !blocks.lines) return null;

  const isBlockSelected = (index) => {
    return selectedBlocks && selectedBlocks.includes(index);
  };

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: blocks.image_width * imageScale,
      height: blocks.image_height * imageScale,
      pointerEvents: 'none'
    }}>
      {blocks.lines.map((block, index) => {
        const selected = isBlockSelected(index);
        const isDragging = draggingBlock === index;
        const isResizing = resizingBlock?.index === index;

        return (
          <div
            key={index}
            onClick={(e) => {
              e.stopPropagation();
              onBlockClick(index);
            }}
            onMouseDown={(e) => {
              if (editMode) {
                e.stopPropagation();
                onBlockDragStart(index, e);
              }
            }}
            style={{
              position: 'absolute',
              left: block.box.x * imageScale,
              top: block.box.y * imageScale,
              width: block.box.width * imageScale,
              height: block.box.height * imageScale,
              border: `2px solid ${
                isDragging || isResizing
                  ? '#ff9800'
                  : selected
                  ? '#2196f3'
                  : 'rgba(33, 150, 243, 0.5)'
              }`,
              backgroundColor: selected
                ? 'rgba(33, 150, 243, 0.1)'
                : 'rgba(33, 150, 243, 0.05)',
              cursor: editMode ? 'move' : 'pointer',
              pointerEvents: 'auto',
              transition: isDragging || isResizing ? 'none' : 'all 0.2s'
            }}
          >
            {/* Resize handles - только в режиме редактирования */}
            {editMode && selected && (
              <>
                {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map(corner => (
                  <div
                    key={corner}
                    onMouseDown={(e) => {
                      e.stopPropagation();
                      onBlockResizeStart(index, corner, e);
                    }}
                    style={{
                      position: 'absolute',
                      width: '8px',
                      height: '8px',
                      backgroundColor: '#2196f3',
                      border: '1px solid white',
                      borderRadius: '50%',
                      cursor: `${corner.replace('-', '-')}-resize`,
                      ...(corner.includes('top') ? { top: '-4px' } : { bottom: '-4px' }),
                      ...(corner.includes('left') ? { left: '-4px' } : { right: '-4px' }),
                      pointerEvents: 'auto',
                      zIndex: 10
                    }}
                  />
                ))}
              </>
            )}

            {/* Текст блока */}
            {!editMode && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: 0,
                backgroundColor: 'rgba(33, 150, 243, 0.9)',
                color: 'white',
                padding: '2px 6px',
                borderRadius: '3px 3px 0 0',
                fontSize: '11px',
                whiteSpace: 'nowrap',
                maxWidth: '200px',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {block.text}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

