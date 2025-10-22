/**
 * BlockToolbar Component
 * Панель инструментов для работы с блоками
 */

import React from 'react';

export const BlockToolbar = ({
  editMode,
  onToggleEditMode,
  onAddBlock,
  onDeleteBlock,
  onEditText,
  onSplitBlock,
  onReprocess,
  selectedBlocks,
  reprocessing,
  language = 'ru'
}) => {
  const translations = {
    en: {
      editBlocks: 'Edit Blocks',
      addBlock: 'Add Block',
      deleteBlock: 'Delete Block',
      editText: 'Edit Text',
      splitBlock: 'Split Block',
      reprocessOCR: 'Re-run OCR',
      reprocessing: 'Processing...',
      selectBlock: 'Select a block first'
    },
    ru: {
      editBlocks: 'Редактировать блоки',
      addBlock: 'Добавить блок',
      deleteBlock: 'Удалить блок',
      editText: 'Редактировать текст',
      splitBlock: 'Разбить блок',
      reprocessOCR: 'Повторить OCR',
      reprocessing: 'Обработка...',
      selectBlock: 'Выберите блок'
    }
  };

  const t = translations[language];
  const hasSelection = selectedBlocks && selectedBlocks.length > 0;

  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      padding: '10px',
      backgroundColor: '#f5f5f5',
      borderRadius: '4px',
      marginBottom: '10px',
      flexWrap: 'wrap'
    }}>
      {/* Режим редактирования */}
      <button
        onClick={onToggleEditMode}
        style={{
          padding: '8px 16px',
          backgroundColor: editMode ? '#2196f3' : '#fff',
          color: editMode ? '#fff' : '#333',
          border: '1px solid #ddd',
          borderRadius: '4px',
          cursor: 'pointer',
          fontWeight: editMode ? 'bold' : 'normal'
        }}
      >
        {t.editBlocks}
      </button>

      {/* Добавить блок */}
      {editMode && (
        <button
          onClick={onAddBlock}
          style={{
            padding: '8px 16px',
            backgroundColor: '#4caf50',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          + {t.addBlock}
        </button>
      )}

      {/* Удалить блок */}
      {editMode && (
        <button
          onClick={onDeleteBlock}
          disabled={!hasSelection}
          style={{
            padding: '8px 16px',
            backgroundColor: hasSelection ? '#f44336' : '#ccc',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: hasSelection ? 'pointer' : 'not-allowed'
          }}
          title={!hasSelection ? t.selectBlock : ''}
        >
          {t.deleteBlock}
        </button>
      )}

      {/* Редактировать текст */}
      {editMode && (
        <button
          onClick={onEditText}
          disabled={!hasSelection}
          style={{
            padding: '8px 16px',
            backgroundColor: hasSelection ? '#ff9800' : '#ccc',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: hasSelection ? 'pointer' : 'not-allowed'
          }}
          title={!hasSelection ? t.selectBlock : ''}
        >
          {t.editText}
        </button>
      )}

      {/* Разбить блок */}
      {editMode && (
        <button
          onClick={onSplitBlock}
          disabled={!hasSelection}
          style={{
            padding: '8px 16px',
            backgroundColor: hasSelection ? '#9c27b0' : '#ccc',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: hasSelection ? 'pointer' : 'not-allowed'
          }}
          title={!hasSelection ? t.selectBlock : ''}
        >
          {t.splitBlock}
        </button>
      )}

      {/* Повторить OCR */}
      <button
        onClick={onReprocess}
        disabled={reprocessing}
        style={{
          padding: '8px 16px',
          backgroundColor: reprocessing ? '#ccc' : '#2196f3',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          cursor: reprocessing ? 'not-allowed' : 'pointer',
          marginLeft: 'auto'
        }}
      >
        {reprocessing ? t.reprocessing : t.reprocessOCR}
      </button>
    </div>
  );
};

