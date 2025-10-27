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
      console.log('🔵 useOCRBlocks: Loading blocks for contact', contactId);
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contactId}/ocr-blocks`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to load OCR blocks');

      const data = await response.json();
      console.log('🔵 useOCRBlocks: Loaded blocks:', {
        lines: data.lines?.length,
        imageSize: `${data.image_width}x${data.image_height}`
      });
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
   * Reprocess OCR - completely rerun OCR from scratch with OCR v2.0
   */
  const reprocessOCR = async () => {
    setReprocessing(true);
    try {
      const token = localStorage.getItem('token');
      
      // Call rerun-ocr endpoint (runs OCR v2.0 from scratch)
      const response = await fetch(`/api/contacts/${contactId}/rerun-ocr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to rerun OCR');

      const result = await response.json();
      
      console.log('🔄 OCR rerun result:', result);
      
      // Update contact data with new OCR results
      if (result.contact && editableFields && setEditedData) {
        Object.keys(result.contact).forEach(key => {
          if (editableFields.includes(key)) {
            setEditedData(prev => ({
              ...prev,
              [key]: result.contact[key] || prev[key]
            }));
          }
        });
      }
      
      const successMessage = translations?.reprocessSuccess || 
        `OCR rerun successful: ${result.blocks_count} blocks detected with ${result.provider}`;
      toast.success(successMessage);
      
      // Reload OCR blocks
      await loadOCRBlocks();
      
    } catch (error) {
      console.error('Error rerunning OCR:', error);
      if (translations && translations.reprocessError) {
        toast.error(translations.reprocessError);
      } else {
        toast.error('Failed to rerun OCR');
      }
    } finally {
      setReprocessing(false);
    }
  };

  /**
   * Save modified OCR blocks (positions and sizes)
   */
  const saveOCRBlocks = async (blocks) => {
    if (!blocks || !blocks.lines || blocks.lines.length === 0) {
      console.warn('⚠️ No blocks to save');
      return false;
    }

    try {
      console.log('💾 Saving OCR blocks:', {
        count: blocks.lines.length,
        imageSize: `${blocks.image_width}x${blocks.image_height}`,
        firstBlock: blocks.lines[0],
        allBlocks: blocks.lines.map((b, i) => `${i}: ${b.text?.substring(0, 20)}`)
      });

      const payload = {
        blocks: blocks.lines,
        image_width: blocks.image_width,
        image_height: blocks.image_height
      };
      
      console.log('📤 Payload being sent:', JSON.stringify(payload).substring(0, 500) + '...');

      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contactId}/save-ocr-blocks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save blocks');
      }

      const result = await response.json();
      console.log('✅ OCR blocks saved:', result);
      return true;
    } catch (error) {
      console.error('❌ Error saving OCR blocks:', error);
      throw error;
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
    saveOCRBlocks,
    saveOCRCorrections
  };
};
