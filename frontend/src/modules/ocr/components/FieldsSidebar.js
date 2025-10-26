import React from 'react';
import { editableFields, fieldColors } from '../constants/fieldConfig';

/**
 * Fields Sidebar Component
 * 
 * Displays editable contact fields with quick assign buttons
 * 
 * @param {object} props - Component props
 * @param {object} props.editedData - Current field values
 * @param {function} props.onFieldChange - Field change handler (field, value) => void
 * @param {array} props.selectedBlocks - Currently selected blocks
 * @param {function} props.onQuickAssign - Quick assign handler (field) => void
 * @param {boolean} props.saving - Whether data is being saved
 * @param {function} props.onSave - Save handler () => void
 * @param {function} props.onCancel - Cancel handler () => void
 * @param {function} props.onReset - Reset handler () => void
 * @param {object} props.translations - Translation object
 */
const FieldsSidebar = ({
  editedData = {},
  onFieldChange,
  selectedBlocks = [],
  onQuickAssign,
  saving,
  onSave,
  onCancel,
  onReset,
  translations
}) => {
  const t = translations || {};

  // Fields that should span 2 columns
  const wideFields = ['address', 'address_additional', 'comment', 'website'];

  return (
    <div style={{
      width: '350px',
      backgroundColor: '#f8fafc',
      borderRadius: '8px',
      padding: '20px',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '20px',
        paddingBottom: '15px',
        borderBottom: '2px solid #e2e8f0'
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '16px',
          fontWeight: '600',
          color: '#1e293b'
        }}>
          📝 {t.fields?.title || 'Contact Fields'}
        </h3>
        {selectedBlocks.length > 0 && (
          <p style={{
            margin: '8px 0 0 0',
            fontSize: '12px',
            color: '#64748b'
          }}>
            💡 {t.multiSelectHint || 'Click field buttons to assign selected blocks'}
          </p>
        )}
      </div>

      {/* Fields grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px',
        marginBottom: '20px',
        flex: 1
      }}>
        {editableFields.map(field => (
          <div
            key={field}
            style={{
              gridColumn: wideFields.includes(field) ? 'span 2' : 'span 1'
            }}
          >
            {/* Label with color indicator */}
            <label style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '6px',
              fontSize: '13px',
              fontWeight: '600',
              color: '#4a5568'
            }}>
              <span style={{
                width: '12px',
                height: '12px',
                backgroundColor: fieldColors[field] || '#64748b',
                borderRadius: '3px',
                marginRight: '8px',
                flexShrink: 0
              }} />
              {t.fields?.[field] || field}
            </label>

            {/* Input with quick assign button */}
            <div style={{ position: 'relative' }}>
              <input
                type={field === 'email' ? 'email' : 'text'}
                value={editedData[field] || ''}
                onChange={(e) => onFieldChange && onFieldChange(field, e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  paddingRight: selectedBlocks.length > 0 ? '50px' : '10px',
                  fontSize: '14px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  transition: 'all 0.2s',
                  outline: 'none',
                  backgroundColor: '#fff',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = fieldColors[field] || '#3b82f6';
                  e.target.style.boxShadow = `0 0 0 3px ${fieldColors[field] || '#3b82f6'}20`;
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e2e8f0';
                  e.target.style.boxShadow = 'none';
                }}
                placeholder={t.fields?.[field] || field}
              />

              {/* Quick assign button (shown when blocks selected) */}
              {selectedBlocks.length > 0 && onQuickAssign && (
                <button
                  onClick={() => onQuickAssign(field)}
                  title={`Assign ${selectedBlocks.length} block(s) to ${field}`}
                  style={{
                    position: 'absolute',
                    right: '5px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    padding: '5px 10px',
                    fontSize: '11px',
                    backgroundColor: fieldColors[field] || '#3b82f6',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-50%) scale(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(-50%) scale(1)';
                  }}
                >
                  ← {selectedBlocks.length > 1 && `(${selectedBlocks.length})`}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div style={{
        display: 'flex',
        gap: '10px',
        paddingTop: '20px',
        borderTop: '2px solid #e2e8f0'
      }}>
        {/* Save button */}
        <button
          onClick={onSave}
          disabled={saving}
          style={{
            flex: 1,
            padding: '12px',
            fontSize: '14px',
            fontWeight: '600',
            border: 'none',
            backgroundColor: saving ? '#cbd5e1' : '#10b981',
            color: '#fff',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#059669';
            }
          }}
          onMouseLeave={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#10b981';
            }
          }}
        >
          {saving 
            ? '⏳ ' + (t.messages?.saving || 'Saving...') 
            : '💾 ' + (t.buttons?.save || 'Save Changes')}
        </button>

        {/* Cancel button */}
        <button
          onClick={onCancel}
          disabled={saving}
          style={{
            padding: '12px 20px',
            fontSize: '14px',
            fontWeight: '600',
            border: '2px solid #e2e8f0',
            backgroundColor: '#fff',
            color: '#64748b',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            opacity: saving ? 0.5 : 1
          }}
          onMouseEnter={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#f8fafc';
              e.target.style.borderColor = '#cbd5e1';
            }
          }}
          onMouseLeave={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#fff';
              e.target.style.borderColor = '#e2e8f0';
            }
          }}
        >
          {t.buttons?.cancel || 'Cancel'}
        </button>
      </div>

      {/* Reset button (optional) */}
      {onReset && (
        <button
          onClick={onReset}
          disabled={saving}
          style={{
            marginTop: '10px',
            padding: '8px',
            fontSize: '12px',
            fontWeight: '600',
            border: '1px solid #e2e8f0',
            backgroundColor: '#fff',
            color: '#94a3b8',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            opacity: saving ? 0.5 : 1
          }}
          onMouseEnter={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#fef2f2';
              e.target.style.borderColor = '#fecaca';
              e.target.style.color = '#ef4444';
            }
          }}
          onMouseLeave={(e) => {
            if (!saving) {
              e.target.style.backgroundColor = '#fff';
              e.target.style.borderColor = '#e2e8f0';
              e.target.style.color = '#94a3b8';
            }
          }}
        >
          🔄 {t.buttons?.reset || 'Reset'}
        </button>
      )}
    </div>
  );
};

export default FieldsSidebar;

