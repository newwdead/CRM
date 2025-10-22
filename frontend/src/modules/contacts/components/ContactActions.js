/**
 * ContactActions Component
 * Панель действий с контактами (массовые операции, экспорт)
 */

import React from 'react';

export const ContactActions = ({
  selectedCount,
  onBulkEdit,
  onBulkDelete,
  onExport,
  onRefresh,
  language = 'ru'
}) => {
  const translations = {
    en: {
      selected: 'Selected: {count}',
      bulkEdit: 'Bulk Edit',
      bulkDelete: 'Bulk Delete',
      export: 'Export',
      refresh: 'Refresh'
    },
    ru: {
      selected: 'Выбрано: {count}',
      bulkEdit: 'Массовое редактирование',
      bulkDelete: 'Массовое удаление',
      export: 'Экспорт',
      refresh: 'Обновить'
    }
  };

  const t = translations[language];

  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      marginBottom: '20px',
      alignItems: 'center',
      flexWrap: 'wrap'
    }}>
      {/* Selection count */}
      {selectedCount > 0 && (
        <span style={{
          padding: '8px 12px',
          backgroundColor: '#e3f2fd',
          borderRadius: '4px',
          fontSize: '14px',
          fontWeight: 'bold'
        }}>
          {t.selected.replace('{count}', selectedCount)}
        </span>
      )}

      {/* Bulk Actions */}
      {selectedCount > 0 && (
        <>
          <button
            onClick={onBulkEdit}
            style={{
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {t.bulkEdit}
          </button>
          <button
            onClick={onBulkDelete}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {t.bulkDelete}
          </button>
        </>
      )}

      {/* Export Button */}
      <button
        onClick={onExport}
        style={{
          padding: '8px 16px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          marginLeft: selectedCount > 0 ? '10px' : '0'
        }}
      >
        {t.export}
      </button>

      {/* Refresh Button */}
      <button
        onClick={onRefresh}
        style={{
          padding: '8px 16px',
          backgroundColor: '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          marginLeft: 'auto'
        }}
      >
        {t.refresh}
      </button>
    </div>
  );
};

