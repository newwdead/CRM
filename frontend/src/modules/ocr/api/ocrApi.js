/**
 * OCR API Module
 * Все API вызовы для OCR функционала
 */

const API_BASE = '';

/**
 * Получить OCR блоки для контакта
 */
export const getOCRBlocks = async (contactId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/contacts/${contactId}/ocr-blocks`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to load OCR blocks');
  }
  
  return await response.json();
};

/**
 * Повторно обработать OCR с обновленными блоками
 */
export const reprocessOCR = async (contactId, blocks) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/contacts/${contactId}/reprocess-ocr`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ blocks })
  });
  
  if (!response.ok) {
    throw new Error('Failed to reprocess OCR');
  }
  
  return await response.json();
};

/**
 * Обновить данные контакта из OCR
 */
export const updateContactFromOCR = async (contactId, fields) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/contacts/${contactId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(fields)
  });
  
  if (!response.ok) {
    throw new Error('Failed to update contact');
  }
  
  return await response.json();
};

