/**
 * FieldMapper Component
 * Позволяет назначать OCR блоки конкретным полям контакта
 */

import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const translations = {
  en: {
    title: 'Field Mapping',
    assignToField: 'Assign to field',
    selectField: 'Select field...',
    clearMapping: 'Clear',
    rerecognize: 'Re-recognize',
    saveМappings: 'Save Mappings',
    blockText: 'Block text',
    mappedTo: 'Mapped to',
    noMapping: 'Not mapped',
    rerecognizeSuccess: 'Block re-recognized',
    rerecognizeError: 'Failed to re-recognize',
    saveMappingsSuccess: 'Mappings saved successfully',
    saveMappingsError: 'Failed to save mappings'
  },
  ru: {
    title: 'Привязка к полям',
    assignToField: 'Назначить полю',
    selectField: 'Выберите поле...',
    clearMapping: 'Очистить',
    rerecognize: 'Перераспознать',
    saveMappings: 'Сохранить привязки',
    blockText: 'Текст блока',
    mappedTo: 'Привязан к',
    noMapping: 'Не привязан',
    rerecognizeSuccess: 'Блок перераспознан',
    rerecognizeError: 'Ошибка распознавания',
    saveMappingsSuccess: 'Привязки сохранены',
    saveMappingsError: 'Ошибка сохранения'
  }
};

