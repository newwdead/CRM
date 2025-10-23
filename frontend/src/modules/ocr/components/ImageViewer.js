/**
 * ImageViewer Component
 * Отображение изображения визитки
 */

import React, { useRef, useEffect } from 'react';

export const ImageViewer = ({ 
  imageUrl, 
  imageScale, 
  onScaleChange,
  children,
  onMouseDown,
  onMouseMove,
  onMouseUp
}) => {
  const imageRef = useRef(null);
  const containerRef = useRef(null);

  // Вычисление масштаба при загрузке
  useEffect(() => {
    const calculateScale = () => {
      if (!imageRef.current || !containerRef.current) return;

      const container = containerRef.current;
      const image = imageRef.current;

      const containerWidth = container.offsetWidth;
      const imageWidth = image.naturalWidth;

      if (imageWidth > 0 && containerWidth > 0) {
        const scale = Math.min(containerWidth / imageWidth, 1);
        onScaleChange(scale);
      }
    };

    const image = imageRef.current;
    if (image && image.complete) {
      calculateScale();
    } else if (image) {
      image.addEventListener('load', calculateScale);
      return () => image.removeEventListener('load', calculateScale);
    }
  }, [imageUrl, onScaleChange]);

  return (
    <div 
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        minHeight: '400px',
        maxHeight: '80vh',
        overflow: 'auto',
        border: '1px solid #ddd',
        borderRadius: '4px',
        backgroundColor: '#f5f5f5',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        cursor: onMouseDown ? 'crosshair' : 'default'
      }}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
    >
      <div style={{
        position: 'relative',
        display: 'inline-block'
      }}>
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Business card"
          style={{
            display: 'block',
            maxWidth: '100%',
            height: 'auto',
            transform: `scale(${imageScale})`,
            transformOrigin: 'top left',
            userSelect: 'none'
          }}
        />
        {children}
      </div>
    </div>
  );
};

