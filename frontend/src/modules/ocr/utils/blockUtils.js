/**
 * Utility functions for OCR block manipulations
 */

/**
 * Calculate block position on scaled image
 * @param {object} block - Block with box coordinates
 * @param {number} imageScale - Current image scale
 * @param {object} imageOffset - Image offset {x, y}
 * @returns {object} Scaled position {x, y, width, height}
 */
export const calculateBlockPosition = (block, imageScale, imageOffset = { x: 0, y: 0 }) => {
  if (!block || !block.box) return null;

  return {
    x: block.box.x * imageScale + imageOffset.x,
    y: block.box.y * imageScale + imageOffset.y,
    width: block.box.width * imageScale,
    height: block.box.height * imageScale
  };
};

/**
 * Check if two blocks intersect
 * @param {object} block1 - First block
 * @param {object} block2 - Second block
 * @returns {boolean} True if blocks intersect
 */
export const isBlockIntersecting = (block1, block2) => {
  if (!block1 || !block2 || !block1.box || !block2.box) return false;

  const b1 = block1.box;
  const b2 = block2.box;

  return !(
    b1.x + b1.width < b2.x ||
    b2.x + b2.width < b1.x ||
    b1.y + b1.height < b2.y ||
    b2.y + b2.height < b1.y
  );
};

/**
 * Merge multiple blocks into one
 * Combines text and creates bounding box
 * @param {array} blocks - Array of blocks to merge
 * @returns {object} Merged block
 */
export const mergeBlocks = (blocks) => {
  if (!blocks || blocks.length === 0) return null;
  if (blocks.length === 1) return blocks[0];

  // Combine text
  const text = blocks.map(b => b.text).join(' ');

  // Calculate bounding box
  const minX = Math.min(...blocks.map(b => b.box.x));
  const minY = Math.min(...blocks.map(b => b.box.y));
  const maxX = Math.max(...blocks.map(b => b.box.x + b.box.width));
  const maxY = Math.max(...blocks.map(b => b.box.y + b.box.height));

  // Average confidence
  const avgConfidence = blocks.reduce((sum, b) => sum + (b.confidence || 0), 0) / blocks.length;

  return {
    text,
    box: {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY
    },
    confidence: avgConfidence
  };
};

/**
 * Split block vertically at Y position
 * @param {object} block - Block to split
 * @param {number} splitY - Y position to split at (relative to block)
 * @returns {array} Array of two blocks [top, bottom]
 */
export const splitBlockVertically = (block, splitY) => {
  if (!block || !block.box) return [block];

  const midY = block.box.y + (splitY || block.box.height / 2);
  const textMid = Math.floor(block.text.length / 2);

  const block1 = {
    ...block,
    box: {
      ...block.box,
      height: midY - block.box.y
    },
    text: block.text.substring(0, textMid)
  };

  const block2 = {
    ...block,
    box: {
      ...block.box,
      y: midY,
      height: block.box.y + block.box.height - midY
    },
    text: block.text.substring(textMid)
  };

  return [block1, block2];
};

/**
 * Split block horizontally at X position
 * @param {object} block - Block to split
 * @param {number} splitX - X position to split at (relative to block)
 * @returns {array} Array of two blocks [left, right]
 */
export const splitBlockHorizontally = (block, splitX) => {
  if (!block || !block.box) return [block];

  const midX = block.box.x + (splitX || block.box.width / 2);
  const textMid = Math.floor(block.text.length / 2);

  const block1 = {
    ...block,
    box: {
      ...block.box,
      width: midX - block.box.x
    },
    text: block.text.substring(0, textMid)
  };

  const block2 = {
    ...block,
    box: {
      ...block.box,
      x: midX,
      width: block.box.x + block.box.width - midX
    },
    text: block.text.substring(textMid)
  };

  return [block1, block2];
};

/**
 * Sort blocks by reading order (top to bottom, left to right)
 * @param {array} blocks - Array of blocks to sort
 * @returns {array} Sorted blocks
 */
export const sortBlocksByReadingOrder = (blocks) => {
  if (!blocks || blocks.length === 0) return [];

  return [...blocks].sort((a, b) => {
    const yDiff = a.box.y - b.box.y;
    // If Y difference is small (< 10px), consider same line
    if (Math.abs(yDiff) < 10) {
      return a.box.x - b.box.x; // Sort by X
    }
    return yDiff; // Sort by Y
  });
};

/**
 * Get blocks within a specific area
 * @param {array} blocks - Array of blocks
 * @param {object} area - Area {x, y, width, height}
 * @returns {array} Blocks within area
 */
export const getBlocksInArea = (blocks, area) => {
  if (!blocks || !area) return [];

  return blocks.filter(block => {
    if (!block.box) return false;

    const b = block.box;
    const blockCenterX = b.x + b.width / 2;
    const blockCenterY = b.y + b.height / 2;

    return (
      blockCenterX >= area.x &&
      blockCenterX <= area.x + area.width &&
      blockCenterY >= area.y &&
      blockCenterY <= area.y + area.height
    );
  });
};

/**
 * Calculate confidence color (green for high, red for low)
 * @param {number} confidence - Confidence value (0-100)
 * @returns {string} Hex color code
 */
export const getConfidenceColor = (confidence) => {
  if (confidence >= 80) return '#10b981'; // Green
  if (confidence >= 60) return '#f59e0b'; // Orange
  return '#ef4444'; // Red
};

/**
 * Validate block data
 * @param {object} block - Block to validate
 * @returns {boolean} True if block is valid
 */
export const isValidBlock = (block) => {
  return (
    block &&
    block.box &&
    typeof block.box.x === 'number' &&
    typeof block.box.y === 'number' &&
    typeof block.box.width === 'number' &&
    typeof block.box.height === 'number' &&
    block.box.width > 0 &&
    block.box.height > 0 &&
    typeof block.text === 'string' &&
    block.text.length > 0
  );
};

