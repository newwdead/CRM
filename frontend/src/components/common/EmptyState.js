import React from 'react';

/**
 * EmptyState Component
 * Reusable empty state for lists and collections
 */
const EmptyState = ({ 
  icon = '📭', 
  title = 'No data', 
  description = '', 
  action = null,
  className = ''
}) => {
  return (
    <div 
      className={`empty-state ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        textAlign: 'center',
        color: '#666'
      }}
      role="status"
      aria-live="polite"
    >
      <div style={{ fontSize: '4em', marginBottom: '20px', opacity: 0.5 }}>
        {icon}
      </div>
      <h3 style={{ 
        fontSize: '1.5em', 
        fontWeight: 600, 
        margin: '0 0 10px 0',
        color: '#333'
      }}>
        {title}
      </h3>
      {description && (
        <p style={{ 
          fontSize: '1em', 
          margin: '0 0 30px 0',
          maxWidth: '400px',
          color: '#666'
        }}>
          {description}
        </p>
      )}
      {action && (
        <div>
          {action}
        </div>
      )}
    </div>
  );
};

export default EmptyState;

