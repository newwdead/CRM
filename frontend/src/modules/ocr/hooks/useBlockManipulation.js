import { useState } from 'react';
import toast from 'react-hot-toast';

/**
 * Custom hook for managing OCR block manipulation
 * 
 * Handles:
 * - Dragging blocks (move position)
 * - Resizing blocks
 * - Deleting blocks
 * - Adding new blocks
 * - Editing block text
 * - Splitting blocks
 * 
 * @param {object} ocrBlocks - OCR blocks data
 * @param {function} setOcrBlocks - Setter for OCR blocks
 * @param {object} imageRef - Ref to image container
 * @param {number} imageScale - Current image scale
 * @param {number} blockScaleFactor - Block coordinate scale factor
 * @param {string} language - Current language (ru/en)
 * @returns {object} Block manipulation state and operations
 */
export const useBlockManipulation = (ocrBlocks, setOcrBlocks, imageRef, imageScale, blockScaleFactor = 1, language = 'en') => {
  const [draggingBlock, setDraggingBlock] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [dragPosition, setDragPosition] = useState(null); // Temporary position during drag
  const [resizingBlock, setResizingBlock] = useState(null);
  const [resizeHandle, setResizeHandle] = useState(null); // Which handle is being dragged
  const [resizeStart, setResizeStart] = useState(null); // Start position and size
  const [resizeBox, setResizeBox] = useState(null); // Temporary box during resize
  const [editingBlockText, setEditingBlockText] = useState(null);
  const [isAddingBlock, setIsAddingBlock] = useState(null);
  const [newBlockStart, setNewBlockStart] = useState(null);
  const [editBlockMode, setEditBlockMode] = useState(false);

  /**
   * Start dragging a block
   */
  const startBlockDrag = (block, event) => {
    if (!editBlockMode || !imageRef.current) return;
    event.stopPropagation();
    
    const rect = imageRef.current.getBoundingClientRect();
    
    // Calculate mouse position in displayed image coordinates
    const mouseX = (event.clientX - rect.left) / imageScale;
    const mouseY = (event.clientY - rect.top) / imageScale;
    
    // Calculate block position in displayed coordinates
    const scaledBlockX = block.box.x * blockScaleFactor;
    const scaledBlockY = block.box.y * blockScaleFactor;
    
    // Store offset between mouse and block top-left corner
    setDragOffset({
      x: mouseX - scaledBlockX,
      y: mouseY - scaledBlockY
    });
    
    setDraggingBlock(block);
    
    console.log('🔵 Drag start:', {
      mouse: `${mouseX.toFixed(0)}, ${mouseY.toFixed(0)}`,
      blockScaled: `${scaledBlockX.toFixed(0)}, ${scaledBlockY.toFixed(0)}`,
      offset: `${(mouseX - scaledBlockX).toFixed(0)}, ${(mouseY - scaledBlockY).toFixed(0)}`,
      blockScaleFactor
    });
  };

  /**
   * Handle block drag movement
   */
  const handleBlockDrag = (event) => {
    if (!draggingBlock || !editBlockMode || !imageRef.current) return;
    
    const rect = imageRef.current.getBoundingClientRect();
    
    // Calculate mouse position in displayed image coordinates
    const mouseX = (event.clientX - rect.left) / imageScale;
    const mouseY = (event.clientY - rect.top) / imageScale;
    
    // Calculate new block position (subtract offset)
    const newScaledX = mouseX - dragOffset.x;
    const newScaledY = mouseY - dragOffset.y;
    
    // Convert back to OCR coordinate space
    const newX = newScaledX / blockScaleFactor;
    const newY = newScaledY / blockScaleFactor;
    
    // Store temporary position for rendering
    setDragPosition({ x: newX, y: newY });
  };

  /**
   * End block drag
   */
  const endBlockDrag = () => {
    if (draggingBlock && dragPosition) {
      // Apply final position to state
      setOcrBlocks(prev => {
        const maxWidth = prev.image_width;
        const maxHeight = prev.image_height;
        
        return {
          ...prev,
          lines: prev.lines.map(line => 
            line === draggingBlock
              ? { 
                  ...line, 
                  box: { 
                    ...line.box, 
                    x: Math.max(0, Math.min(dragPosition.x, maxWidth - line.box.width)),
                    y: Math.max(0, Math.min(dragPosition.y, maxHeight - line.box.height))
                  } 
                }
              : line
          )
        };
      });
    }
    
    setDraggingBlock(null);
    setDragPosition(null);
  };

  /**
   * Start resizing a block
   */
  const startBlockResize = (block, handle, event) => {
    if (!editBlockMode || !imageRef.current) return;
    event.stopPropagation();
    
    const rect = imageRef.current.getBoundingClientRect();
    const mouseX = (event.clientX - rect.left) / imageScale;
    const mouseY = (event.clientY - rect.top) / imageScale;
    
    setResizingBlock(block);
    setResizeHandle(handle);
    setResizeStart({
      mouseX,
      mouseY,
      box: { ...block.box }
    });
    
    console.log('🔵 Resize start:', { handle, box: block.box });
  };

  /**
   * Handle block resize movement
   */
  const handleBlockResize = (event) => {
    if (!resizingBlock || !resizeStart || !imageRef.current) return;
    
    const rect = imageRef.current.getBoundingClientRect();
    const mouseX = (event.clientX - rect.left) / imageScale;
    const mouseY = (event.clientY - rect.top) / imageScale;
    
    // Calculate delta in scaled coordinates
    const deltaX = (mouseX - resizeStart.mouseX) / blockScaleFactor;
    const deltaY = (mouseY - resizeStart.mouseY) / blockScaleFactor;
    
    const startBox = resizeStart.box;
    let newBox = { ...startBox };
    
    // Apply delta based on which handle is being dragged
    switch (resizeHandle) {
      case 'se': // Bottom-right corner
        newBox.width = Math.max(20, startBox.width + deltaX);
        newBox.height = Math.max(20, startBox.height + deltaY);
        break;
      case 'sw': // Bottom-left corner
        newBox.x = startBox.x + deltaX;
        newBox.width = Math.max(20, startBox.width - deltaX);
        newBox.height = Math.max(20, startBox.height + deltaY);
        break;
      case 'ne': // Top-right corner
        newBox.y = startBox.y + deltaY;
        newBox.width = Math.max(20, startBox.width + deltaX);
        newBox.height = Math.max(20, startBox.height - deltaY);
        break;
      case 'nw': // Top-left corner
        newBox.x = startBox.x + deltaX;
        newBox.y = startBox.y + deltaY;
        newBox.width = Math.max(20, startBox.width - deltaX);
        newBox.height = Math.max(20, startBox.height - deltaY);
        break;
      case 'e': // Right edge
        newBox.width = Math.max(20, startBox.width + deltaX);
        break;
      case 'w': // Left edge
        newBox.x = startBox.x + deltaX;
        newBox.width = Math.max(20, startBox.width - deltaX);
        break;
      case 'n': // Top edge
        newBox.y = startBox.y + deltaY;
        newBox.height = Math.max(20, startBox.height - deltaY);
        break;
      case 's': // Bottom edge
        newBox.height = Math.max(20, startBox.height + deltaY);
        break;
    }
    
    // Store temporary box for rendering
    setResizeBox(newBox);
  };

  /**
   * End block resize
   */
  const endBlockResize = () => {
    if (resizingBlock && resizeBox) {
      // Apply final size to state
      setOcrBlocks(prev => {
        const maxWidth = prev.image_width;
        const maxHeight = prev.image_height;
        
        return {
          ...prev,
          lines: prev.lines.map(line => 
            line === resizingBlock
              ? { 
                  ...line, 
                  box: { 
                    ...resizeBox,
                    x: Math.max(0, Math.min(resizeBox.x, maxWidth - resizeBox.width)),
                    y: Math.max(0, Math.min(resizeBox.y, maxHeight - resizeBox.height)),
                    width: Math.min(resizeBox.width, maxWidth - resizeBox.x),
                    height: Math.min(resizeBox.height, maxHeight - resizeBox.y)
                  } 
                }
              : line
          )
        };
      });
    }
    
    setResizingBlock(null);
    setResizeHandle(null);
    setResizeStart(null);
    setResizeBox(null);
  };

  /**
   * Delete a block
   */
  const deleteBlock = (block) => {
    const confirmMessage = language === 'ru' ? 'Удалить этот блок?' : 'Delete this block?';
    
    if (!window.confirm(confirmMessage)) {
      return;
    }
    
    setOcrBlocks(prev => ({
      ...prev,
      lines: prev.lines.filter(line => line !== block)
    }));
    
    const successMessage = language === 'ru' ? 'Блок удален' : 'Block deleted';
    toast.success(successMessage);
  };

  /**
   * Start adding a new block
   */
  const startAddingBlock = () => {
    setIsAddingBlock(true);
    const message = language === 'ru' ? 'Выделите область для нового блока' : 'Draw area for new block';
    toast.info(message);
  };

  /**
   * Handle mouse down for new block creation
   */
  const handleNewBlockMouseDown = (event) => {
    if (!isAddingBlock || !imageRef.current) return;
    
    const container = imageRef.current.parentElement;
    const rect = container.getBoundingClientRect();
    const x = (event.clientX - rect.left) / imageScale;
    const y = (event.clientY - rect.top) / imageScale;
    
    setNewBlockStart({ x, y });
  };

  /**
   * Handle mouse up for new block creation
   */
  const handleNewBlockMouseUp = (event) => {
    if (!isAddingBlock || !newBlockStart || !imageRef.current) return;
    
    const container = imageRef.current.parentElement;
    const rect = container.getBoundingClientRect();
    const x = (event.clientX - rect.left) / imageScale;
    const y = (event.clientY - rect.top) / imageScale;
    
    const width = Math.abs(x - newBlockStart.x);
    const height = Math.abs(y - newBlockStart.y);
    
    if (width < 20 || height < 10) {
      const errorMessage = language === 'ru' ? 'Блок слишком маленький' : 'Block too small';
      toast.error(errorMessage);
      setIsAddingBlock(false);
      setNewBlockStart(null);
      return;
    }
    
    const newBlock = {
      text: language === 'ru' ? 'Новый текст' : 'New text',
      box: {
        x: Math.min(newBlockStart.x, x),
        y: Math.min(newBlockStart.y, y),
        width: width,
        height: height
      },
      confidence: 0
    };
    
    setOcrBlocks(prev => ({
      ...prev,
      lines: [...prev.lines, newBlock]
    }));
    
    setIsAddingBlock(false);
    setNewBlockStart(null);
    
    const successMessage = language === 'ru' ? 'Блок добавлен' : 'Block added';
    toast.success(successMessage);
  };

  /**
   * Cancel adding new block
   */
  const cancelAddingBlock = () => {
    setIsAddingBlock(false);
    setNewBlockStart(null);
  };

  /**
   * Start editing block text
   */
  const startEditBlockText = (block) => {
    setEditingBlockText(block);
  };

  /**
   * Save edited block text
   */
  const saveBlockText = (newText) => {
    setOcrBlocks(prev => ({
      ...prev,
      lines: prev.lines.map(line => 
        line === editingBlockText
          ? { ...line, text: newText }
          : line
      )
    }));
    
    setEditingBlockText(null);
    
    const successMessage = language === 'ru' ? 'Текст сохранен' : 'Text saved';
    toast.success(successMessage);
  };

  /**
   * Cancel editing block text
   */
  const cancelEditBlockText = () => {
    setEditingBlockText(null);
  };

  /**
   * Split a block into two blocks (vertically)
   */
  const splitBlock = (block) => {
    const midY = block.box.y + block.box.height / 2;
    
    const block1 = {
      ...block,
      box: {
        ...block.box,
        height: block.box.height / 2
      },
      text: block.text.substring(0, Math.floor(block.text.length / 2))
    };
    
    const block2 = {
      ...block,
      box: {
        ...block.box,
        y: midY,
        height: block.box.height / 2
      },
      text: block.text.substring(Math.floor(block.text.length / 2))
    };
    
    setOcrBlocks(prev => ({
      ...prev,
      lines: prev.lines.map(line => line === block ? block1 : line).concat([block2])
    }));
    
    const successMessage = language === 'ru' ? 'Блок разбит на два' : 'Block split into two';
    toast.success(successMessage);
  };

  /**
   * Toggle edit block mode
   */
  const toggleEditMode = () => {
    setEditBlockMode(prev => !prev);
    if (editBlockMode) {
      // Exiting edit mode, clear any active operations
      setDraggingBlock(null);
      setIsAddingBlock(false);
      setNewBlockStart(null);
    }
  };

  return {
    // State
    draggingBlock,
    dragPosition,
    resizingBlock,
    resizeBox,
    editingBlockText,
    isAddingBlock,
    newBlockStart,
    editBlockMode,
    
    // Edit mode
    setEditBlockMode,
    toggleEditMode,
    
    // Drag & drop
    startBlockDrag,
    handleBlockDrag,
    endBlockDrag,
    
    // Resize
    startBlockResize,
    handleBlockResize,
    endBlockResize,
    
    // Add/delete
    deleteBlock,
    startAddingBlock,
    cancelAddingBlock,
    handleNewBlockMouseDown,
    handleNewBlockMouseUp,
    
    // Text editing
    startEditBlockText,
    saveBlockText,
    cancelEditBlockText,
    
    // Split
    splitBlock
  };
};

