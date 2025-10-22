/**
 * Hook для перетаскивания блоков
 * Изолированная логика drag & drop
 */

import { useState, useCallback, useRef } from 'react';

export const useBlockDrag = (blocks, updateBlock, imageScale) => {
  const [draggingBlock, setDraggingBlock] = useState(null);
  const dragStartPos = useRef(null);

  const handleDragStart = useCallback((blockIndex, event) => {
    event.stopPropagation();
    const block = blocks?.lines[blockIndex];
    if (!block) return;

    setDraggingBlock(blockIndex);
    dragStartPos.current = {
      mouseX: event.clientX,
      mouseY: event.clientY,
      blockX: block.box.x,
      blockY: block.box.y
    };
  }, [blocks]);

  const handleDrag = useCallback((event) => {
    if (draggingBlock === null || !dragStartPos.current || !blocks) return;

    const block = blocks.lines[draggingBlock];
    if (!block) return;

    // Вычисляем смещение от начальной позиции
    const dx = (event.clientX - dragStartPos.current.mouseX) / imageScale;
    const dy = (event.clientY - dragStartPos.current.mouseY) / imageScale;

    // Новые координаты
    let newX = dragStartPos.current.blockX + dx;
    let newY = dragStartPos.current.blockY + dy;

    // Ограничение границ
    newX = Math.max(0, Math.min(newX, blocks.image_width - block.box.width));
    newY = Math.max(0, Math.min(newY, blocks.image_height - block.box.height));

    // Обновляем блок
    updateBlock(draggingBlock, {
      box: {
        ...block.box,
        x: newX,
        y: newY
      }
    });
  }, [draggingBlock, blocks, imageScale, updateBlock]);

  const handleDragEnd = useCallback(() => {
    setDraggingBlock(null);
    dragStartPos.current = null;
  }, []);

  return {
    draggingBlock,
    handleDragStart,
    handleDrag,
    handleDragEnd,
    isDragging: draggingBlock !== null
  };
};

