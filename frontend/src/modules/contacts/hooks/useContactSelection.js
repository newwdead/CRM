import { useState, useCallback } from 'react';

/**
 * Custom hook for managing contact selection
 * 
 * Handles:
 * - Multi-select contacts
 * - Select all/deselect all
 * - Toggle individual selection
 * 
 * @returns {object} Selection state and methods
 */
export const useContactSelection = () => {
  const [selected, setSelected] = useState([]);

  /**
   * Toggle selection for a single contact
   * @param {number} id - Contact ID
   */
  const toggle = useCallback((id) => {
    setSelected(prevSelected => 
      prevSelected.includes(id) 
        ? prevSelected.filter(x => x !== id) 
        : [...prevSelected, id]
    );
  }, []);

  /**
   * Toggle all contacts (select/deselect all)
   * @param {array} contacts - Array of contacts
   */
  const toggleAll = useCallback((contacts) => {
    if (selected.length === contacts.length) {
      setSelected([]);
    } else {
      setSelected(contacts.map(c => c.id));
    }
  }, [selected.length]);

  /**
   * Clear all selections
   */
  const clearSelection = useCallback(() => {
    setSelected([]);
  }, []);

  /**
   * Set specific IDs as selected
   * @param {array} ids - Array of contact IDs
   */
  const setSelection = useCallback((ids) => {
    setSelected(ids);
  }, []);

  /**
   * Check if a contact is selected
   * @param {number} id - Contact ID
   * @returns {boolean} Whether the contact is selected
   */
  const isSelected = useCallback((id) => {
    return selected.includes(id);
  }, [selected]);

  /**
   * Get count of selected contacts
   * @returns {number} Number of selected contacts
   */
  const selectedCount = selected.length;

  /**
   * Check if all contacts are selected
   * @param {array} contacts - Array of contacts
   * @returns {boolean} Whether all contacts are selected
   */
  const isAllSelected = useCallback((contacts) => {
    return contacts.length > 0 && selected.length === contacts.length;
  }, [selected.length]);

  return {
    selected,
    selectedCount,
    toggle,
    toggleAll,
    clearSelection,
    setSelection,
    isSelected,
    isAllSelected
  };
};

export default useContactSelection;

