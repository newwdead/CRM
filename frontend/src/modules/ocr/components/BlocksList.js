/**
 * BlocksList Component  
 * Список блоков с возможностью привязки к полям
 */

import React from 'react';

export const BlocksList = ({
  blocks,
  selectedBlocks,
  onBlockSelect,
  onAssignToField,
  assigningToField,
  language = 'ru'
}) => {
  const translations = {
    en: {
      ocrBlocks: 'OCR Blocks',
      clickToSelect: 'Click to select, assign to fields',
      confidence: 'Confidence',
      assignTo: 'Assigning to:',
      cancel: 'Cancel'
    },
    ru: {
      ocrBlocks: 'Блоки OCR',
      clickToSelect: 'Кликните для выбора, привязки к полям',
      confidence: 'Точность',
      assignTo: 'Привязка к:',
      cancel: 'Отмена'
    }
  };

  const t = translations[language];

  if (!blocks || !blocks.lines || blocks.lines.length === 0) {
    return null;
  }

  return (
    <div style={{
      marginTop: '20px',
      padding: '15px',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px',
      border: '1px solid #ddd'
    }}>
      <h4 style={{ marginTop: 0, marginBottom: '15px' }}>
        {t.ocrBlocks} ({blocks.lines.length})
      </h4>

      {assigningToField && (
        <div style={{
          padding: '10px',
          backgroundColor: '#e3f2fd',
          borderRadius: '4px',
          marginBottom: '10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>
            {t.assignTo} <strong>{assigningToField}</strong>
          </span>
          <button
            onClick={() => onAssignToField(null)}
            style={{
              padding: '4px 12px',
              backgroundColor: '#f44336',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {t.cancel}
          </button>
        </div>
      )}

      <div style={{
        maxHeight: '300px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        {blocks.lines.map((block, index) => {
          const isSelected = selectedBlocks && selectedBlocks.includes(index);
          
          return (
            <div
              key={index}
              onClick={() => {
                if (assigningToField) {
                  onAssignToField(assigningToField, block.text);
                } else {
                  onBlockSelect(index);
                }
              }}
              style={{
                padding: '10px',
                backgroundColor: isSelected ? '#e3f2fd' : '#fff',
                border: `2px solid ${isSelected ? '#2196f3' : '#ddd'}`,
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '5px'
              }}>
                <span style={{
                  fontSize: '12px',
                  color: '#666',
                  fontWeight: 'bold'
                }}>
                  #{index + 1}
                </span>
                <span style={{
                  fontSize: '11px',
                  color: '#999'
                }}>
                  {t.confidence}: {Math.round((block.confidence || 0) * 100)}%
                </span>
              </div>
              <div style={{
                fontSize: '14px',
                color: '#333',
                wordWrap: 'break-word'
              }}>
                {block.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

