import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { getAccessToken } from '../../utils/tokenManager';

/**
 * Protected Route Component
 * Redirects to login if not authenticated
 * Redirects to home if user doesn't have required role
 */
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const location = useLocation();
  // Check both new and old token storage for backward compatibility
  const token = getAccessToken() || localStorage.getItem('token');
  const userStr = localStorage.getItem('user');

  // Not authenticated - redirect to login
  if (!token || !userStr) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin requirement
  if (requireAdmin) {
    try {
      const user = JSON.parse(userStr);
      if (!user.is_admin) {
        return <Navigate to="/" replace />;
      }
    } catch (error) {
      return <Navigate to="/login" replace />;
    }
  }

  return children;
};

export default ProtectedRoute;

