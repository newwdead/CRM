import React, { useState, useEffect } from 'react';

/**
 * Block Text Editor Modal
 * 
 * Modal dialog for editing text content of a block
 * 
 * @param {object} props - Component props
 * @param {object} props.block - Block being edited (with .text property)
 * @param {function} props.onSave - Save handler (newText) => void
 * @param {function} props.onCancel - Cancel handler () => void
 * @param {object} props.translations - Translation object
 */
const BlockTextEditor = ({ block, onSave, onCancel, translations }) => {
  const [text, setText] = useState('');
  const t = translations || {};

  // Initialize text when block changes
  useEffect(() => {
    if (block && block.text) {
      setText(block.text);
    }
  }, [block]);

  if (!block) return null;

  const handleSave = () => {
    if (onSave) {
      onSave(text);
    }
  };

  const handleKeyDown = (e) => {
    // Save on Ctrl+Enter
    if (e.ctrlKey && e.key === 'Enter') {
      handleSave();
    }
    // Cancel on Escape
    if (e.key === 'Escape') {
      if (onCancel) onCancel();
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}
        onClick={onCancel}
      />

      {/* Modal */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
          width: '90%',
          maxWidth: '500px',
          zIndex: 10000,
          padding: '24px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
            📝 {t.editText || 'Edit Block Text'}
          </h3>
          <button
            onClick={onCancel}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              color: '#64748b',
              lineHeight: 1
            }}
            title="Close"
          >
            ×
          </button>
        </div>

        {/* Confidence indicator */}
        {block.confidence !== undefined && (
          <div style={{
            marginBottom: '12px',
            padding: '8px',
            backgroundColor: '#f0f9ff',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#1e40af'
          }}>
            🎯 Confidence: {Math.round(block.confidence)}%
          </div>
        )}

        {/* Textarea */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          style={{
            width: '100%',
            minHeight: '120px',
            padding: '12px',
            fontSize: '14px',
            border: '2px solid #e2e8f0',
            borderRadius: '6px',
            fontFamily: 'inherit',
            resize: 'vertical',
            outline: 'none',
            marginBottom: '16px'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#3b82f6';
            e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e2e8f0';
            e.target.style.boxShadow = 'none';
          }}
          placeholder={t.editText || 'Enter text...'}
        />

        {/* Character count */}
        <div style={{
          fontSize: '12px',
          color: '#64748b',
          marginBottom: '16px',
          textAlign: 'right'
        }}>
          {text.length} characters
        </div>

        {/* Buttons */}
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '600',
              border: '2px solid #e2e8f0',
              backgroundColor: '#fff',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f8fafc';
              e.target.style.borderColor = '#cbd5e1';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#fff';
              e.target.style.borderColor = '#e2e8f0';
            }}
          >
            {t.cancelEdit || t.cancel || 'Cancel'}
          </button>

          <button
            onClick={handleSave}
            disabled={!text.trim()}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '600',
              border: 'none',
              backgroundColor: text.trim() ? '#3b82f6' : '#cbd5e1',
              color: '#fff',
              borderRadius: '6px',
              cursor: text.trim() ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              if (text.trim()) {
                e.target.style.backgroundColor = '#2563eb';
              }
            }}
            onMouseLeave={(e) => {
              if (text.trim()) {
                e.target.style.backgroundColor = '#3b82f6';
              }
            }}
          >
            {t.saveText || t.save || 'Save'}
          </button>
        </div>

        {/* Hint */}
        <div style={{
          marginTop: '12px',
          fontSize: '11px',
          color: '#94a3b8',
          textAlign: 'center'
        }}>
          💡 Tip: Press Ctrl+Enter to save, Esc to cancel
        </div>
      </div>
    </>
  );
};

export default BlockTextEditor;

