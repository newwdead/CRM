import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

/**
 * Custom hook for managing OCR blocks state and operations
 * 
 * Handles:
 * - Loading OCR blocks from API
 * - Reprocessing OCR with updated blocks
 * - Loading state management
 * 
 * @param {number} contactId - Contact ID
 * @param {function} calculateImageScale - Callback to calculate image scale after load
 * @param {array} editableFields - List of editable field names
 * @param {function} setEditedData - Setter for edited data
 * @param {object} translations - Translation object
 * @returns {object} OCR blocks state and operations
 */
export const useOCRBlocks = (contactId, calculateImageScale, editableFields, setEditedData, translations) => {
  const [ocrBlocks, setOcrBlocks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reprocessing, setReprocessing] = useState(false);

  /**
   * Load OCR blocks from API
   */
  const loadOCRBlocks = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contactId}/ocr-blocks`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to load OCR blocks');

      const data = await response.json();
      setOcrBlocks(data);
      
      // Calculate image scale to fit container
      if (calculateImageScale && data.image_width && data.image_height) {
        calculateImageScale(data.image_width, data.image_height);
      }
      
    } catch (error) {
      console.error('Error loading OCR blocks:', error);
      if (translations && translations.messages) {
        toast.error(translations.messages.loadError || 'Failed to load OCR blocks');
      } else {
        toast.error('Failed to load OCR blocks');
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Reprocess OCR with current blocks
   */
  const reprocessOCR = async () => {
    if (!ocrBlocks || !ocrBlocks.lines) {
      toast.error('No OCR blocks to reprocess');
      return;
    }

    setReprocessing(true);
    try {
      const token = localStorage.getItem('token');
      
      // Send updated blocks to backend
      const response = await fetch(`/api/contacts/${contactId}/reprocess-ocr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          blocks: ocrBlocks.lines.map(line => ({
            text: line.text,
            box: line.box,
            confidence: line.confidence
          }))
        })
      });

      if (!response.ok) throw new Error('Failed to reprocess OCR');

      const data = await response.json();
      
      // Update contact data with new OCR results
      if (editableFields && setEditedData) {
        Object.keys(data).forEach(key => {
          if (editableFields.includes(key)) {
            setEditedData(prev => ({
              ...prev,
              [key]: data[key] || prev[key]
            }));
          }
        });
      }
      
      if (translations && translations.reprocessSuccess) {
        toast.success(translations.reprocessSuccess);
      } else {
        toast.success('OCR reprocessed successfully');
      }
      
      // Reload OCR blocks
      await loadOCRBlocks();
      
    } catch (error) {
      console.error('Error reprocessing OCR:', error);
      if (translations && translations.reprocessError) {
        toast.error(translations.reprocessError);
      } else {
        toast.error('Failed to reprocess OCR');
      }
    } finally {
      setReprocessing(false);
    }
  };

  /**
   * Save OCR corrections for training
   * This is used when a user assigns a block to a field
   */
  const saveOCRCorrections = async (blocks, correctedText, correctedField) => {
    if (!blocks || blocks.length === 0) return;

    try {
      const token = localStorage.getItem('token');
      
      for (const block of blocks) {
        await fetch(`/api/contacts/${contactId}/ocr-corrections`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            original_text: block.text,
            original_box: block.box,
            original_confidence: Math.round(block.confidence),
            corrected_text: correctedText,
            corrected_field: correctedField,
            ocr_provider: 'tesseract',
            language: 'rus+eng'
          })
        });
      }
    } catch (error) {
      console.error('Failed to save correction:', error);
      // Don't show error to user, this is background training data
    }
  };

  // Load OCR blocks on mount
  useEffect(() => {
    if (contactId) {
      loadOCRBlocks();
    }
  }, [contactId]);

  return {
    ocrBlocks,
    setOcrBlocks,
    loading,
    reprocessing,
    loadOCRBlocks,
    reprocessOCR,
    saveOCRCorrections
  };
};
