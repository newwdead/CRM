/**
 * Token Manager - Handles JWT token storage, refresh, and auto-renewal
 * 
 * Features:
 * - Stores access and refresh tokens in localStorage
 * - Auto-refreshes access token before expiration
 * - Handles token rotation
 * - Provides token validation utilities
 */

const TOKEN_KEYS = {
  ACCESS: 'access_token',
  REFRESH: 'refresh_token',
  EXPIRES_AT: 'token_expires_at',
};

// Refresh token 2 minutes before expiration
const REFRESH_BUFFER_MS = 2 * 60 * 1000;

let refreshTimer = null;

/**
 * Store authentication tokens
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token
 * @param {number} expiresIn - Expiration time in seconds
 */
export function setTokens(accessToken, refreshToken, expiresIn) {
  localStorage.setItem(TOKEN_KEYS.ACCESS, accessToken);
  localStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken);
  
  // Calculate expiration timestamp
  const expiresAt = Date.now() + (expiresIn * 1000);
  localStorage.setItem(TOKEN_KEYS.EXPIRES_AT, expiresAt.toString());
  
  // Schedule auto-refresh
  scheduleTokenRefresh(expiresIn);
}

/**
 * Get stored access token
 * @returns {string|null} Access token or null if not found
 */
export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEYS.ACCESS);
}

/**
 * Get stored refresh token
 * @returns {string|null} Refresh token or null if not found
 */
export function getRefreshToken() {
  return localStorage.getItem(TOKEN_KEYS.REFRESH);
}

/**
 * Check if access token is expired or will expire soon
 * @returns {boolean} True if token needs refresh
 */
export function needsRefresh() {
  const expiresAt = localStorage.getItem(TOKEN_KEYS.EXPIRES_AT);
  if (!expiresAt) return true;
  
  const timeUntilExpiry = parseInt(expiresAt) - Date.now();
  return timeUntilExpiry <= REFRESH_BUFFER_MS;
}

/**
 * Clear all stored tokens
 */
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEYS.ACCESS);
  localStorage.removeItem(TOKEN_KEYS.REFRESH);
  localStorage.removeItem(TOKEN_KEYS.EXPIRES_AT);
  localStorage.removeItem('user');
  
  // Cancel auto-refresh timer
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

/**
 * Refresh access token using refresh token
 * @returns {Promise<boolean>} True if refresh successful
 */
export async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    console.warn('No refresh token available');
    return false;
  }
  
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (!response.ok) {
      console.error('Token refresh failed:', response.status);
      
      // If refresh fails with 401, clear tokens and redirect to login
      if (response.status === 401) {
        clearTokens();
        window.location.href = '/login';
      }
      
      return false;
    }
    
    const data = await response.json();
    
    // Store new tokens
    setTokens(data.access_token, data.refresh_token, data.expires_in);
    
    console.log('Access token refreshed successfully');
    return true;
  } catch (error) {
    console.error('Error refreshing token:', error);
    return false;
  }
}

/**
 * Schedule automatic token refresh
 * @param {number} expiresIn - Token expiration in seconds
 */
function scheduleTokenRefresh(expiresIn) {
  // Cancel existing timer
  if (refreshTimer) {
    clearTimeout(refreshTimer);
  }
  
  // Schedule refresh 2 minutes before expiration
  const refreshDelay = (expiresIn * 1000) - REFRESH_BUFFER_MS;
  
  if (refreshDelay > 0) {
    refreshTimer = setTimeout(async () => {
      console.log('Auto-refreshing access token...');
      await refreshAccessToken();
    }, refreshDelay);
    
    console.log(`Token auto-refresh scheduled in ${Math.round(refreshDelay / 1000 / 60)} minutes`);
  } else {
    // Token expires very soon, refresh immediately
    refreshAccessToken();
  }
}

/**
 * Initialize token manager (call on app startup)
 * Checks if existing token needs refresh
 */
export function initTokenManager() {
  const accessToken = getAccessToken();
  const refreshToken = getRefreshToken();
  const expiresAt = localStorage.getItem(TOKEN_KEYS.EXPIRES_AT);
  
  if (!accessToken || !refreshToken) {
    return; // No tokens stored
  }
  
  if (needsRefresh()) {
    // Token expired or expiring soon, refresh immediately
    refreshAccessToken();
  } else if (expiresAt) {
    // Schedule next refresh
    const timeUntilExpiry = parseInt(expiresAt) - Date.now();
    const expiresIn = Math.floor(timeUntilExpiry / 1000);
    scheduleTokenRefresh(expiresIn);
  }
}

/**
 * Create Authorization header with access token
 * @returns {Object} Headers object with Authorization
 */
export function getAuthHeaders() {
  const token = getAccessToken();
  if (!token) return {};
  
  return {
    'Authorization': `Bearer ${token}`,
  };
}

/**
 * Make authenticated API request with auto-refresh
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function authenticatedFetch(url, options = {}) {
  // Check if token needs refresh before making request
  if (needsRefresh()) {
    await refreshAccessToken();
  }
  
  // Add auth headers
  const headers = {
    ...options.headers,
    ...getAuthHeaders(),
  };
  
  // Make request
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // If 401, try refreshing token once
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    
    if (refreshed) {
      // Retry request with new token
      const retryHeaders = {
        ...options.headers,
        ...getAuthHeaders(),
      };
      
      return fetch(url, {
        ...options,
        headers: retryHeaders,
      });
    } else {
      // Refresh failed, redirect to login
      clearTokens();
      window.location.href = '/login';
    }
  }
  
  return response;
}

// Export all functions
export default {
  setTokens,
  getAccessToken,
  getRefreshToken,
  needsRefresh,
  clearTokens,
  refreshAccessToken,
  initTokenManager,
  getAuthHeaders,
  authenticatedFetch,
};

