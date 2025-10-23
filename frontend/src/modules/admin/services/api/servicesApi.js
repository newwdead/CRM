/**
 * Services API Module
 * Все API вызовы для управления сервисами Docker
 */

const API_BASE = '/api';

/**
 * Получить статус всех сервисов
 */
export const getServicesStatus = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/services/status`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch services' }));
    throw new Error(error.detail || 'Failed to fetch services');
  }
  
  return await response.json();
};

/**
 * Перезапустить сервис
 */
export const restartService = async (serviceName) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/services/${serviceName}/restart`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to restart service' }));
    throw new Error(error.detail || 'Failed to restart service');
  }
  
  return await response.json();
};

/**
 * Получить логи сервиса
 */
export const getServiceLogs = async (serviceName, lines = 50) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/services/${serviceName}/logs?lines=${lines}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch logs' }));
    throw new Error(error.detail || 'Failed to fetch logs');
  }
  
  return await response.json();
};

