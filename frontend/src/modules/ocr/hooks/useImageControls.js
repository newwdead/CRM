import { useState, useRef } from 'react';

/**
 * Custom hook for managing image display controls
 * 
 * Handles:
 * - Image scaling/zoom
 * - Image offset/pan
 * - Calculating scale to fit container
 * 
 * @returns {object} Image control state and operations
 */
export const useImageControls = () => {
  const [imageScale, setImageScale] = useState(1);
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });
  const imageRef = useRef(null);

  /**
   * Calculate image scale to fit in container
   * @param {number} imgWidth - Image width in pixels
   * @param {number} imgHeight - Image height in pixels
   */
  const calculateImageScale = (imgWidth, imgHeight) => {
    if (!imageRef.current) return;
    
    const container = imageRef.current.parentElement;
    if (!container) return;
    
    const maxWidth = container.clientWidth - 40; // padding
    const maxHeight = container.clientHeight - 40;
    
    const scaleX = maxWidth / imgWidth;
    const scaleY = maxHeight / imgHeight;
    const scale = Math.min(scaleX, scaleY, 1); // Don't scale up beyond original size
    
    setImageScale(scale);
  };

  /**
   * Zoom in
   * @param {number} factor - Zoom factor (default 1.2)
   */
  const zoomIn = (factor = 1.2) => {
    setImageScale(prev => Math.min(prev * factor, 3)); // Max zoom 3x
  };

  /**
   * Zoom out
   * @param {number} factor - Zoom factor (default 0.8)
   */
  const zoomOut = (factor = 0.8) => {
    setImageScale(prev => Math.max(prev * factor, 0.1)); // Min zoom 0.1x
  };

  /**
   * Reset zoom to fit
   */
  const resetZoom = () => {
    setImageScale(1);
    setImageOffset({ x: 0, y: 0 });
  };

  /**
   * Set custom zoom level
   * @param {number} scale - New scale value
   */
  const setZoom = (scale) => {
    setImageScale(Math.max(0.1, Math.min(scale, 3)));
  };

  /**
   * Pan image by offset
   * @param {number} dx - X offset
   * @param {number} dy - Y offset
   */
  const panImage = (dx, dy) => {
    setImageOffset(prev => ({
      x: prev.x + dx,
      y: prev.y + dy
    }));
  };

  /**
   * Set image offset directly
   * @param {number} x - X position
   * @param {number} y - Y position
   */
  const setImagePosition = (x, y) => {
    setImageOffset({ x, y });
  };

  /**
   * Reset image position to center
   */
  const resetPosition = () => {
    setImageOffset({ x: 0, y: 0 });
  };

  return {
    imageScale,
    imageOffset,
    imageRef,
    setImageScale,
    setImageOffset,
    calculateImageScale,
    zoomIn,
    zoomOut,
    resetZoom,
    setZoom,
    panImage,
    setImagePosition,
    resetPosition
  };
};

