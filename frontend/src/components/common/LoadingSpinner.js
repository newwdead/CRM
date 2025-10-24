import React from 'react';
import PropTypes from 'prop-types';

/**
 * Shared Loading Spinner Component
 * Consistent loading indicator across the app
 * 
 * @param {object} props - Component props
 * @param {string} props.size - Spinner size
 * @param {string} props.message - Optional loading message
 */
const LoadingSpinner = ({ size = 'medium', message = '' }) => {
  const sizeStyles = {
    small: { width: '16px', height: '16px' },
    medium: { width: '32px', height: '32px' },
    large: { width: '48px', height: '48px' }
  };

  const style = sizeStyles[size] || sizeStyles.medium;

  return (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <div 
        className="modern-spinner" 
        style={style}
      ></div>
      {message && (
        <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>
          {message}
        </p>
      )}
    </div>
  );
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  message: PropTypes.string
};

export default LoadingSpinner;

