import React from 'react';
import { editableFields, fieldColors } from '../constants/fieldConfig';

/**
 * Assignment Panel Component
 * 
 * Panel for assigning selected blocks to contact fields
 * Shows selected blocks preview and field list
 * 
 * @param {object} props - Component props
 * @param {array} props.selectedBlocks - Currently selected blocks
 * @param {function} props.onAssign - Assign handler (fieldName) => void
 * @param {function} props.onCancel - Cancel handler () => void
 * @param {function} props.onClearSelection - Clear selection handler () => void
 * @param {object} props.translations - Translation object
 */
const AssignmentPanel = ({
  selectedBlocks = [],
  onAssign,
  onCancel,
  onClearSelection,
  translations
}) => {
  const t = translations || {};

  if (selectedBlocks.length === 0) return null;

  // Calculate combined text preview
  const combinedText = selectedBlocks.map(b => b.text).join(' ');
  const previewText = combinedText.length > 100 
    ? combinedText.substring(0, 100) + '...' 
    : combinedText;

  // Average confidence
  const avgConfidence = selectedBlocks.reduce((sum, b) => sum + (b.confidence || 0), 0) / selectedBlocks.length;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#fff',
        borderRadius: '12px',
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
        padding: '20px',
        minWidth: '400px',
        maxWidth: '90%',
        zIndex: 9000,
        border: '2px solid #3b82f6'
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
          📋 {t.assignTo || 'Assign to field'}
        </h4>
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

      {/* Selected blocks info */}
      <div style={{
        padding: '12px',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        marginBottom: '16px',
        border: '1px solid #bfdbfe'
      }}>
        <div style={{
          fontSize: '12px',
          color: '#1e40af',
          marginBottom: '8px',
          fontWeight: '600'
        }}>
          {t.selectedBlocks || 'Selected blocks'}: {selectedBlocks.length}
          {avgConfidence > 0 && ` • Confidence: ${Math.round(avgConfidence)}%`}
        </div>
        <div style={{
          fontSize: '14px',
          color: '#1e293b',
          fontStyle: 'italic',
          wordBreak: 'break-word'
        }}>
          "{previewText}"
        </div>
      </div>

      {/* Field selection grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '8px',
        marginBottom: '16px',
        maxHeight: '200px',
        overflowY: 'auto',
        padding: '4px'
      }}>
        {editableFields.map(field => (
          <button
            key={field}
            onClick={() => onAssign && onAssign(field)}
            style={{
              padding: '10px 12px',
              fontSize: '13px',
              fontWeight: '600',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              backgroundColor: fieldColors[field] || '#64748b',
              color: '#fff',
              transition: 'all 0.2s',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'scale(1.05)';
              e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = 'none';
            }}
            title={`Assign to ${t.fields?.[field] || field}`}
          >
            {t.fields?.[field] || field}
          </button>
        ))}
      </div>

      {/* Action buttons */}
      <div style={{
        display: 'flex',
        gap: '10px',
        paddingTop: '12px',
        borderTop: '1px solid #e2e8f0'
      }}>
        <button
          onClick={onClearSelection}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '13px',
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
          🗑️ {t.clearSelection || 'Clear Selection'}
        </button>

        <button
          onClick={onCancel}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '13px',
            fontWeight: '600',
            border: 'none',
            backgroundColor: '#64748b',
            color: '#fff',
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = '#475569';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = '#64748b';
          }}
        >
          {t.cancelAssignment || t.cancel || 'Cancel'}
        </button>
      </div>

      {/* Hint */}
      <div style={{
        marginTop: '12px',
        fontSize: '11px',
        color: '#94a3b8',
        textAlign: 'center'
      }}>
        💡 {t.multiSelectHint || 'Hold Ctrl to select multiple blocks'}
      </div>
    </div>
  );
};

export default AssignmentPanel;

