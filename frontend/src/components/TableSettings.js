import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

export default function TableSettings({ columns, onSave, onClose, lang = 'ru' }) {
  const [localColumns, setLocalColumns] = useState(columns);

  const t = {
    ru: {
      title: 'Настройка таблицы',
      subtitle: 'Выберите колонки для отображения и измените их порядок',
      showColumn: 'Показать',
      hideColumn: 'Скрыть',
      dragHint: 'Перетащите для изменения порядка',
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
      subtitle: 'Select columns to display and reorder them',
      showColumn: 'Show',
      hideColumn: 'Hide',
      dragHint: 'Drag to reorder',
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
  }[lang] || {};

  const handleDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(localColumns);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Update order property
    const reordered = items.map((col, index) => ({
      ...col,
      order: index
    }));

    setLocalColumns(reordered);
  };

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
        style={{ maxWidth: '600px', maxHeight: '80vh', overflow: 'auto' }}
      >
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ margin: '0 0 8px 0' }}>⚙️ {t.title}</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
            {t.subtitle}
          </p>
        </div>

        {/* Drag hint */}
        <div style={{
          padding: '12px',
          background: 'var(--info-bg)',
          border: '1px solid var(--info-color)',
          borderRadius: 'var(--radius)',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          💡 {t.dragHint}
        </div>

        {/* Columns list with drag & drop */}
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="columns">
            {(provided, snapshot) => (
              <div
                {...provided.droppableProps}
                ref={provided.innerRef}
                style={{
                  background: snapshot.isDraggingOver ? 'var(--bg-secondary)' : 'transparent',
                  borderRadius: 'var(--radius)',
                  padding: '8px',
                  minHeight: '200px'
                }}
              >
                {localColumns.map((column, index) => (
                  <Draggable key={column.key} draggableId={column.key} index={index}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        style={{
                          ...provided.draggableProps.style,
                          padding: '12px',
                          marginBottom: '8px',
                          background: snapshot.isDragging ? 'var(--primary-light)' : 'white',
                          border: `1px solid ${snapshot.isDragging ? 'var(--primary-color)' : 'var(--border-color)'}`,
                          borderRadius: 'var(--radius)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          cursor: 'grab'
                        }}
                      >
                        {/* Drag handle */}
                        <span style={{ fontSize: '20px', cursor: 'grab' }}>⋮⋮</span>

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
                          onClick={(e) => e.stopPropagation()}
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
                          onClick={(e) => e.stopPropagation()}
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
                            onClick={(e) => e.stopPropagation()}
                          />
                          {column.visible ? '👁️' : '👁️‍🗨️'}
                        </label>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>

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

