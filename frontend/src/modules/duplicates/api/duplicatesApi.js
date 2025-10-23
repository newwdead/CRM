/**
 * Duplicates API
 * Handles all API calls for duplicate management
 */

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Fetch all duplicates
 */
export const fetchDuplicates = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/duplicates`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch duplicates');
  }

  return response.json();
};

/**
 * Fetch duplicates for a specific contact
 */
export const fetchContactDuplicates = async (contactId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/duplicates/${contactId}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch contact duplicates');
  }

  return response.json();
};

/**
 * Merge duplicate contacts
 */
export const mergeDuplicates = async (primaryId, duplicateIds) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/duplicates/merge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ primary_id: primaryId, duplicate_ids: duplicateIds })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to merge duplicates');
  }

  return response.json();
};

/**
 * Mark duplicates as reviewed
 */
export const markAsReviewed = async (duplicateId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/duplicates/${duplicateId}/reviewed`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to mark as reviewed');
  }

  return response.json();
};

/**
 * Dismiss duplicate match
 */
export const dismissDuplicate = async (duplicateId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/duplicates/${duplicateId}/dismiss`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to dismiss duplicate');
  }

  return response.json();
};

export default {
  fetchDuplicates,
  fetchContactDuplicates,
  mergeDuplicates,
  markAsReviewed,
  dismissDuplicate
};

