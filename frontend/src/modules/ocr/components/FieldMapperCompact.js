/**
 * FieldMapperCompact Component
 * Компактный и удобный интерфейс для привязки OCR блоков к полям
 * С автоматическим определением полей
 */

import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const translations = {
  en: {
    title: 'Field Mapping',
    autoDetected: 'Auto-detected',
    notMapped: 'Not mapped',
    saveMappings: 'Save',
    rerecognize: 'Re-scan',
    saving: 'Saving...',
    success: 'Saved!',
    error: 'Error'
  },
  ru: {
    title: 'Привязка полей',
    autoDetected: 'Авто-определено',
    notMapped: 'Не назначено',
    saveMappings: 'Сохранить',
    rerecognize: 'Пересканировать',
    saving: 'Сохранение...',
    success: 'Сохранено!',
    error: 'Ошибка'
  }
};

// Автоопределение поля из текста
const autoDetectField = (text) => {
  if (!text || text.length < 2) return null;
  
  const lower = text.toLowerCase().trim();
  
  // Email
  if (/@/.test(text)) return 'email';
  
  // Website
  if (/^(https?:\/\/|www\.)/.test(lower)) return 'website';
  
  // Phone (любые варианты с +, скобками, дефисами)
  if (/[\d\s\-\+\(\)]{7,}/.test(text) && /\d{3,}/.test(text)) {
    if (/^\+7|^8/.test(text)) return 'phone_mobile';
    return 'phone';
  }
  
  // Address (содержит номер дома, улицу)
  if (/(ул\.|улица|пр\.|проспект|пер\.|переулок|д\.|дом)/i.test(text)) return 'address';
  if (/\d+.*?(street|avenue|road|st\.|ave\.|rd\.)/i.test(text)) return 'address';
  
  // Position keywords
  const positionKeywords = ['директор', 'менеджер', 'специалист', 'инженер', 'руководитель', 
    'manager', 'director', 'ceo', 'cto', 'developer', 'designer'];
  if (positionKeywords.some(kw => lower.includes(kw))) return 'position';
  
  // Company indicators
  const companyIndicators = ['ооо', 'зао', 'оао', 'ао', 'ип', 'ltd', 'inc', 'corp', 'llc'];
  if (companyIndicators.some(ind => lower.includes(ind))) return 'company';
  
  // Name patterns (короткие слова, похожие на имена)
  if (/^[А-ЯЁA-Z][а-яёa-z]+$/.test(text) && text.length < 15) {
    // Может быть имя, фамилия или отчество
    return null; // Не угадываем, пусть пользователь выберет
  }
  
  return null;
};

