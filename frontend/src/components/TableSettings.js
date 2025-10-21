import React, { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

export default function TableSettings({ columns, onSave, onClose, lang = 'ru' }) {
  const [localColumns, setLocalColumns] = useState(columns);

  const t = {
    ru: {
      title: 'Настройка таблицы',
      subtitle: 'Выберите колонки для отображения',
      showColumn: 'Показать',
      hideColumn: 'Скрыть',
      save: 'Сохранить',
      cancel: 'Отмена',
      reset: 'Сбросить',
      resetConfirm: 'Сбросить настройки таблицы?',
      saved: 'Настройки сохранены!',
      column: 'Колонка',
      visible: 'Видимость',
      order: 'Порядок',
      width: 'Ширина',
      auto: 'Авто',
      px: 'px',
    },
    en: {
      title: 'Table Settings',
      subtitle: 'Select columns to display',
      showColumn: 'Show',
      hideColumn: 'Hide',
      save: 'Save',
      cancel: 'Cancel',
      reset: 'Reset',
      resetConfirm: 'Reset table settings?',
      saved: 'Settings saved!',
      column: 'Column',
      visible: 'Visibility',
      order: 'Order',
      width: 'Width',
      auto: 'Auto',
      px: 'px',
    }
  }[lang] || t.ru;

  const toggleVisibility = (key) => {
    setLocalColumns(localColumns.map(col => 
      col.key === key ? { ...col, visible: !col.visible } : col
    ));
  };

  const handleWidthChange = (key, width) => {
    setLocalColumns(localColumns.map(col => 
      col.key === key ? { ...col, width: width || 'auto' } : col
    ));
  };

  const moveUp = (index) => {
    if (index === 0) return;
    const items = [...localColumns];
    [items[index - 1], items[index]] = [items[index], items[index - 1]];
    const reordered = items.map((col, idx) => ({ ...col, order: idx }));
    setLocalColumns(reordered);
  };

  const moveDown = (index) => {
    if (index === localColumns.length - 1) return;
    const items = [...localColumns];
    [items[index], items[index + 1]] = [items[index + 1], items[index]];
    const reordered = items.map((col, idx) => ({ ...col, order: idx }));
    setLocalColumns(reordered);
  };

  const handleSave = () => {
    onSave(localColumns);
    toast.success(t.saved, { icon: '✅', duration: 2000 });
    onClose();
  };

  const handleReset = () => {
    if (window.confirm(t.resetConfirm)) {
      // Reset to default
      const defaultColumns = columns.map((col, index) => ({
        ...col,
        visible: true,
        order: index,
        width: 'auto'
      }));
      setLocalColumns(defaultColumns);
      onSave(defaultColumns);
      toast.success(t.saved, { icon: '🔄', duration: 2000 });
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="modal table-settings-modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '650px', maxHeight: '80vh', overflow: 'auto' }}
      >
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ margin: '0 0 8px 0' }}>⚙️ {t.title}</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
            {t.subtitle}
          </p>
        </div>

        {/* Columns list */}
        <div style={{
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius)',
          padding: '8px',
          minHeight: '200px'
        }}>
          {localColumns.map((column, index) => (
            <div
              key={column.key}
              style={{
                padding: '12px',
                marginBottom: '8px',
                background: 'white',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}
            >
              {/* Order controls */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <button
                  onClick={() => moveUp(index)}
                  disabled={index === 0}
                  style={{
                    padding: '2px 6px',
                    fontSize: '12px',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    background: 'white',
                    cursor: index === 0 ? 'not-allowed' : 'pointer',
                    opacity: index === 0 ? 0.3 : 1
                  }}
                  title="Вверх"
                >
                  ▲
                </button>
                <button
                  onClick={() => moveDown(index)}
                  disabled={index === localColumns.length - 1}
                  style={{
                    padding: '2px 6px',
                    fontSize: '12px',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    background: 'white',
                    cursor: index === localColumns.length - 1 ? 'not-allowed' : 'pointer',
                    opacity: index === localColumns.length - 1 ? 0.3 : 1
                  }}
                  title="Вниз"
                >
                  ▼
                </button>
              </div>

              {/* Order number */}
              <span style={{
                minWidth: '30px',
                height: '30px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'var(--bg-secondary)',
                borderRadius: '50%',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {index + 1}
              </span>

              {/* Column info */}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                  {column.label}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {t.width}: {column.width === 'auto' ? t.auto : `${column.width}${t.px}`}
                </div>
              </div>

              {/* Width input */}
              <input
                type="number"
                placeholder={t.auto}
                value={column.width === 'auto' ? '' : column.width}
                onChange={(e) => handleWidthChange(column.key, e.target.value)}
                style={{
                  width: '80px',
                  padding: '6px',
                  fontSize: '12px',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius)'
                }}
              />

              {/* Visibility toggle */}
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  padding: '6px 12px',
                  background: column.visible ? 'var(--success-bg)' : 'var(--bg-secondary)',
                  borderRadius: 'var(--radius)',
                  fontSize: '12px',
                  fontWeight: 500,
                  color: column.visible ? 'var(--success-color)' : 'var(--text-secondary)'
                }}
              >
                <input
                  type="checkbox"
                  checked={column.visible}
                  onChange={() => toggleVisibility(column.key)}
                />
                {column.visible ? '👁️' : '👁️‍🗨️'}
              </label>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginTop: '24px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-color)'
        }}>
          <button
            onClick={handleReset}
            className="secondary"
            style={{ flex: 1 }}
          >
            🔄 {t.reset}
          </button>
          <button
            onClick={onClose}
            className="secondary"
            style={{ flex: 1 }}
          >
            ❌ {t.cancel}
          </button>
          <button
            onClick={handleSave}
            style={{ flex: 1 }}
          >
            ✅ {t.save}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
