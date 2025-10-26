/**
 * Utility functions for image manipulation and calculations
 */

/**
 * Calculate scale to fit image in container
 * @param {number} imageWidth - Original image width
 * @param {number} imageHeight - Original image height
 * @param {number} containerWidth - Container width
 * @param {number} containerHeight - Container height
 * @param {number} padding - Padding to account for (default 40px)
 * @returns {number} Scale factor (0.1 to 1.0, never scale up)
 */
export const calculateFitScale = (
  imageWidth,
  imageHeight,
  containerWidth,
  containerHeight,
  padding = 40
) => {
  if (!imageWidth || !imageHeight || !containerWidth || !containerHeight) {
    return 1;
  }

  const maxWidth = containerWidth - padding;
  const maxHeight = containerHeight - padding;

  const scaleX = maxWidth / imageWidth;
  const scaleY = maxHeight / imageHeight;

  // Use smallest scale to fit both dimensions, but don't scale up
  return Math.min(scaleX, scaleY, 1);
};

/**
 * Get mouse position relative to image
 * @param {Event} event - Mouse event
 * @param {HTMLElement} imageElement - Image DOM element
 * @param {number} imageScale - Current image scale
 * @returns {object} Position {x, y} relative to original image coordinates
 */
export const getMousePositionOnImage = (event, imageElement, imageScale = 1) => {
  if (!event || !imageElement) return { x: 0, y: 0 };

  const rect = imageElement.getBoundingClientRect();

  const x = (event.clientX - rect.left) / imageScale;
  const y = (event.clientY - rect.top) / imageScale;

  return { x, y };
};

/**
 * Clamp position within image bounds
 * @param {number} x - X position
 * @param {number} y - Y position
 * @param {number} width - Element width
 * @param {number} height - Element height
 * @param {number} imageWidth - Image width
 * @param {number} imageHeight - Image height
 * @returns {object} Clamped position {x, y}
 */
export const clampPosition = (x, y, width, height, imageWidth, imageHeight) => {
  return {
    x: Math.max(0, Math.min(x, imageWidth - width)),
    y: Math.max(0, Math.min(y, imageHeight - height))
  };
};

/**
 * Calculate scaled dimensions
 * @param {number} width - Original width
 * @param {number} height - Original height
 * @param {number} scale - Scale factor
 * @returns {object} Scaled dimensions {width, height}
 */
export const scaleSize = (width, height, scale) => {
  return {
    width: width * scale,
    height: height * scale
  };
};

/**
 * Convert screen coordinates to image coordinates
 * @param {number} screenX - Screen X position
 * @param {number} screenY - Screen Y position
 * @param {HTMLElement} imageElement - Image DOM element
 * @param {number} imageScale - Current image scale
 * @param {object} imageOffset - Image offset {x, y}
 * @returns {object} Image coordinates {x, y}
 */
export const screenToImageCoords = (
  screenX,
  screenY,
  imageElement,
  imageScale,
  imageOffset = { x: 0, y: 0 }
) => {
  if (!imageElement) return { x: 0, y: 0 };

  const rect = imageElement.getBoundingClientRect();

  return {
    x: (screenX - rect.left - imageOffset.x) / imageScale,
    y: (screenY - rect.top - imageOffset.y) / imageScale
  };
};

/**
 * Convert image coordinates to screen coordinates
 * @param {number} imageX - Image X position
 * @param {number} imageY - Image Y position
 * @param {HTMLElement} imageElement - Image DOM element
 * @param {number} imageScale - Current image scale
 * @param {object} imageOffset - Image offset {x, y}
 * @returns {object} Screen coordinates {x, y}
 */
export const imageToScreenCoords = (
  imageX,
  imageY,
  imageElement,
  imageScale,
  imageOffset = { x: 0, y: 0 }
) => {
  if (!imageElement) return { x: 0, y: 0 };

  const rect = imageElement.getBoundingClientRect();

  return {
    x: rect.left + imageX * imageScale + imageOffset.x,
    y: rect.top + imageY * imageScale + imageOffset.y
  };
};

/**
 * Get image natural dimensions
 * @param {string} imageUrl - Image URL
 * @returns {Promise<object>} Promise resolving to {width, height}
 */
export const getImageDimensions = (imageUrl) => {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      resolve({
        width: img.naturalWidth,
        height: img.naturalHeight
      });
    };

    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };

    img.src = imageUrl;
  });
};

/**
 * Check if point is within image bounds
 * @param {number} x - X position
 * @param {number} y - Y position
 * @param {number} imageWidth - Image width
 * @param {number} imageHeight - Image height
 * @returns {boolean} True if point is within bounds
 */
export const isWithinImageBounds = (x, y, imageWidth, imageHeight) => {
  return x >= 0 && x <= imageWidth && y >= 0 && y <= imageHeight;
};

