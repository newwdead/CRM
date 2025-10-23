/**
 * OCREditorContainer Component
 * Главный контейнер OCR Editor - объединяет все компоненты и хуки
 * 
 * Было: 1 файл × 1150 строк (монолит)
 * Стало: Модульная архитектура с изолированной логикой
 */

import React, { useState, useRef } from 'react';
import { useOCRBlocks } from '../hooks/useOCRBlocks';
import { useBlockDrag } from '../hooks/useBlockDrag';
import { useBlockResize } from '../hooks/useBlockResize';
import { ImageViewer } from './ImageViewer';
import { BlockCanvas } from './BlockCanvas';
import { BlockToolbar } from './BlockToolbar';
import { BlocksList } from './BlocksList';

export const OCREditorContainer = ({ contact, onSave, onClose }) => {
  const [editedData, setEditedData] = useState({});
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [assigningToField, setAssigningToField] = useState(null);
  const [editBlockMode, setEditBlockMode] = useState(false);
  const [editingBlockText, setEditingBlockText] = useState(null);
  const [isAddingBlock, setIsAddingBlock] = useState(false);
  const [newBlockStart, setNewBlockStart] = useState(null);
  
  const imageRef = useRef(null);
  const language = localStorage.getItem('language') || 'ru';

  // Используем хуки
  const {
    blocks,
    loading,
    reprocessing,
    imageScale,
    setImageScale,
    updateBlock,
    deleteBlock,
    addBlock,
    updateBlockText,
    splitBlock,
    handleReprocess
  } = useOCRBlocks(contact, language);

  const {
    draggingBlock,
    handleDragStart,
    handleDrag,
    handleDragEnd
  } = useBlockDrag(blocks, updateBlock, imageScale);

  const {
    resizingBlock,
    handleResizeStart,
    handleResize,
    handleResizeEnd
  } = useBlockResize(blocks, updateBlock, imageScale);

  // Обработчики событий мыши для canvas
  React.useEffect(() => {
    if (editBlockMode) {
      const handleMouseMove = (e) => {
        handleDrag(e);
        handleResize(e);
      };

      const handleMouseUp = () => {
        handleDragEnd();
        handleResizeEnd();
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [editBlockMode, handleDrag, handleResize, handleDragEnd, handleResizeEnd]);

  // Обработчики для toolbar
  const handleToggleEditMode = () => {
    setEditBlockMode(!editBlockMode);
    setSelectedBlocks([]);
  };

  const handleAddBlockClick = () => {
    setIsAddingBlock(true);
  };

  const handleDeleteBlock = () => {
    if (selectedBlocks.length > 0) {
      selectedBlocks.sort((a, b) => b - a).forEach(index => {
        deleteBlock(index);
      });
      setSelectedBlocks([]);
    }
  };

  const handleEditText = () => {
    if (selectedBlocks.length > 0) {
      setEditingBlockText(selectedBlocks[0]);
    }
  };

  const handleSplitBlock = () => {
    if (selectedBlocks.length > 0) {
      splitBlock(selectedBlocks[0]);
      setSelectedBlocks([]);
    }
  };

  const handleReprocessClick = async () => {
    await handleReprocess((result) => {
      // Обновляем данные контакта после reprocess
      setEditedData(prev => ({
        ...prev,
        ...result
      }));
    });
  };

  // Обработчики для image viewer (добавление блока)
  const handleImageMouseDown = (event) => {
    if (!isAddingBlock) return;
    
    const container = imageRef.current;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    const x = (event.clientX - rect.left) / imageScale;
    const y = (event.clientY - rect.top) / imageScale;
    
    setNewBlockStart({ x, y });
  };

  const handleImageMouseUp = (event) => {
    if (!isAddingBlock || !newBlockStart) return;
    
    const container = imageRef.current;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    const x = (event.clientX - rect.left) / imageScale;
    const y = (event.clientY - rect.top) / imageScale;
    
    const width = Math.abs(x - newBlockStart.x);
    const height = Math.abs(y - newBlockStart.y);
    
    if (width < 20 || height < 10) {
      setIsAddingBlock(false);
      setNewBlockStart(null);
      return;
    }
    
    const newBlock = {
      text: language === 'ru' ? 'Новый текст' : 'New text',
      box: {
        x: Math.min(newBlockStart.x, x),
        y: Math.min(newBlockStart.y, y),
        width: width,
        height: height
      },
      confidence: 0
    };
    
    addBlock(newBlock);
    setIsAddingBlock(false);
    setNewBlockStart(null);
  };

  // Обработчики для блоков
  const handleBlockClick = (index) => {
    if (editBlockMode) {
      setSelectedBlocks([index]);
    } else {
      // Toggle selection
      setSelectedBlocks(prev =>
        prev.includes(index)
          ? prev.filter(i => i !== index)
          : [...prev, index]
      );
    }
  };

  const handleBlockSelect = (index) => {
    handleBlockClick(index);
  };

  const handleAssignToField = (field, text) => {
    if (field && text) {
      setEditedData(prev => ({
        ...prev,
        [field]: text
      }));
      setAssigningToField(null);
    } else {
      setAssigningToField(field);
    }
  };

  // Сохранение изменений
  const handleSave = () => {
    if (onSave) {
      onSave(editedData);
    }
  };

  // Translations
  const translations = {
    en: {
      title: 'OCR Editor with Blocks',
      loading: 'Loading OCR data...',
      save: 'Save',
      cancel: 'Cancel'
    },
    ru: {
      title: 'Редактор OCR с блоками',
      loading: 'Загрузка данных OCR...',
      save: 'Сохранить',
      cancel: 'Отмена'
    }
  };

  const t = translations[language];

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>{t.loading}</p>
      </div>
    );
  }

  // Contact model uses photo_path, not image_url or card_image
  // photo_path is relative to uploads/ directory, backend mounts it at /files/
  const imageUrl = contact.photo_path 
    ? `/files/${contact.photo_path}` 
    : contact.thumbnail_path 
    ? `/files/${contact.thumbnail_path}` 
    : null;

  return (
    <div style={{
      padding: '20px',
      maxWidth: '100%',
      width: '100%',
      margin: '0 auto'
    }}>
      <h2>{t.title}</h2>

      {/* Toolbar */}
      <BlockToolbar
        editMode={editBlockMode}
        onToggleEditMode={handleToggleEditMode}
        onAddBlock={handleAddBlockClick}
        onDeleteBlock={handleDeleteBlock}
        onEditText={handleEditText}
        onSplitBlock={handleSplitBlock}
        onReprocess={handleReprocessClick}
        selectedBlocks={selectedBlocks}
        reprocessing={reprocessing}
        language={language}
      />

      {/* Image with blocks */}
      <ImageViewer
        imageUrl={imageUrl}
        imageScale={imageScale}
        onScaleChange={setImageScale}
        onMouseDown={handleImageMouseDown}
        onMouseUp={handleImageMouseUp}
      >
        <BlockCanvas
          blocks={blocks}
          imageScale={imageScale}
          selectedBlocks={selectedBlocks}
          editMode={editBlockMode}
          draggingBlock={draggingBlock}
          resizingBlock={resizingBlock}
          onBlockClick={handleBlockClick}
          onBlockDragStart={handleDragStart}
          onBlockResizeStart={handleResizeStart}
        />
      </ImageViewer>

      {/* Blocks list */}
      <BlocksList
        blocks={blocks}
        selectedBlocks={selectedBlocks}
        onBlockSelect={handleBlockSelect}
        onAssignToField={handleAssignToField}
        assigningToField={assigningToField}
        language={language}
      />

      {/* Edit block text modal */}
      {editingBlockText !== null && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            minWidth: '400px'
          }}>
            <h3>{language === 'ru' ? 'Редактировать текст' : 'Edit Text'}</h3>
            <textarea
              defaultValue={blocks?.lines[editingBlockText]?.text || ''}
              style={{
                width: '100%',
                minHeight: '100px',
                padding: '10px',
                fontSize: '14px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              ref={(el) => {
                if (el) {
                  el.focus();
                  el.select();
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setEditingBlockText(null);
                }
              }}
            />
            <div style={{ marginTop: '15px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditingBlockText(null)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#ccc',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {language === 'ru' ? 'Отмена' : 'Cancel'}
              </button>
              <button
                onClick={(e) => {
                  const textarea = e.target.parentElement.previousElementSibling;
                  updateBlockText(editingBlockText, textarea.value);
                  setEditingBlockText(null);
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#2196f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {language === 'ru' ? 'Сохранить' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{
        marginTop: '20px',
        display: 'flex',
        gap: '10px',
        justifyContent: 'flex-end'
      }}>
        <button
          onClick={onClose}
          style={{
            padding: '10px 20px',
            backgroundColor: '#ccc',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {t.cancel}
        </button>
        <button
          onClick={handleSave}
          style={{
            padding: '10px 20px',
            backgroundColor: '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {t.save}
        </button>
      </div>
    </div>
  );
};

