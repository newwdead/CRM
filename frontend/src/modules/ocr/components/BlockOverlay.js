import React from 'react';
import { calculateBlockPosition } from '../utils/blockUtils';

/**
 * Block Overlay Component
 * 
 * Renders a single OCR block as SVG rect overlay on image
 * 
 * @param {object} props - Component props
 * @param {object} props.block - Block data with box and text
 * @param {number} props.index - Block index
 * @param {boolean} props.isSelected - Whether block is selected
 * @param {number} props.selectionIndex - Index in selection (-1 if not selected)
 * @param {boolean} props.editMode - Whether edit mode is enabled
 * @param {number} props.imageScale - Image scale factor
 * @param {number} props.blockScaleFactor - Block scale factor (for coordinate transformation)
 * @param {function} props.onClick - Click handler
 * @param {function} props.onDragStart - Drag start handler
 * @param {string} props.fieldColor - Field color if assigned
 */
const BlockOverlay = ({
  block,
  index,
  isSelected,
  selectionIndex = -1,
  editMode,
  imageScale,
  blockScaleFactor = 1,
  isDragging,
  tempPosition,
  isResizing,
  tempBox,
  onClick,
  onDragStart,
  onResizeStart,
  fieldColor
}) => {
  if (!block || !block.box) return null;

  const box = block.box;
  
  // Use tempPosition if dragging, tempBox if resizing, otherwise use block's actual position
  let x, y, width, height;
  
  if (isResizing && tempBox) {
    x = tempBox.x;
    y = tempBox.y;
    width = tempBox.width;
    height = tempBox.height;
  } else if (isDragging && tempPosition) {
    x = tempPosition.x;
    y = tempPosition.y;
    width = box.width;
    height = box.height;
  } else {
    x = box.x;
    y = box.y;
    width = box.width;
    height = box.height;
  }
  
  const scaledBox = {
    x: x * blockScaleFactor * imageScale,
    y: y * blockScaleFactor * imageScale,
    width: width * blockScaleFactor * imageScale,
    height: height * blockScaleFactor * imageScale
  };

  // Determine fill and stroke based on state
  let fill, stroke, strokeWidth;
  
  if (isSelected) {
    fill = 'rgba(251, 191, 36, 0.3)'; // Yellow
    stroke = '#fbbf24';
    strokeWidth = 3;
  } else if (editMode) {
    fill = 'rgba(16, 185, 129, 0.2)'; // Green
    stroke = '#10b981';
    strokeWidth = 2;
  } else if (fieldColor) {
    // Convert hex to rgba
    const r = parseInt(fieldColor.slice(1, 3), 16);
    const g = parseInt(fieldColor.slice(3, 5), 16);
    const b = parseInt(fieldColor.slice(5, 7), 16);
    fill = `rgba(${r}, ${g}, ${b}, 0.3)`;
    stroke = fieldColor;
    strokeWidth = 2;
  } else {
    fill = 'rgba(59, 130, 246, 0.2)'; // Blue
    stroke = '#3b82f6';
    strokeWidth = 1;
  }

  return (
    <g>
      {/* Block rectangle */}
      <rect
        x={scaledBox.x}
        y={scaledBox.y}
        width={scaledBox.width}
        height={scaledBox.height}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        style={{
          pointerEvents: 'auto',
          cursor: editMode ? 'move' : 'pointer',
          transition: 'all 0.2s'
        }}
        onClick={onClick}
        onMouseDown={editMode ? onDragStart : undefined}
      />
      
      {/* Block number/checkmark */}
      <text
        x={scaledBox.x + 5}
        y={scaledBox.y + 15}
        fill="#fff"
        fontSize="12"
        fontWeight="bold"
        style={{ 
          pointerEvents: 'none',
          textShadow: '1px 1px 2px rgba(0,0,0,0.8)'
        }}
      >
        {isSelected ? `✓${selectionIndex + 1}` : index + 1}
      </text>
      
      {/* Confidence indicator (optional) */}
      {block.confidence !== undefined && block.confidence < 80 && (
        <text
          x={scaledBox.x + scaledBox.width - 25}
          y={scaledBox.y + 15}
          fill={block.confidence < 60 ? '#ef4444' : '#f59e0b'}
          fontSize="10"
          fontWeight="bold"
          style={{ 
            pointerEvents: 'none',
            textShadow: '1px 1px 2px rgba(0,0,0,0.8)'
          }}
        >
          {Math.round(block.confidence)}%
        </text>
      )}
      
      {/* Resize handles (only in edit mode and not while dragging) */}
      {editMode && !isDragging && onResizeStart && (
        <>
          {/* Corner handles */}
          <circle
            cx={scaledBox.x}
            cy={scaledBox.y}
            r="6"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'nw-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('nw', e)}
          />
          <circle
            cx={scaledBox.x + scaledBox.width}
            cy={scaledBox.y}
            r="6"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'ne-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('ne', e)}
          />
          <circle
            cx={scaledBox.x}
            cy={scaledBox.y + scaledBox.height}
            r="6"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'sw-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('sw', e)}
          />
          <circle
            cx={scaledBox.x + scaledBox.width}
            cy={scaledBox.y + scaledBox.height}
            r="6"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'se-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('se', e)}
          />
          
          {/* Edge handles (midpoints) */}
          <circle
            cx={scaledBox.x + scaledBox.width / 2}
            cy={scaledBox.y}
            r="5"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'n-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('n', e)}
          />
          <circle
            cx={scaledBox.x + scaledBox.width / 2}
            cy={scaledBox.y + scaledBox.height}
            r="5"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 's-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('s', e)}
          />
          <circle
            cx={scaledBox.x}
            cy={scaledBox.y + scaledBox.height / 2}
            r="5"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'w-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('w', e)}
          />
          <circle
            cx={scaledBox.x + scaledBox.width}
            cy={scaledBox.y + scaledBox.height / 2}
            r="5"
            fill="#fff"
            stroke="#3b82f6"
            strokeWidth="2"
            style={{ cursor: 'e-resize', pointerEvents: 'auto' }}
            onMouseDown={(e) => onResizeStart('e', e)}
          />
        </>
      )}
    </g>
  );
};

export default BlockOverlay;

