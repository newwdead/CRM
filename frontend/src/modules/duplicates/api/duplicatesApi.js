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
  
  // CRITICAL: Add cache-busting version parameter to bypass Service Worker cache
  const timestamp = Date.now();
  const version = '5.2.2';
  
  // IMPORTANT: Backend uses 'page' not 'skip'! Max limit is 100, so we need to fetch multiple pages
  // For now, fetch a large enough page (limit=100 is max, so page=1&limit=100 gets first 100)
  // TODO: Implement proper pagination if needed
  // CRITICAL: Trailing slash required by FastAPI to avoid 307 redirect
  const response = await fetch(`/api/contacts/?page=1&limit=100&v=${version}&_=${timestamp}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    },
    credentials: 'same-origin',
    cache: 'no-store'  // Force no caching at fetch level
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
  
  // CRITICAL: Add cache-busting params
  // IMPORTANT: NO trailing slash for this endpoint (backend defined without slash)
  const timestamp = Date.now();
  const version = '5.2.2';
  
  const response = await fetch(`/api/contacts/merge?v=${version}&_=${timestamp}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    },
    credentials: 'same-origin',
    cache: 'no-store',
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

