import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

/**
 * Advanced OCR Editor with Bounding Boxes
 * Visual editor for correcting OCR results with block-level visualization
 */
const OCREditorWithBlocks = ({ contact, onSave, onClose }) => {
  const [editedData, setEditedData] = useState({});
  const [ocrBlocks, setOcrBlocks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedBlocks, setSelectedBlocks] = useState([]); // Changed to array for multiple selection
  const [assigningToField, setAssigningToField] = useState(null);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  
  const imageRef = useRef(null);
  const [imageScale, setImageScale] = useState(1);
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  const translations = {
    en: {
      title: 'OCR Editor with Blocks',
      subtitle: 'Click blocks to assign to fields',
      loadingBlocks: 'Loading OCR blocks...',
      selectBlock: 'Select a text block',
      selectedBlocks: 'Selected blocks',
      assignTo: 'Assign to field:',
      assignButton: 'Assign',
      cancelAssignment: 'Cancel',
      clearSelection: 'Clear selection',
      multiSelectMode: 'Multi-select mode',
      multiSelectHint: 'Hold Ctrl to select multiple blocks',
      noBlocks: 'No text blocks detected',
      fields: {
        first_name: 'First Name',
        last_name: 'Last Name',
        middle_name: 'Middle Name',
        company: 'Company',
        position: 'Position',
        email: 'Email',
        phone: 'Phone',
        phone_mobile: 'Mobile Phone',
        phone_work: 'Work Phone',
        phone_additional: 'Additional Phone',
        address: 'Address',
        address_additional: 'Additional Address',
        website: 'Website',
        comment: 'Notes'
      },
      buttons: {
        save: 'Save Changes',
        cancel: 'Cancel',
        reset: 'Reset'
      },
      messages: {
        saved: 'Changes saved successfully',
        error: 'Failed to save changes',
        loadError: 'Failed to load OCR blocks'
      }
    },
    ru: {
      title: 'Редактор OCR с блоками',
      subtitle: 'Нажмите на блоки для назначения полям',
      loadingBlocks: 'Загрузка блоков OCR...',
      selectBlock: 'Выберите текстовый блок',
      selectedBlocks: 'Выбрано блоков',
      assignTo: 'Назначить полю:',
      assignButton: 'Назначить',
      cancelAssignment: 'Отмена',
      clearSelection: 'Очистить выбор',
      multiSelectMode: 'Режим мультивыбора',
      multiSelectHint: 'Удерживайте Ctrl для выбора нескольких блоков',
      noBlocks: 'Текстовые блоки не обнаружены',
      fields: {
        first_name: 'Имя',
        last_name: 'Фамилия',
        middle_name: 'Отчество',
        company: 'Компания',
        position: 'Должность',
        email: 'Email',
        phone: 'Телефон',
        phone_mobile: 'Мобильный',
        phone_work: 'Рабочий',
        phone_additional: 'Доп. телефон',
        address: 'Адрес',
        address_additional: 'Доп. адрес',
        website: 'Веб-сайт',
        comment: 'Примечания'
      },
      buttons: {
        save: 'Сохранить',
        cancel: 'Отмена',
        reset: 'Сбросить'
      },
      messages: {
        saved: 'Изменения сохранены',
        error: 'Не удалось сохранить',
        loadError: 'Не удалось загрузить блоки OCR'
      }
    }
  };

  const t = translations[language];

  const editableFields = [
    'first_name', 'last_name', 'middle_name',
    'company', 'position',
    'email',
    'phone', 'phone_mobile', 'phone_work', 'phone_additional',
    'address', 'address_additional',
    'website',
    'comment'
  ];

  // Field colors for visualization
  const fieldColors = {
    first_name: '#3b82f6',
    last_name: '#8b5cf6',
    middle_name: '#a855f7',
    company: '#10b981',
    position: '#14b8a6',
    email: '#f59e0b',
    phone: '#ef4444',
    phone_mobile: '#ec4899',
    phone_work: '#f97316',
    phone_additional: '#84cc16',
    address: '#06b6d4',
    address_additional: '#0ea5e9',
    website: '#6366f1',
    comment: '#64748b'
  };

  useEffect(() => {
    // Initialize edited data
    const initial = {};
    editableFields.forEach(field => {
      initial[field] = contact[field] || '';
    });
    setEditedData(initial);

    // Load OCR blocks
    loadOCRBlocks();
  }, [contact.id]);

  const loadOCRBlocks = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${contact.id}/ocr-blocks`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to load OCR blocks');

      const data = await response.json();
      setOcrBlocks(data);
      
      // Calculate image scale to fit container
      calculateImageScale(data.image_width, data.image_height);
      
    } catch (error) {
      console.error('Error loading OCR blocks:', error);
      toast.error(t.messages.loadError);
    } finally {
      setLoading(false);
    }
  };

  const calculateImageScale = (imgWidth, imgHeight) => {
    if (!imageRef.current) return;
    
    const container = imageRef.current.parentElement;
    const maxWidth = container.clientWidth - 40; // padding
    const maxHeight = container.clientHeight - 40;
    
    const scaleX = maxWidth / imgWidth;
    const scaleY = maxHeight / imgHeight;
    const scale = Math.min(scaleX, scaleY, 1); // Don't scale up
    
    setImageScale(scale);
  };

  const handleBlockClick = (block, event) => {
    // Multi-select with Ctrl/Cmd key
    if (event && (event.ctrlKey || event.metaKey)) {
      setSelectedBlocks(prev => {
        const isSelected = prev.some(b => b === block);
        if (isSelected) {
          // Remove block
          return prev.filter(b => b !== block);
        } else {
          // Add block
          return [...prev, block];
        }
      });
    } else {
      // Single select
      setSelectedBlocks([block]);
    }
  };

  const handleAssignBlock = async (fieldName) => {
    if (selectedBlocks.length === 0) return;
    
    // Combine text from all selected blocks (separated by space)
    const combinedText = selectedBlocks.map(block => block.text).join(' ');
    
    // Update field value with combined text
    setEditedData(prev => ({
      ...prev,
      [fieldName]: combinedText
    }));
    
    // Save corrections for training (for each block)
    try {
      const token = localStorage.getItem('token');
      for (const block of selectedBlocks) {
        await fetch(`/api/contacts/${contact.id}/ocr-corrections`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            original_text: block.text,
            original_box: block.box,
            original_confidence: Math.round(block.confidence),
            corrected_text: combinedText,
            corrected_field: fieldName,
            ocr_provider: 'tesseract',
            language: 'rus+eng'
          })
        });
      }
    } catch (error) {
      console.error('Failed to save correction:', error);
      // Don't show error to user, this is background training data
    }
    
    const previewText = combinedText.length > 30 ? combinedText.substring(0, 30) + '...' : combinedText;
    toast.success(`Назначено: "${previewText}" → ${t.fields[fieldName]}`);
    setSelectedBlocks([]);
  };

  const handleFieldChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    // Check if there are any changes
    const hasChanges = editableFields.some(
      field => editedData[field] !== (contact[field] || '')
    );

    if (!hasChanges) {
      toast.info(t.messages.noChanges);
      return;
    }

    setSaving(true);
    try {
      await onSave(editedData);
      toast.success(t.messages.saved);
      onClose();
    } catch (error) {
      console.error('Save error:', error);
      toast.error(t.messages.error);
    } finally {
      setSaving(false);
    }
  };

  const imageUrl = contact.photo_path 
    ? `/api/files/${contact.photo_path}`
    : null;

  if (loading) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000
      }}>
        <div style={{
          backgroundColor: '#fff',
          padding: '40px',
          borderRadius: '16px',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '18px',
            color: '#333',
            marginBottom: '20px'
          }}>
            {t.loadingBlocks}
          </div>
          <div className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '20px',
        overflowY: 'auto'
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: '#fff',
          borderRadius: '16px',
          maxWidth: '1600px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'row',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
        }}
      >
        {/* Left side - Image with Bounding Boxes */}
        <div style={{
          width: '50%',
          backgroundColor: '#1a1a1a',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <h3 style={{
            margin: '0 0 10px 0',
            fontSize: '18px',
            color: '#fff',
            fontWeight: '600'
          }}>
            {t.title}
          </h3>
          <p style={{
            margin: '0 0 10px 0',
            fontSize: '14px',
            color: '#999'
          }}>
            {t.subtitle}
          </p>
          <div style={{
            margin: '0 0 15px 0',
            padding: '8px 12px',
            fontSize: '12px',
            color: '#fbbf24',
            backgroundColor: 'rgba(251, 191, 36, 0.1)',
            border: '1px solid rgba(251, 191, 36, 0.3)',
            borderRadius: '6px'
          }}>
            💡 {t.multiSelectHint}
          </div>
          
          {imageUrl && ocrBlocks && (
            <div style={{
              flex: 1,
              position: 'relative',
              overflow: 'auto',
              backgroundColor: '#000',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                position: 'relative',
                display: 'inline-block'
              }}>
                <img
                  ref={imageRef}
                  src={imageUrl}
                  alt="Business Card"
                  style={{
                    display: 'block',
                    maxWidth: '100%',
                    maxHeight: '100%',
                    transform: `scale(${imageScale})`,
                    transformOrigin: 'top left'
                  }}
                />
                
                {/* Render bounding boxes */}
                <svg
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: `${ocrBlocks.image_width * imageScale}px`,
                    height: `${ocrBlocks.image_height * imageScale}px`,
                    pointerEvents: 'none'
                  }}
                >
                  {ocrBlocks.lines.map((line, idx) => {
                    const box = line.box;
                    const isSelected = selectedBlocks.includes(line);
                    const selectionIndex = selectedBlocks.indexOf(line);
                    
                    return (
                      <g key={idx}>
                        <rect
                          x={box.x * imageScale}
                          y={box.y * imageScale}
                          width={box.width * imageScale}
                          height={box.height * imageScale}
                          fill={isSelected ? 'rgba(251, 191, 36, 0.3)' : 'rgba(59, 130, 246, 0.2)'}
                          stroke={isSelected ? '#fbbf24' : '#3b82f6'}
                          strokeWidth={isSelected ? 3 : 1}
                          style={{
                            pointerEvents: 'auto',
                            cursor: 'pointer'
                          }}
                          onClick={(e) => handleBlockClick(line, e)}
                        />
                        <text
                          x={box.x * imageScale + 5}
                          y={box.y * imageScale + 15}
                          fill="#fff"
                          fontSize="12"
                          fontWeight="bold"
                          style={{ pointerEvents: 'none' }}
                        >
                          {isSelected ? `✓${selectionIndex + 1}` : idx + 1}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          )}

          {/* Selected Blocks Info */}
          {selectedBlocks.length > 0 && (
            <div style={{
              marginTop: '15px',
              padding: '15px',
              backgroundColor: '#2a2a2a',
              borderRadius: '8px',
              border: '2px solid #fbbf24'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px'
              }}>
                <div style={{
                  fontSize: '12px',
                  color: '#999'
                }}>
                  {t.selectedBlocks}: {selectedBlocks.length}
                </div>
                <button
                  onClick={() => setSelectedBlocks([])}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    backgroundColor: '#ef4444',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  {t.clearSelection}
                </button>
              </div>
              
              {/* Show combined text */}
              <div style={{
                fontSize: '14px',
                color: '#fff',
                fontWeight: '600',
                marginBottom: '10px',
                padding: '8px',
                backgroundColor: '#1a1a1a',
                borderRadius: '4px',
                maxHeight: '80px',
                overflowY: 'auto'
              }}>
                {selectedBlocks.map((block, idx) => (
                  <span key={idx}>
                    {idx > 0 && ' '}
                    <span style={{ color: '#fbbf24' }}>{block.text}</span>
                  </span>
                ))}
              </div>
              
              <div style={{
                fontSize: '11px',
                color: '#666',
                marginBottom: '8px'
              }}>
                {t.multiSelectHint}
              </div>
              
              <div style={{
                fontSize: '12px',
                color: '#999'
              }}>
                {t.assignTo}
              </div>
            </div>
          )}
        </div>

        {/* Right side - Editable Fields */}
        <div style={{
          width: '50%',
          padding: '30px',
          overflowY: 'auto',
          backgroundColor: '#fff'
        }}>
          <div style={{
            marginBottom: '20px'
          }}>
            <h2 style={{
              margin: '0 0 8px 0',
              fontSize: '22px',
              color: '#1a202c',
              fontWeight: '700'
            }}>
              {t.title}
            </h2>
          </div>

          {/* Editable Fields Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '15px',
            marginBottom: '25px'
          }}>
            {editableFields.map(field => (
              <div
                key={field}
                style={{
                  gridColumn: ['address', 'address_additional', 'comment', 'website'].includes(field) ? 'span 2' : 'span 1'
                }}
              >
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '6px',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#4a5568'
                }}>
                  <span style={{
                    width: '12px',
                    height: '12px',
                    backgroundColor: fieldColors[field],
                    borderRadius: '3px',
                    marginRight: '8px'
                  }} />
                  {t.fields[field]}
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={field === 'email' ? 'email' : 'text'}
                    value={editedData[field] || ''}
                    onChange={(e) => handleFieldChange(field, e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      paddingRight: selectedBlocks.length > 0 ? '80px' : '10px',
                      fontSize: '14px',
                      border: '2px solid #e2e8f0',
                      borderRadius: '6px',
                      transition: 'all 0.2s',
                      outline: 'none',
                      backgroundColor: '#fff'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = fieldColors[field];
                      e.target.style.boxShadow = `0 0 0 3px ${fieldColors[field]}20`;
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#e2e8f0';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                  {selectedBlocks.length > 0 && (
                    <button
                      onClick={() => handleAssignBlock(field)}
                      title={`Назначить ${selectedBlocks.length} блок(ов)`}
                      style={{
                        position: 'absolute',
                        right: '5px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        padding: '5px 12px',
                        fontSize: '11px',
                        backgroundColor: fieldColors[field],
                        color: '#fff',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      ← {selectedBlocks.length > 1 && `(${selectedBlocks.length})`}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '10px',
            paddingTop: '20px',
            borderTop: '2px solid #e2e8f0'
          }}>
            <button
              onClick={handleSave}
              disabled={saving}
              style={{
                flex: 1,
                padding: '12px',
                backgroundColor: saving ? '#cbd5e0' : '#0366d6',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                opacity: saving ? 0.6 : 1
              }}
            >
              {saving ? '⏳ Сохранение...' : t.buttons.save}
            </button>

            <button
              onClick={onClose}
              disabled={saving}
              style={{
                padding: '12px 20px',
                backgroundColor: '#fff',
                color: '#e53e3e',
                border: '2px solid #feb2b2',
                borderRadius: '8px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {t.buttons.cancel}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default OCREditorWithBlocks;

