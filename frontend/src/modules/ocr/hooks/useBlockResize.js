/**
 * Hook для изменения размера блоков
 * Изолированная логика resize
 */

import { useState, useCallback, useRef } from 'react';

export const useBlockResize = (blocks, updateBlock, imageScale) => {
  const [resizingBlock, setResizingBlock] = useState(null);
  const resizeStartData = useRef(null);

  const handleResizeStart = useCallback((blockIndex, corner, event) => {
    event.stopPropagation();
    const block = blocks?.lines[blockIndex];
    if (!block) return;

    setResizingBlock({ index: blockIndex, corner });
    resizeStartData.current = {
      mouseX: event.clientX,
      mouseY: event.clientY,
      box: { ...block.box }
    };
  }, [blocks]);

  const handleResize = useCallback((event) => {
    if (!resizingBlock || !resizeStartData.current || !blocks) return;

    const { index, corner } = resizingBlock;
    const block = blocks.lines[index];
    if (!block) return;

    const dx = (event.clientX - resizeStartData.current.mouseX) / imageScale;
    const dy = (event.clientY - resizeStartData.current.mouseY) / imageScale;

    const originalBox = resizeStartData.current.box;
    let newBox = { ...originalBox };

    // Минимальные размеры
    const minWidth = 20;
    const minHeight = 10;

    switch (corner) {
      case 'top-left':
        newBox.x = originalBox.x + dx;
        newBox.y = originalBox.y + dy;
        newBox.width = originalBox.width - dx;
        newBox.height = originalBox.height - dy;
        break;
      case 'top-right':
        newBox.y = originalBox.y + dy;
        newBox.width = originalBox.width + dx;
        newBox.height = originalBox.height - dy;
        break;
      case 'bottom-left':
        newBox.x = originalBox.x + dx;
        newBox.width = originalBox.width - dx;
        newBox.height = originalBox.height + dy;
        break;
      case 'bottom-right':
        newBox.width = originalBox.width + dx;
        newBox.height = originalBox.height + dy;
        break;
      default:
        return;
    }

    // Проверка минимальных размеров
    if (newBox.width < minWidth || newBox.height < minHeight) return;

    // Проверка границ
    if (newBox.x < 0 || newBox.y < 0) return;
    if (newBox.x + newBox.width > blocks.image_width) return;
    if (newBox.y + newBox.height > blocks.image_height) return;

    updateBlock(index, { box: newBox });
  }, [resizingBlock, blocks, imageScale, updateBlock]);

  const handleResizeEnd = useCallback(() => {
    setResizingBlock(null);
    resizeStartData.current = null;
  }, []);

  return {
    resizingBlock,
    handleResizeStart,
    handleResize,
    handleResizeEnd,
    isResizing: resizingBlock !== null
  };
};

