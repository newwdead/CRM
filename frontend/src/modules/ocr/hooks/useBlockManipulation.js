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
 * @param {string} language - Current language (ru/en)
 * @returns {object} Block manipulation state and operations
 */
export const useBlockManipulation = (ocrBlocks, setOcrBlocks, imageRef, imageScale, language = 'en') => {
  const [draggingBlock, setDraggingBlock] = useState(null);
  const [resizingBlock, setResizingBlock] = useState(null);
  const [editingBlockText, setEditingBlockText] = useState(null);
  const [isAddingBlock, setIsAddingBlock] = useState(null);
  const [newBlockStart, setNewBlockStart] = useState(null);
  const [editBlockMode, setEditBlockMode] = useState(false);

  /**
   * Start dragging a block
   */
  const startBlockDrag = (block, event) => {
    if (!editBlockMode) return;
    event.stopPropagation();
    setDraggingBlock(block);
  };

  /**
   * Handle block drag movement
   */
  const handleBlockDrag = (event) => {
    if (!draggingBlock || !editBlockMode || !imageRef.current) return;
    
    const rect = imageRef.current.getBoundingClientRect();
    
    // Calculate new position relative to image
    const x = (event.clientX - rect.left) / imageScale;
    const y = (event.clientY - rect.top) / imageScale;
    
    // Update block position (keeping width and height)
    setOcrBlocks(prev => ({
      ...prev,
      lines: prev.lines.map(line => 
        line === draggingBlock
          ? { 
              ...line, 
              box: { 
                ...line.box, 
                x: Math.max(0, Math.min(x, prev.image_width - line.box.width)),
                y: Math.max(0, Math.min(y, prev.image_height - line.box.height))
              } 
            }
          : line
      )
    }));
  };

  /**
   * End block drag
   */
  const endBlockDrag = () => {
    setDraggingBlock(null);
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
    resizingBlock,
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