export const FieldMapper = ({ blocks, onBlocksUpdate, contactId, selectedBlock, language = 'ru' }) => {
  const [availableFields, setAvailableFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rerecognizing, setRerecognizing] = useState(null);
  
  const t = translations[language];
  
  useEffect(() => {
    loadAvailableFields();
  }, [contactId]);
  
  const loadAvailableFields = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('[FieldMapper] Loading fields for contact:', contactId);
      
      const response = await fetch(`/api/ocr-blocks/${contactId}/available-fields`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('[FieldMapper] Response status:', response.status);
      
      if (!response.ok) {
        const error = await response.text();
        console.error('[FieldMapper] Failed to load fields:', error);
        throw new Error('Failed to load fields');
      }
      
      const data = await response.json();
      console.log('[FieldMapper] Loaded fields:', data.fields?.length);
      setAvailableFields(data.fields);
    } catch (error) {
      console.error('[FieldMapper] Error loading fields:', error);
      toast.error('Не удалось загрузить список полей');
    }
  };
  
  const handleFieldChange = (blockIndex, fieldName) => {
    const updatedBlocks = blocks.lines.map((block, idx) => {
      if (idx === blockIndex) {
        return { ...block, field: fieldName || null };
      }
      return block;
    });
    
    onBlocksUpdate({ ...blocks, lines: updatedBlocks });
  };
  
  const handleRerecognize = async (blockIndex) => {
    const block = blocks.lines[blockIndex];
    
    try {
      setRerecognizing(blockIndex);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/ocr-blocks/${contactId}/ocr-rerecognize-block`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          box: block.box,
          block_index: blockIndex
        })
      });
      
      if (!response.ok) throw new Error('Failed to re-recognize');
      
      const data = await response.json();
      
      // Update block with new text
      const updatedBlocks = blocks.lines.map((b, idx) => {
        if (idx === blockIndex) {
          return {
            ...b,
            text: data.text,
            confidence: data.confidence
          };
        }
        return b;
      });
      
      onBlocksUpdate({ ...blocks, lines: updatedBlocks });
      toast.success(t.rerecognizeSuccess);
      
    } catch (error) {
      console.error('Error re-recognizing:', error);
      toast.error(t.rerecognizeError);
    } finally {
      setRerecognizing(null);
    }
  };
  
  const handleSaveMappings = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/ocr-blocks/${contactId}/save-field-mappings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          blocks: blocks.lines
        })
      });
      
      if (!response.ok) throw new Error('Failed to save mappings');
      
      const data = await response.json();
      toast.success(`${t.saveMappingsSuccess}: ${data.updated_fields.join(', ')}`);
      
    } catch (error) {
      console.error('Error saving mappings:', error);
      toast.error(t.saveMappingsError);
    } finally {
      setLoading(false);
    }
  };
  
  const getFieldLabel = (fieldName, lang) => {
    const field = availableFields.find(f => f.name === fieldName);
    return field ? (lang === 'ru' ? field.label : field.label_en) : fieldName;
  };
  
  const getFieldColor = (fieldName) => {
    // Цветовая кодировка по типам полей
    const colors = {
      'first_name': 'bg-blue-100 text-blue-800 border-blue-300',
      'last_name': 'bg-blue-100 text-blue-800 border-blue-300',
      'middle_name': 'bg-blue-100 text-blue-800 border-blue-300',
      'company': 'bg-purple-100 text-purple-800 border-purple-300',
      'position': 'bg-purple-100 text-purple-800 border-purple-300',
      'email': 'bg-green-100 text-green-800 border-green-300',
      'phone': 'bg-orange-100 text-orange-800 border-orange-300',
      'phone_mobile': 'bg-orange-100 text-orange-800 border-orange-300',
      'phone_work': 'bg-orange-100 text-orange-800 border-orange-300',
      'phone_additional': 'bg-orange-100 text-orange-800 border-orange-300',
      'address': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'address_additional': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'website': 'bg-indigo-100 text-indigo-800 border-indigo-300',
      'comment': 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return colors[fieldName] || 'bg-gray-100 text-gray-800 border-gray-300';
  };
  
  if (!blocks || !blocks.lines) return null;
  
  return (
    <div style={{
      padding: '15px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #dee2e6'
    }}>
      <h4 style={{ marginBottom: '15px', fontSize: '16px', fontWeight: 'bold' }}>
        {t.title}
      </h4>
      
      {/* Debug info */}
      {availableFields.length === 0 && (
        <div style={{ padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px', marginBottom: '10px', fontSize: '12px' }}>
          ⚠️ Поля не загружены. Проверьте консоль браузера.
        </div>
      )}
      
      {/* Blocks List */}
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {blocks.lines.map((block, index) => {
          const isSelected = selectedBlock === index;
          const isRerecognizing = rerecognizing === index;
          
          return (
            <div
              key={index}
              style={{
                padding: '10px',
                marginBottom: '10px',
                backgroundColor: isSelected ? '#e3f2fd' : 'white',
                border: `2px solid ${isSelected ? '#2196F3' : block.field ? getFieldColor(block.field).split(' ')[2].replace('border-', '#') : '#dee2e6'}`,
                borderRadius: '6px',
                transition: 'all 0.2s'
              }}
            >
              {/* Block Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: '#6c757d', fontWeight: 'bold' }}>
                  Блок #{index + 1}
                </span>
                
                {block.field && (
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getFieldColor(block.field)}`}>
                    {getFieldLabel(block.field, language)}
                  </span>
                )}
              </div>
              
              {/* Block Text */}
              <div style={{
                padding: '8px',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                marginBottom: '8px',
                fontSize: '14px',
                fontFamily: 'monospace',
                wordBreak: 'break-word'
              }}>
                {block.text || <span style={{ color: '#999' }}>(пусто)</span>}
              </div>
              
              {/* Controls */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {/* Field Selector */}
                <select
                  value={block.field || ''}
                  onChange={(e) => handleFieldChange(index, e.target.value)}
                  style={{
                    flex: 1,
                    padding: '6px 8px',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}
                >
                  <option value="">{t.selectField}</option>
                  {availableFields.map(field => (
                    <option key={field.name} value={field.name}>
                      {language === 'ru' ? field.label : field.label_en}
                    </option>
                  ))}
                </select>
                
                {/* Re-recognize Button */}
                <button
                  onClick={() => handleRerecognize(index)}
                  disabled={isRerecognizing}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: isRerecognizing ? '#6c757d' : '#17a2b8',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: isRerecognizing ? 'not-allowed' : 'pointer',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {isRerecognizing ? '...' : '🔄'}
                </button>
                
                {/* Clear Button */}
                {block.field && (
                  <button
                    onClick={() => handleFieldChange(index, null)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Save Button */}
      <button
        onClick={handleSaveMappings}
        disabled={loading}
        style={{
          marginTop: '15px',
          padding: '10px 20px',
          width: '100%',
          backgroundColor: loading ? '#6c757d' : '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          fontSize: '14px',
          fontWeight: 'bold',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Сохранение...' : `💾 ${t.saveMappings}`}
      </button>
      
      {/* Legend */}
      <div style={{ marginTop: '15px', padding: '10px', backgroundColor: 'white', borderRadius: '4px', fontSize: '12px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Цветовая кодировка:</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">Имя</span>
          <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800">Компания/Должность</span>
          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">Email</span>
          <span className="px-2 py-1 rounded text-xs bg-orange-100 text-orange-800">Телефон</span>
          <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800">Адрес</span>
        </div>
      </div>
    </div>
  );
};

