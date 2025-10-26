import { useState, useCallback } from 'react';

/**
 * Custom hook for managing contact-related modals
 * 
 * Handles:
 * - Image viewer modal
 * - Contact card modal
 * - OCR editor modal
 * - Table settings modal
 * 
 * @returns {object} Modal states and methods
 */
export const useContactModals = () => {
  // Image viewer state
  const [viewingImage, setViewingImage] = useState(null);
  
  // Contact card viewer state
  const [viewingContact, setViewingContact] = useState(null);
  
  // Table settings modal state
  const [showTableSettings, setShowTableSettings] = useState(false);

  /**
   * Open image viewer
   * @param {string} imageUrl - URL of image to view
   */
  const openImageViewer = useCallback((imageUrl) => {
    setViewingImage(imageUrl);
  }, []);

  /**
   * Close image viewer
   */
  const closeImageViewer = useCallback(() => {
    setViewingImage(null);
  }, []);

  /**
   * Open contact card
   * @param {object} contact - Contact object to view
   */
  const openContactCard = useCallback((contact) => {
    setViewingContact(contact);
  }, []);

  /**
   * Close contact card
   */
  const closeContactCard = useCallback(() => {
    setViewingContact(null);
  }, []);

  /**
   * Open table settings modal
   */
  const openTableSettings = useCallback(() => {
    setShowTableSettings(true);
  }, []);

  /**
   * Close table settings modal
   */
  const closeTableSettings = useCallback(() => {
    setShowTableSettings(false);
  }, []);

  return {
    // Image viewer
    viewingImage,
    openImageViewer,
    closeImageViewer,
    
    // Contact card
    viewingContact,
    openContactCard,
    closeContactCard,
    
    // Table settings
    showTableSettings,
    openTableSettings,
    closeTableSettings
  };
};

export default useContactModals;

