import React, { useState, useEffect } from 'react';

/**
 * KeyboardHint Component
 * Display keyboard shortcuts hint with dismiss option
 */
const KeyboardHint = ({ shortcuts = [], className = '' }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Check if user previously dismissed
    const dismissed = localStorage.getItem('keyboardHintsDismissed');
    if (dismissed === 'true') {
      setIsVisible(false);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('keyboardHintsDismissed', 'true');
  };

  if (!isVisible) {
    return null;
  }

  if (shortcuts.length === 0) {
    shortcuts = [
      { keys: ['Ctrl', 'K'], description: 'Quick search' },
      { keys: ['Esc'], description: 'Close modals' }
    ];
  }

  return (
    <div 
      className={`keyboard-hints ${className}`}
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '12px 16px',
        borderRadius: '8px',
        fontSize: '0.875em',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        zIndex: 1000
      }}
      role="complementary"
      aria-label="Keyboard shortcuts"
    >
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '8px' 
      }}>
        <div style={{ fontWeight: 600, fontSize: '0.9em' }}>
          ⌨️ Keyboard Shortcuts
        </div>
        <button
          onClick={handleDismiss}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            padding: '0 4px',
            fontSize: '1.2em',
            lineHeight: 1,
            opacity: 0.7,
            transition: 'opacity 0.2s'
          }}
          onMouseOver={(e) => e.target.style.opacity = 1}
          onMouseOut={(e) => e.target.style.opacity = 0.7}
          aria-label="Dismiss keyboard hints"
          title="Hide keyboard shortcuts (click again in footer to show)"
        >
          ×
        </button>
      </div>
      {shortcuts.map((shortcut, idx) => (
        <div 
          key={idx}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: idx < shortcuts.length - 1 ? '6px' : 0
          }}
        >
          <div style={{ display: 'flex', gap: '4px' }}>
            {shortcut.keys.map((key, keyIdx) => (
              <kbd 
                key={keyIdx}
                style={{
                  background: '#444',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.85em',
                  fontFamily: 'monospace',
                  border: '1px solid #666'
                }}
              >
                {key}
              </kbd>
            ))}
          </div>
          <span style={{ opacity: 0.8 }}>{shortcut.description}</span>
        </div>
      ))}
    </div>
  );
};

export default KeyboardHint;

