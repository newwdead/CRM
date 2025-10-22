/**
 * Hook для управления контактами
 * Изолированная логика работы с контактами
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  getContacts, 
  updateContact, 
  deleteContact, 
  bulkUpdateContacts, 
  bulkDeleteContacts 
} from '../api/contactsApi';
import toast from 'react-hot-toast';

export const useContacts = (filterParams, language = 'ru') => {
  const [contacts, setContacts] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);

  const translations = {
    en: {
      loadError: 'Failed to load contacts',
      updateSuccess: 'Contact updated',
      updateError: 'Failed to update contact',
      deleteSuccess: 'Contact deleted',
      deleteError: 'Failed to delete contact',
      bulkUpdateSuccess: 'Contacts updated',
      bulkUpdateError: 'Failed to update contacts',
      bulkDeleteSuccess: 'Contacts deleted',
      bulkDeleteError: 'Failed to delete contacts'
    },
    ru: {
      loadError: 'Ошибка загрузки контактов',
      updateSuccess: 'Контакт обновлен',
      updateError: 'Ошибка обновления контакта',
      deleteSuccess: 'Контакт удален',
      deleteError: 'Ошибка удаления контакта',
      bulkUpdateSuccess: 'Контакты обновлены',
      bulkUpdateError: 'Ошибка обновления контактов',
      bulkDeleteSuccess: 'Контакты удалены',
      bulkDeleteError: 'Ошибка удаления контактов'
    }
  };

  const t = translations[language];

  // Загрузка контактов
  const loadContacts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getContacts(filterParams);
      
      setContacts(data.contacts || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (error) {
      console.error('Error loading contacts:', error);
      toast.error(t.loadError);
      setContacts([]);
    } finally {
      setLoading(false);
    }
  }, [filterParams, t.loadError]);

  // Автозагрузка при изменении фильтров
  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  // Обновление контакта
  const handleUpdateContact = useCallback(async (contactId, data) => {
    try {
      const updated = await updateContact(contactId, data);
      setContacts(prev => 
        prev.map(c => c.id === contactId ? { ...c, ...updated } : c)
      );
      toast.success(t.updateSuccess);
      return updated;
    } catch (error) {
      console.error('Error updating contact:', error);
      toast.error(t.updateError);
      throw error;
    }
  }, [t.updateSuccess, t.updateError]);

  // Удаление контакта
  const handleDeleteContact = useCallback(async (contactId) => {
    try {
      await deleteContact(contactId);
      setContacts(prev => prev.filter(c => c.id !== contactId));
      setSelected(prev => prev.filter(id => id !== contactId));
      toast.success(t.deleteSuccess);
      await loadContacts(); // Перезагрузка для обновления пагинации
    } catch (error) {
      console.error('Error deleting contact:', error);
      toast.error(t.deleteError);
      throw error;
    }
  }, [t.deleteSuccess, t.deleteError, loadContacts]);

  // Массовое обновление
  const handleBulkUpdate = useCallback(async (data) => {
    if (selected.length === 0) return;
    
    try {
      await bulkUpdateContacts(selected, data);
      toast.success(t.bulkUpdateSuccess);
      setSelected([]);
      await loadContacts();
    } catch (error) {
      console.error('Error bulk updating contacts:', error);
      toast.error(t.bulkUpdateError);
      throw error;
    }
  }, [selected, t.bulkUpdateSuccess, t.bulkUpdateError, loadContacts]);

  // Массовое удаление
  const handleBulkDelete = useCallback(async () => {
    if (selected.length === 0) return;
    
    try {
      await bulkDeleteContacts(selected);
      toast.success(t.bulkDeleteSuccess);
      setSelected([]);
      await loadContacts();
    } catch (error) {
      console.error('Error bulk deleting contacts:', error);
      toast.error(t.bulkDeleteError);
      throw error;
    }
  }, [selected, t.bulkDeleteSuccess, t.bulkDeleteError, loadContacts]);

  // Выбор контактов
  const toggleSelect = useCallback((contactId) => {
    setSelected(prev => 
      prev.includes(contactId)
        ? prev.filter(id => id !== contactId)
        : [...prev, contactId]
    );
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selected.length === contacts.length) {
      setSelected([]);
    } else {
      setSelected(contacts.map(c => c.id));
    }
  }, [selected, contacts]);

  const clearSelection = useCallback(() => {
    setSelected([]);
  }, []);

  return {
    // Данные
    contacts,
    selected,
    loading,
    total,
    pages,
    
    // Методы
    refresh: loadContacts,
    updateContact: handleUpdateContact,
    deleteContact: handleDeleteContact,
    bulkUpdate: handleBulkUpdate,
    bulkDelete: handleBulkDelete,
    
    // Выбор
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    isSelected: (id) => selected.includes(id),
    selectedCount: selected.length,
    allSelected: selected.length === contacts.length && contacts.length > 0
  };
};

