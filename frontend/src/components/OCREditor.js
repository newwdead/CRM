import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

/**
 * OCR Editor Component
 * Visual editor for correcting OCR results on business card images
 */
const OCREditor = ({ contact, onSave, onClose }) => {
  const [editedData, setEditedData] = useState({});
  const [imageLoaded, setImageLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');

  const translations = {
    en: {
      title: 'Edit OCR Results',
      subtitle: 'Visual editor for business card data',
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
        reset: 'Reset to Original'
      },
      messages: {
        saved: 'Changes saved successfully',
        error: 'Failed to save changes',
        noChanges: 'No changes to save'
      },
      imagePreview: 'Business Card Image',
      ocrRaw: 'Original OCR Text',
      expandRaw: 'Show Raw OCR',
      collapseRaw: 'Hide Raw OCR'
    },
    ru: {
      title: 'Редактор OCR',
      subtitle: 'Визуальный редактор данных визитки',
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
        noChanges: 'Нет изменений'
      },
      imagePreview: 'Изображение визитки',
      ocrRaw: 'Исходный текст OCR',
      expandRaw: 'Показать OCR текст',
      collapseRaw: 'Скрыть OCR текст'
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

  useEffect(() => {
    // Initialize edited data with contact data
    const initial = {};
    editableFields.forEach(field => {
      initial[field] = contact[field] || '';
    });
    setEditedData(initial);
  }, [contact]);

  const [showRawOCR, setShowRawOCR] = useState(false);

  const handleFieldChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleReset = () => {
    const initial = {};
    editableFields.forEach(field => {
      initial[field] = contact[field] || '';
    });
    setEditedData(initial);
    toast.success(t.buttons.reset);
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

  // Parse OCR raw data for display
  const getRawOCRText = () => {
    if (!contact.ocr_raw) return 'No OCR data available';
    
    try {
      const parsed = JSON.parse(contact.ocr_raw);
      return parsed.raw_text || parsed.raw_data || JSON.stringify(parsed, null, 2);
    } catch (e) {
      return contact.ocr_raw;
    }
  };

  const imageUrl = contact.photo_path 
    ? `/api/files/${contact.photo_path}`
    : null;

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
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
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
          maxWidth: '1400px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'row',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
        }}
      >
        {/* Left side - Image Preview */}
        <div style={{
          width: '40%',
          backgroundColor: '#f7f9fc',
          padding: '30px',
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid #e1e4e8'
        }}>
          <h3 style={{
            margin: '0 0 20px 0',
            fontSize: '18px',
            color: '#333',
            fontWeight: '600'
          }}>
            {t.imagePreview}
          </h3>
          
          {imageUrl && (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#fff',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '20px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              overflow: 'hidden'
            }}>
              <img
                src={imageUrl}
                alt="Business Card"
                onLoad={() => setImageLoaded(true)}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  borderRadius: '8px',
                  opacity: imageLoaded ? 1 : 0,
                  transition: 'opacity 0.3s'
                }}
              />
            </div>
          )}

          {/* Raw OCR Text */}
          <div>
            <button
              onClick={() => setShowRawOCR(!showRawOCR)}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: showRawOCR ? '#0366d6' : '#fff',
                color: showRawOCR ? '#fff' : '#0366d6',
                border: `2px solid #0366d6`,
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginBottom: '10px'
              }}
            >
              {showRawOCR ? t.collapseRaw : t.expandRaw}
            </button>
            
            <AnimatePresence>
              {showRawOCR && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{
                    backgroundColor: '#2d3748',
                    color: '#e2e8f0',
                    padding: '16px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    overflow: 'auto',
                    maxHeight: '200px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}
                >
                  {getRawOCRText()}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Right side - Editable Fields */}
        <div style={{
          width: '60%',
          padding: '30px',
          overflowY: 'auto'
        }}>
          <div style={{
            marginBottom: '30px'
          }}>
            <h2 style={{
              margin: '0 0 8px 0',
              fontSize: '24px',
              color: '#1a202c',
              fontWeight: '700'
            }}>
              {t.title}
            </h2>
            <p style={{
              margin: 0,
              fontSize: '14px',
              color: '#718096'
            }}>
              {t.subtitle}
            </p>
          </div>

          {/* Editable Fields Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '20px',
            marginBottom: '30px'
          }}>
            {editableFields.map(field => (
              <div
                key={field}
                style={{
                  gridColumn: ['address', 'address_additional', 'comment', 'website'].includes(field) ? 'span 2' : 'span 1'
                }}
              >
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#4a5568'
                }}>
                  {t.fields[field]}
                  {field === 'phone_mobile' && ' 📱'}
                  {field === 'phone_work' && ' ☎️'}
                  {field === 'phone_additional' && ' ➕'}
                </label>
                <input
                  type={field === 'email' ? 'email' : 'text'}
                  value={editedData[field] || ''}
                  onChange={(e) => handleFieldChange(field, e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '14px',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    transition: 'all 0.2s',
                    outline: 'none',
                    backgroundColor: '#fff',
                    color: '#2d3748'
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#0366d6';
                    e.target.style.boxShadow = '0 0 0 3px rgba(3, 102, 214, 0.1)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#e2e8f0';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '12px',
            paddingTop: '20px',
            borderTop: '2px solid #e2e8f0'
          }}>
            <button
              onClick={handleSave}
              disabled={saving}
              style={{
                flex: 1,
                padding: '14px',
                backgroundColor: saving ? '#cbd5e0' : '#0366d6',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                opacity: saving ? 0.6 : 1
              }}
              onMouseEnter={(e) => {
                if (!saving) e.target.style.backgroundColor = '#0256c7';
              }}
              onMouseLeave={(e) => {
                if (!saving) e.target.style.backgroundColor = '#0366d6';
              }}
            >
              {saving ? '⏳ Сохранение...' : t.buttons.save}
            </button>

            <button
              onClick={handleReset}
              disabled={saving}
              style={{
                padding: '14px 24px',
                backgroundColor: '#fff',
                color: '#718096',
                border: '2px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!saving) {
                  e.target.style.backgroundColor = '#f7fafc';
                  e.target.style.borderColor = '#cbd5e0';
                }
              }}
              onMouseLeave={(e) => {
                if (!saving) {
                  e.target.style.backgroundColor = '#fff';
                  e.target.style.borderColor = '#e2e8f0';
                }
              }}
            >
              {t.buttons.reset}
            </button>

            <button
              onClick={onClose}
              disabled={saving}
              style={{
                padding: '14px 24px',
                backgroundColor: '#fff',
                color: '#e53e3e',
                border: '2px solid #feb2b2',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!saving) {
                  e.target.style.backgroundColor = '#fff5f5';
                  e.target.style.borderColor = '#fc8181';
                }
              }}
              onMouseLeave={(e) => {
                if (!saving) {
                  e.target.style.backgroundColor = '#fff';
                  e.target.style.borderColor = '#feb2b2';
                }
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

export default OCREditor;

