/**
 * Settings API Module
 * API вызовы для настроек интеграций
 */

const API_BASE = '/api';

export const getIntegrationsStatus = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/settings/integrations/status`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch integrations');
  return await response.json();
};

export const toggleIntegration = async (integrationId, enabled) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/settings/integrations/${integrationId}/toggle`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ enabled })
  });
  if (!response.ok) throw new Error('Failed to toggle integration');
  return await response.json();
};

export const testIntegration = async (integrationId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/settings/integrations/${integrationId}/test`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to test integration');
  return await response.json();
};

export const updateIntegrationConfig = async (integrationId, config) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/settings/integrations/${integrationId}/config`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(config)
  });
  if (!response.ok) throw new Error('Failed to update config');
  return await response.json();
};

