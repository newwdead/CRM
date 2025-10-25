/**
 * Duplicates API Module
 * Микросервис для работы с дубликатами - полностью изолированный
 * Не зависит от contactsApi или других модулей
 */

/**
 * Получить все контакты для поиска дубликатов
 * Прямой запрос без зависимостей
 */
export const getDuplicatesContacts = async () => {
  // Get token - check both keys
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  
  if (!token) {
    throw new Error('No authentication token');
  }
  
  // Direct relative URL - no absolute paths, no protocol
  const response = await fetch('/api/contacts?skip=0&limit=10000', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    },
    credentials: 'same-origin'
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  return Array.isArray(data) ? data : (data.items || data.contacts || []);
};

/**
 * Объединить дубликаты
 */
export const mergeDuplicates = async (masterId, slaveIds) => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  
  if (!token) {
    throw new Error('No authentication token');
  }
  
  const response = await fetch('/api/contacts/merge', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      master_id: masterId,
      slave_ids: slaveIds
    })
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    throw new Error(`HTTP ${response.status}`);
  }
  
  return await response.json();
};

