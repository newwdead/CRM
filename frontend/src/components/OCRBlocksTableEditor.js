import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import './OCRTableEditor.css';

/**
 * Simple Table-Based OCR Editor
 * No drag'n'drop, no coordinate transformations - just reliable editing
 */
const OCRBlocksTableEditor = ({ contact, onSave, onClose }) => {
  const [language] = useState(localStorage.getItem('language') || 'ru');
  const [blocks, setBlocks] = useState([]);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [editedData, setEditedData] = useState({});
  
  const translations = {
    ru: {
      title: 'Редактор OCR блоков',
      imagePreview: 'Изображение визитки',
      blocksTable: 'Блоки OCR',
      id: 'ID',
      text: 'Текст',
      field: 'Поле',
      confidence: 'Точность',
      actions: 'Действия',
      edit: 'Редактировать',
      delete: 'Удалить',
      reprocessOCR: 'Повторить OCR',
      save: 'Сохранить',
      cancel: 'Отмена',
      loading: 'Загрузка...',
      noBlocks: 'Блоки не найдены',
      selectField: '-- Выберите поле --',
      deleteConfirm: 'Удалить этот блок?',
      saveSuccess: 'Изменения сохранены',
      reprocessSuccess: 'OCR выполнен успешно',
      fields: {
        none: 'Не назначено',
        name: 'Имя',
        company: 'Компания',
        position: 'Должность',
        email: 'Email',
        phone: 'Телефон',
        phone_mobile: 'Моб. телефон',
        phone_work: 'Раб. телефон',
        address: 'Адрес',
        website: 'Сайт'
      }
    },
    en: {
      title: 'OCR Blocks Editor',
      imagePreview: 'Business Card Image',
      blocksTable: 'OCR Blocks',
      id: 'ID',
      text: 'Text',
      field: 'Field',
      confidence: 'Confidence',
      actions: 'Actions',
      edit: 'Edit',
      delete: 'Delete',
      reprocessOCR: 'Reprocess OCR',
      save: 'Save',
      cancel: 'Cancel',
      loading: 'Loading...',
      noBlocks: 'No blocks found',
      selectField: '-- Select field --',
      deleteConfirm: 'Delete this block?',
      saveSuccess: 'Changes saved',
      reprocessSuccess: 'OCR completed successfully',
      fields: {
        none: 'Not assigned',
        name: 'Name',
        company: 'Company',
        position: 'Position',
        email: 'Email',
        phone: 'Phone',
        phone_mobile: 'Mobile Phone',
        phone_work: 'Work Phone',
        address: 'Address',
        website: 'Website'
      }
    }
  };
  
  const t = translations[language];
  
  // Load OCR blocks
  useEffect(() => {
    loadBlocks();
  }, [contact.id]);
  
  const loadBlocks = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contact.id}/ocr-blocks`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to load blocks');
      
      const data = await response.json();
      setBlocks(data.lines || []);
      setImageSize({ width: data.image_width, height: data.image_height });
      
      // Initialize edited data from contact
      const initialData = {};
      ['full_name', 'company', 'position', 'email', 'phone', 'phone_mobile', 'phone_work', 'address', 'website'].forEach(field => {
        initialData[field] = contact[field] || '';
      });
      setEditedData(initialData);
      
    } catch (error) {
      console.error('Error loading blocks:', error);
      toast.error('Failed to load OCR blocks');
    } finally {
      setLoading(false);
    }
  };
  
  const reprocessOCR = async () => {
    if (!window.confirm(t.reprocessSuccess + '?')) return;
    
    try {
      setReprocessing(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contact.id}/rerun-ocr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to reprocess');
      
      toast.success(t.reprocessSuccess);
      await loadBlocks();
      
    } catch (error) {
      console.error('Error reprocessing:', error);
      toast.error('Failed to reprocess OCR');
    } finally {
      setReprocessing(false);
    }
  };
  
  const updateBlockText = (blockId, newText) => {
    setBlocks(prev => prev.map(block => 
      block.block_id === blockId ? { ...block, text: newText } : block
    ));
  };
  
  const assignBlockToField = (blockId, fieldName) => {
    const block = blocks.find(b => b.block_id === blockId);
    if (!block) return;
    
    // Update block field_type
    setBlocks(prev => prev.map(b => 
      b.block_id === blockId ? { ...b, field_type: fieldName || null } : b
    ));
    
    // Update edited data
    if (fieldName && fieldName !== 'none') {
      setEditedData(prev => ({
        ...prev,
        [fieldName]: block.text
      }));
    }
  };
  
  const deleteBlock = (blockId) => {
    if (!window.confirm(t.deleteConfirm)) return;
    setBlocks(prev => prev.filter(b => b.block_id !== blockId));
  };
  
  const handleSave = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // Save blocks
      await fetch(`/api/contacts/${contact.id}/save-ocr-blocks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          blocks: blocks,
          image_width: imageSize.width,
          image_height: imageSize.height
        })
      });
      
      // Send feedback for self-learning (async, don't wait)
      fetch(`/api/self-learning/feedback/${contact.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          blocks: blocks,
          image_width: imageSize.width,
          image_height: imageSize.height
        })
      }).then(res => {
        if (res.ok) {
          res.json().then(data => {
            if (data.corrections_count > 0) {
              console.log(`💡 Sent ${data.corrections_count} corrections for training`);
            }
          });
        }
      }).catch(err => {
        console.warn('Failed to send feedback:', err);
      });
      
      // Save contact data
      await onSave(editedData);
      
      toast.success(t.saveSuccess);
      
    } catch (error) {
      console.error('Error saving:', error);
      toast.error('Failed to save');
      setSaving(false);
    }
  };
  
  const imageUrl = contact.photo_path ? `/api/files/${contact.photo_path}` : null;
  
  if (loading) {
    return (
      <div className="ocr-editor-loading">
        <div className="spinner"></div>
        <p>{t.loading}</p>
      </div>
    );
  }
  
  return (
    <div className="ocr-table-editor">
      {/* Header */}
      <div className="ocr-editor-header">
        <h2>{t.title}</h2>
        <div className="header-actions">
          <button
            onClick={reprocessOCR}
            disabled={reprocessing}
            className="btn-secondary"
          >
            🔄 {t.reprocessOCR}
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            💾 {t.save}
          </button>
          <button onClick={onClose} className="btn-secondary">
            ❌ {t.cancel}
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="ocr-table-content">
        {/* Left Panel: Image Preview */}
        <div className="image-preview-panel">
          <h3>{t.imagePreview}</h3>
          {imageUrl && (
            <div className="image-container">
              <img 
                src={imageUrl} 
                alt="Business Card"
                style={{ maxWidth: '100%', maxHeight: '600px', objectFit: 'contain' }}
              />
              {/* Overlay blocks (read-only visualization) */}
              <svg
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none'
                }}
                viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                preserveAspectRatio="xMidYMid meet"
              >
                {blocks.map((block, idx) => {
                  if (!block.box) return null;
                  const isSelected = block.block_id === selectedBlockId;
                  return (
                    <rect
                      key={idx}
                      x={block.box.x}
                      y={block.box.y}
                      width={block.box.width}
                      height={block.box.height}
                      fill={isSelected ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.1)'}
                      stroke={isSelected ? '#3b82f6' : '#60a5fa'}
                      strokeWidth="2"
                    />
                  );
                })}
              </svg>
            </div>
          )}
        </div>
        
        {/* Right Panel: Blocks Table */}
        <div className="blocks-table-panel">
          <h3>{t.blocksTable} ({blocks.length})</h3>
          
          {blocks.length === 0 ? (
            <p className="no-blocks">{t.noBlocks}</p>
          ) : (
            <div className="blocks-table-wrapper">
              <table className="blocks-table">
                <thead>
                  <tr>
                    <th style={{ width: '50px' }}>{t.id}</th>
                    <th>{t.text}</th>
                    <th style={{ width: '180px' }}>{t.field}</th>
                    <th style={{ width: '90px' }}>{t.confidence}</th>
                    <th style={{ width: '80px' }}>{t.actions}</th>
                  </tr>
                </thead>
                <tbody>
                  {blocks.map((block, idx) => (
                    <tr 
                      key={idx}
                      className={block.block_id === selectedBlockId ? 'selected' : ''}
                      onMouseEnter={() => setSelectedBlockId(block.block_id)}
                      onMouseLeave={() => setSelectedBlockId(null)}
                    >
                      <td>{block.block_id ?? idx}</td>
                      <td>
                        <input
                          type="text"
                          value={block.text || ''}
                          onChange={(e) => updateBlockText(block.block_id, e.target.value)}
                          className="block-text-input"
                        />
                      </td>
                      <td>
                        <select
                          value={block.field_type || 'none'}
                          onChange={(e) => assignBlockToField(block.block_id, e.target.value)}
                          className="block-field-select"
                        >
                          <option value="none">{t.selectField}</option>
                          {Object.entries(t.fields).filter(([k]) => k !== 'none').map(([key, label]) => (
                            <option key={key} value={key}>{label}</option>
                          ))}
                        </select>
                      </td>
                      <td>{Math.round((block.confidence || 0) * 100)}%</td>
                      <td>
                        <button
                          onClick={() => deleteBlock(block.block_id)}
                          className="btn-delete-small"
                          title={t.delete}
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OCRBlocksTableEditor;