export const FieldMapperCompact = ({ blocks, onBlocksUpdate, contactId, language = 'ru' }) => {
  const [availableFields, setAvailableFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedBlock, setExpandedBlock] = useState(null);
  
  const t = translations[language];
  
  useEffect(() => {
    loadAvailableFields();
  }, [contactId]);
  
  // Auto-detect fields on mount
  useEffect(() => {
    if (blocks && blocks.lines && availableFields.length > 0) {
      autoDetectAllFields();
    }
  }, [availableFields.length]);
  
  const loadAvailableFields = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/ocr-blocks/${contactId}/available-fields`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to load fields');
      
      const data = await response.json();
      setAvailableFields(data.fields);
    } catch (error) {
      console.error('[FieldMapper] Error:', error);
    }
  };
  
  const autoDetectAllFields = () => {
    if (!blocks || !blocks.lines) return;
    
    const updatedBlocks = blocks.lines.map(block => {
      // Если поле уже назначено, не меняем
      if (block.field) return block;
      
      // Авто-определяем
      const detectedField = autoDetectField(block.text);
      if (detectedField) {
        return { ...block, field: detectedField, autoDetected: true };
      }
      return block;
    });
    
    onBlocksUpdate({ ...blocks, lines: updatedBlocks });
  };
  
  const handleFieldChange = (blockIndex, fieldName) => {
    const updatedBlocks = blocks.lines.map((block, idx) => {
      if (idx === blockIndex) {
        return { ...block, field: fieldName || null, autoDetected: false };
      }
      return block;
    });
    
    onBlocksUpdate({ ...blocks, lines: updatedBlocks });
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
        body: JSON.stringify({ blocks: blocks.lines })
      });
      
      if (!response.ok) throw new Error('Failed to save');
      
      toast.success(t.success);
    } catch (error) {
      console.error('Error saving:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };
  
  const getFieldLabel = (fieldName) => {
    const field = availableFields.find(f => f.name === fieldName);
    return field ? (language === 'ru' ? field.label : field.label_en) : fieldName;
  };
  
  const getFieldColor = (fieldName) => {
    const colors = {
      'first_name': '#3b82f6',
      'last_name': '#3b82f6',
      'middle_name': '#3b82f6',
      'company': '#8b5cf6',
      'position': '#8b5cf6',
      'email': '#10b981',
      'phone': '#f59e0b',
      'phone_mobile': '#f59e0b',
      'phone_work': '#f59e0b',
      'phone_additional': '#f59e0b',
      'address': '#eab308',
      'address_additional': '#eab308',
      'website': '#6366f1',
      'comment': '#6b7280'
    };
    return colors[fieldName] || '#9ca3af';
  };
  
  if (!blocks || !blocks.lines || availableFields.length === 0) return null;
  
  return (
    <div style={{
      marginTop: '20px',
      padding: '15px',
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '15px'
      }}>
        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#374151' }}>
          📋 {t.title}
        </h4>
        
        <button
          onClick={handleSaveMappings}
          disabled={loading}
          style={{
            padding: '6px 16px',
            backgroundColor: loading ? '#9ca3af' : '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: '500',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {loading ? t.saving : `💾 ${t.saveMappings}`}
        </button>
      </div>
      
      {/* Compact Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '10px'
      }}>
        {blocks.lines.map((block, index) => {
          const fieldColor = block.field ? getFieldColor(block.field) : '#e5e7eb';
          const isExpanded = expandedBlock === index;
          
          return (
            <div
              key={index}
              style={{
                padding: '10px',
                backgroundColor: '#f9fafb',
                border: `2px solid ${fieldColor}`,
                borderRadius: '6px',
                transition: 'all 0.2s',
                cursor: 'pointer'
              }}
              onClick={() => setExpandedBlock(isExpanded ? null : index)}
            >
              {/* Block text preview */}
              <div style={{
                fontSize: '12px',
                color: '#1f2937',
                marginBottom: '8px',
                fontWeight: '500',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {block.text || '(пусто)'}
              </div>
              
              {/* Field selector */}
              <select
                value={block.field || ''}
                onChange={(e) => {
                  e.stopPropagation();
                  handleFieldChange(index, e.target.value);
                }}
                onClick={(e) => e.stopPropagation()}
                style={{
                  width: '100%',
                  padding: '5px 8px',
                  fontSize: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: 'white',
                  color: '#374151',
                  cursor: 'pointer'
                }}
              >
                <option value="">
                  {block.autoDetected ? `✨ ${t.autoDetected}` : t.notMapped}
                </option>
                {availableFields.map(field => (
                  <option key={field.name} value={field.name}>
                    {language === 'ru' ? field.label : field.label_en}
                  </option>
                ))}
              </select>
              
              {/* Current field badge */}
              {block.field && (
                <div style={{
                  marginTop: '6px',
                  padding: '3px 8px',
                  backgroundColor: fieldColor,
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: '500',
                  borderRadius: '4px',
                  display: 'inline-block'
                }}>
                  {block.autoDetected && '✨ '}
                  {getFieldLabel(block.field)}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Legend */}
      <div style={{
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#f9fafb',
        borderRadius: '6px',
        fontSize: '11px',
        color: '#6b7280'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '6px' }}>Легенда:</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ padding: '2px 8px', backgroundColor: '#3b82f6', color: 'white', borderRadius: '3px' }}>Имя</span>
          <span style={{ padding: '2px 8px', backgroundColor: '#8b5cf6', color: 'white', borderRadius: '3px' }}>Компания</span>
          <span style={{ padding: '2px 8px', backgroundColor: '#10b981', color: 'white', borderRadius: '3px' }}>Email</span>
          <span style={{ padding: '2px 8px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '3px' }}>Телефон</span>
          <span style={{ padding: '2px 8px', backgroundColor: '#eab308', color: 'white', borderRadius: '3px' }}>Адрес</span>
          <span style={{ fontSize: '10px' }}>✨ = Авто-определено</span>
        </div>
      </div>
    </div>
  );
};

