/**
 * Contacts API Module
 * Все API вызовы для работы с контактами
 */

const API_BASE = '/api';

/**
 * Получить список контактов с фильтрами и пагинацией
 */
export const getContacts = async (params = {}) => {
  const token = localStorage.getItem('token');
  const queryParams = new URLSearchParams(params).toString();
  const url = `${API_BASE}/contacts/?${queryParams}`;
  
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch contacts');
  }
  
  return await response.json();
};

/**
 * Обновить контакт
 */
export const updateContact = async (contactId, data) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/contacts/${contactId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    throw new Error('Failed to update contact');
  }
  
  return await response.json();
};

/**
 * Удалить контакт
 */
export const deleteContact = async (contactId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/contacts/${contactId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete contact');
  }
  
  return await response.json();
};

/**
 * Массовое обновление контактов
 */
export const bulkUpdateContacts = async (contactIds, data) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/contacts/bulk-update`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ contact_ids: contactIds, ...data })
  });
  
  if (!response.ok) {
    throw new Error('Failed to bulk update contacts');
  }
  
  return await response.json();
};

/**
 * Массовое удаление контактов
 */
export const bulkDeleteContacts = async (contactIds) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/contacts/bulk-delete`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ contact_ids: contactIds })
  });
  
  if (!response.ok) {
    throw new Error('Failed to bulk delete contacts');
  }
  
  return await response.json();
};

/**
 * Экспорт контактов
 */
export const exportContacts = async (format = 'csv', filters = {}) => {
  const token = localStorage.getItem('token');
  const queryParams = new URLSearchParams({ ...filters, format }).toString();
  const url = `${API_BASE}/contacts/export?${queryParams}`;
  
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) {
    throw new Error('Failed to export contacts');
  }
  
  return await response.blob();
};

