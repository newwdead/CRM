import { useState } from 'react';
import toast from 'react-hot-toast';

/**
 * Custom hook for managing field assignment
 * 
 * Handles:
 * - Assigning selected blocks to contact fields
 * - Assignment mode state
 * - Field value updates
 * 
 * @param {array} selectedBlocks - Currently selected blocks
 * @param {function} clearSelection - Function to clear selection
 * @param {function} setEditedData - Setter for edited contact data
 * @param {function} saveOCRCorrections - Function to save OCR corrections
 * @param {object} translations - Translation object
 * @returns {object} Field assignment state and operations
 */
export const useFieldAssignment = (
  selectedBlocks,
  clearSelection,
  setEditedData,
  saveOCRCorrections,
  translations
) => {
  const [assigningToField, setAssigningToField] = useState(null);

  /**
   * Start field assignment mode
   */
  const startAssignment = () => {
    if (selectedBlocks.length === 0) {
      toast.error(
        translations?.selectBlock || 'Please select at least one block'
      );
      return;
    }
    setAssigningToField(true);
  };

  /**
   * Cancel field assignment
   */
  const cancelAssignment = () => {
    setAssigningToField(null);
  };

  /**
   * Assign selected blocks to a specific field
   * @param {string} fieldName - Name of the field to assign to
   */
  const assignToField = async (fieldName) => {
    if (selectedBlocks.length === 0) {
      toast.error(
        translations?.selectBlock || 'Please select at least one block'
      );
      return;
    }
    
    // Combine text from all selected blocks (separated by space)
    const combinedText = selectedBlocks.map(block => block.text).join(' ');
    
    // Update field value with combined text
    if (setEditedData) {
      setEditedData(prev => ({
        ...prev,
        [fieldName]: combinedText
      }));
    }
    
    // Save OCR corrections for training
    if (saveOCRCorrections) {
      await saveOCRCorrections(selectedBlocks, combinedText, fieldName);
    }
    
    // Show success message
    const previewText = combinedText.length > 30 
      ? combinedText.substring(0, 30) + '...' 
      : combinedText;
    
    const fieldLabel = translations?.fields?.[fieldName] || fieldName;
    toast.success(`Assigned: "${previewText}" → ${fieldLabel}`);
    
    // Clear selection
    if (clearSelection) {
      clearSelection();
    }
    
    // Exit assignment mode
    setAssigningToField(null);
  };

  /**
   * Quick assign without entering assignment mode
   * @param {string} fieldName - Name of the field to assign to
   */
  const quickAssign = async (fieldName) => {
    if (selectedBlocks.length === 0) return;
    await assignToField(fieldName);
  };

  return {
    assigningToField,
    setAssigningToField,
    startAssignment,
    cancelAssignment,
    assignToField,
    quickAssign
  };
};

