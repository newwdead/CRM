import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

/**
 * Custom hook for bulk contact operations
 * 
 * Handles:
 * - Bulk edit contacts
 * - Bulk delete contacts
 * - Export contacts (CSV, XLSX)
 * - Create new contact
 * 
 * @param {object} options - Hook options
 * @param {string} options.lang - Language (ru/en)
 * @param {function} options.onSuccess - Callback after successful operation
 * @returns {object} Bulk operations state and methods
 */
export const useBulkOperations = ({ lang = 'ru', onSuccess } = {}) => {
  // Bulk edit state
  const [showBulkEdit, setShowBulkEdit] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({});
  
  // New contact state
  const [showNewContact, setShowNewContact] = useState(false);
  const [newContact, setNewContact] = useState({
    full_name: '', company: '', position: '', email: '',
    phone: '', address: '', comment: '', website: ''
  });

  /**
   * Apply bulk edit to selected contacts
   * @param {array} selectedIds - Array of contact IDs
   * @returns {Promise<boolean>} Success status
   */
  const applyBulkEdit = useCallback(async (selectedIds) => {
    const fields = Object.fromEntries(
      Object.entries(bulkEditData).filter(([k, v]) => v && v.trim() !== '')
    );
    
    if (!Object.keys(fields).length) {
      toast.error(lang === 'ru' ? 'Заполните хотя бы одно поле' : 'Fill at least one field');
      return false;
    }
    
    const token = localStorage.getItem('token');
    const headers = { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
    
    try {
      const response = await fetch('/api/contacts/update_bulk', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ ids: selectedIds, fields })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update contacts');
      }
      
      setShowBulkEdit(false);
      setBulkEditData({});
      toast.success(lang === 'ru' ? 'Контакты обновлены' : 'Contacts updated');
      
      if (onSuccess) onSuccess();
      return true;
    } catch (error) {
      console.error('Error in bulk edit:', error);
      toast.error(lang === 'ru' ? 'Ошибка обновления' : 'Update failed');
      return false;
    }
  }, [bulkEditData, lang, onSuccess]);

  /**
   * Delete selected contacts
   * @param {array} selectedIds - Array of contact IDs
   * @returns {Promise<boolean>} Success status
   */
  const deleteSelected = useCallback(async (selectedIds) => {
    if (!selectedIds.length) {
      toast.error(lang === 'ru' ? 'Ничего не выбрано' : 'Nothing selected');
      return false;
    }
    
    const confirmMessage = lang === 'ru' 
      ? `Удалить выбранные контакты? (${selectedIds.length})`
      : `Delete selected contacts? (${selectedIds.length})`;
      
    if (!window.confirm(confirmMessage)) {
      return false;
    }
    
    const token = localStorage.getItem('token');
    const headers = { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
    
    try {
      const response = await fetch('/api/contacts/delete_bulk', {
        method: 'POST',
        headers,
        body: JSON.stringify(selectedIds)
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete contacts');
      }
      
      toast.success(lang === 'ru' ? 'Контакты удалены' : 'Contacts deleted');
      
      if (onSuccess) onSuccess();
      return true;
    } catch (error) {
      console.error('Error deleting contacts:', error);
      toast.error(lang === 'ru' ? 'Ошибка удаления' : 'Delete failed');
      return false;
    }
  }, [lang, onSuccess]);

  /**
   * Export selected contacts
   * @param {array} selectedIds - Array of contact IDs
   * @param {string} format - Export format ('csv' or 'xlsx')
   * @returns {Promise<boolean>} Success status
   */
  const exportSelected = useCallback(async (selectedIds, format = 'csv') => {
    if (!selectedIds.length) {
      toast.error(lang === 'ru' ? 'Ничего не выбрано' : 'Nothing selected');
      return false;
    }
    
    const ids = selectedIds.join(',');
    const url = format === 'xlsx'
      ? `/api/contacts/export/xlsx?ids=${encodeURIComponent(ids)}`
      : `/api/contacts/export?ids=${encodeURIComponent(ids)}`;
    
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const a = document.createElement('a');
      const href = window.URL.createObjectURL(blob);
      a.href = href;
      a.download = format === 'xlsx' ? 'contacts.xlsx' : 'contacts.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(href);
      
      toast.success(lang === 'ru' ? 'Экспорт выполнен' : 'Export completed');
      return true;
    } catch (error) {
      console.error('Export error:', error);
      toast.error(lang === 'ru' ? 'Ошибка экспорта' : 'Export failed');
      return false;
    }
  }, [lang]);

  /**
   * Create new contact
   * @returns {Promise<boolean>} Success status
   */
  const createNew = useCallback(async () => {
    const empty = Object.values(newContact).every(v => !v);
    if (empty) {
      toast.error(lang === 'ru' ? 'Заполните хотя бы одно поле' : 'Fill at least one field');
      return false;
    }
    
    const token = localStorage.getItem('token');
    const headers = { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
    
    try {
      const response = await fetch('/api/contacts/', {
        method: 'POST',
        headers,
        body: JSON.stringify(newContact)
      });
      
      if (!response.ok) {
        const error = await response.json();
        toast.error(`Error: ${error.detail || 'Failed to create contact'}`);
        return false;
      }
      
      setNewContact({
        full_name: '', company: '', position: '', email: '',
        phone: '', address: '', comment: '', website: ''
      });
      setShowNewContact(false);
      toast.success(lang === 'ru' ? 'Контакт создан' : 'Contact created');
      
      if (onSuccess) onSuccess();
      return true;
    } catch (error) {
      console.error('Error creating contact:', error);
      toast.error(lang === 'ru' ? 'Сетевая ошибка' : 'Network error');
      return false;
    }
  }, [newContact, lang, onSuccess]);

  return {
    // Bulk edit state
    showBulkEdit,
    setShowBulkEdit,
    bulkEditData,
    setBulkEditData,
    
    // New contact state
    showNewContact,
    setShowNewContact,
    newContact,
    setNewContact,
    
    // Methods
    applyBulkEdit,
    deleteSelected,
    exportSelected,
    createNew
  };
};

export default useBulkOperations;

