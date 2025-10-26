import { useState } from 'react';

/**
 * Custom hook for managing OCR block selection
 * 
 * Handles:
 * - Single block selection
 * - Multi-block selection (with Ctrl/Cmd key)
 * - Clear selection
 * - Multi-select mode toggle
 * 
 * @returns {object} Selection state and operations
 */
export const useBlockSelection = () => {
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [multiSelectMode, setMultiSelectMode] = useState(false);

  /**
   * Handle block click with optional multi-select
   * @param {object} block - Block to select/deselect
   * @param {Event} event - Mouse event (to check Ctrl/Cmd key)
   */
  const handleBlockClick = (block, event) => {
    // Multi-select with Ctrl/Cmd key
    if (event && (event.ctrlKey || event.metaKey)) {
      setSelectedBlocks(prev => {
        const isSelected = prev.some(b => b === block);
        if (isSelected) {
          // Remove block from selection
          return prev.filter(b => b !== block);
        } else {
          // Add block to selection
          return [...prev, block];
        }
      });
    } else {
      // Single select (replace selection)
      setSelectedBlocks([block]);
    }
  };

  /**
   * Clear all selected blocks
   */
  const clearSelection = () => {
    setSelectedBlocks([]);
  };

  /**
   * Select multiple blocks
   * @param {array} blocks - Array of blocks to select
   */
  const selectMultipleBlocks = (blocks) => {
    setSelectedBlocks(blocks);
  };

  /**
   * Check if a block is selected
   * @param {object} block - Block to check
   * @returns {boolean} True if block is selected
   */
  const isBlockSelected = (block) => {
    return selectedBlocks.some(b => b === block);
  };

  /**
   * Toggle multi-select mode
   */
  const toggleMultiSelectMode = () => {
    setMultiSelectMode(prev => !prev);
  };

  /**
   * Add block to selection (without replacing)
   * @param {object} block - Block to add
   */
  const addToSelection = (block) => {
    setSelectedBlocks(prev => {
      const isAlreadySelected = prev.some(b => b === block);
      if (isAlreadySelected) {
        return prev; // Already selected, don't duplicate
      }
      return [...prev, block];
    });
  };

  /**
   * Remove block from selection
   * @param {object} block - Block to remove
   */
  const removeFromSelection = (block) => {
    setSelectedBlocks(prev => prev.filter(b => b !== block));
  };

  return {
    selectedBlocks,
    multiSelectMode,
    setMultiSelectMode,
    handleBlockClick,
    clearSelection,
    selectMultipleBlocks,
    isBlockSelected,
    toggleMultiSelectMode,
    addToSelection,
    removeFromSelection
  };
};

