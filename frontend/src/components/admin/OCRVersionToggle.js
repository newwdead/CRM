import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const OCRVersionToggle = ({ lang = 'ru' }) => {
  const [ocrVersion, setOcrVersion] = useState('v2.0');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [versionInfo, setVersionInfo] = useState(null);

  const translations = {
    ru: {
      title: 'Версия OCR',
      subtitle: 'Выберите движок распознавания визиток',
      version1Title: 'OCR v1.0 (Tesseract)',
      version1Desc: 'Классический Tesseract OCR',
      version1Speed: 'Скорость: Быстрая (1-2с)',
      version1Accuracy: 'Точность: 60-70%',
      version2Title: 'OCR v2.0 (PaddleOCR + AI)',
      version2Desc: 'AI-powered OCR с классификацией полей',
      version2Speed: 'Скорость: Средняя (3-5с)',
      version2Accuracy: 'Точность: 80-90%',
      current: 'Текущая версия',
      select: 'Выбрать',
      selected: 'Выбрано',
      saving: 'Сохранение...',
      success: 'Версия OCR успешно изменена',
      error: 'Ошибка при изменении версии OCR',
      features: 'Возможности'
    },
    en: {
      title: 'OCR Version',
      subtitle: 'Choose business card recognition engine',
      version1Title: 'OCR v1.0 (Tesseract)',
      version1Desc: 'Classic Tesseract OCR',
      version1Speed: 'Speed: Fast (1-2s)',
      version1Accuracy: 'Accuracy: 60-70%',
      version2Title: 'OCR v2.0 (PaddleOCR + AI)',
      version2Desc: 'AI-powered OCR with field classification',
      version2Speed: 'Speed: Medium (3-5s)',
      version2Accuracy: 'Accuracy: 80-90%',
      current: 'Current version',
      select: 'Select',
      selected: 'Selected',
      saving: 'Saving...',
      success: 'OCR version changed successfully',
      error: 'Failed to change OCR version',
      features: 'Features'
    }
  };

  const t = translations[lang] || translations.ru;

  useEffect(() => {
    fetchOcrVersion();
  }, []);

  const fetchOcrVersion = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/ocr/settings/version', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch OCR version');

      const data = await response.json();
      setOcrVersion(data.version);
      setVersionInfo(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching OCR version:', error);
      setLoading(false);
      toast.error(t.error);
    }
  };

  const handleVersionChange = async (newVersion) => {
    if (newVersion === ocrVersion || saving) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/ocr/settings/version', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ version: newVersion })
      });

      if (!response.ok) throw new Error('Failed to update OCR version');

      const data = await response.json();
      setOcrVersion(newVersion);
      toast.success(t.success);
    } catch (error) {
      console.error('Error updating OCR version:', error);
      toast.error(t.error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center',
        color: '#666'
      }}>
        {t.saving}
      </div>
    );
  }

  const versions = [
    {
      id: 'v1.0',
      icon: '🔤',
      color: '#6c757d',
      title: t.version1Title,
      description: t.version1Desc,
      speed: t.version1Speed,
      accuracy: t.version1Accuracy,
      features: [
        'Basic text recognition',
        'Multiple languages',
        'Fast processing'
      ]
    },
    {
      id: 'v2.0',
      icon: '🤖',
      color: '#0366d6',
      title: t.version2Title,
      description: t.version2Desc,
      speed: t.version2Speed,
      accuracy: t.version2Accuracy,
      features: [
        'PaddleOCR recognition',
        'LayoutLMv3 AI classification',
        'Auto-validation',
        'MinIO storage',
        'Fallback to v1.0'
      ]
    }
  ];

  return (
    <div style={{ 
      padding: '24px',
      backgroundColor: '#f5f7fa',
      borderRadius: '12px',
      marginTop: '16px'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ 
          margin: '0 0 8px 0', 
          fontSize: '20px', 
          color: '#333',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          🎛️ {t.title}
        </h3>
        <p style={{ 
          margin: 0, 
          fontSize: '14px', 
          color: '#666' 
        }}>
          {t.subtitle}
        </p>
      </div>

      {/* Current Version Badge */}
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 16px',
        backgroundColor: '#fff',
        borderRadius: '20px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        fontSize: '14px',
        fontWeight: '600'
      }}>
        <span style={{ color: '#666' }}>{t.current}:</span>
        <span style={{ color: ocrVersion === 'v2.0' ? '#0366d6' : '#6c757d' }}>
          {ocrVersion}
        </span>
      </div>

      {/* Version Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '16px'
      }}>
        {versions.map((version) => {
          const isSelected = version.id === ocrVersion;
          
          return (
            <motion.div
              key={version.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: isSelected ? 1 : 1.02 }}
              style={{
                backgroundColor: '#fff',
                borderRadius: '12px',
                padding: '20px',
                border: `3px solid ${isSelected ? version.color : '#e1e4e8'}`,
                boxShadow: isSelected 
                  ? `0 4px 12px ${version.color}40` 
                  : '0 2px 4px rgba(0,0,0,0.1)',
                cursor: isSelected ? 'default' : 'pointer',
                transition: 'all 0.2s',
                position: 'relative'
              }}
              onClick={() => !isSelected && !saving && handleVersionChange(version.id)}
            >
              {/* Selected Badge */}
              {isSelected && (
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  backgroundColor: version.color,
                  color: '#fff',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  ✓ {t.selected}
                </div>
              )}

              {/* Icon & Title */}
              <div style={{ 
                display: 'flex', 
                alignItems: 'flex-start',
                gap: '12px',
                marginBottom: '12px'
              }}>
                <div style={{ fontSize: '32px' }}>
                  {version.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ 
                    margin: '0 0 4px 0', 
                    fontSize: '18px',
                    color: '#333'
                  }}>
                    {version.title}
                  </h4>
                  <p style={{ 
                    margin: 0, 
                    fontSize: '13px', 
                    color: '#666' 
                  }}>
                    {version.description}
                  </p>
                </div>
              </div>

              {/* Stats */}
              <div style={{ 
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                marginBottom: '12px',
                paddingTop: '12px',
                borderTop: '1px solid #e1e4e8'
              }}>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  ⚡ {version.speed}
                </div>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  🎯 {version.accuracy}
                </div>
              </div>

              {/* Features */}
              <div style={{ 
                marginBottom: '16px'
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  fontWeight: '600',
                  color: '#333',
                  marginBottom: '8px'
                }}>
                  {t.features}:
                </div>
                <ul style={{ 
                  margin: 0, 
                  paddingLeft: '20px',
                  fontSize: '12px',
                  color: '#666'
                }}>
                  {version.features.map((feature, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Select Button */}
              {!isSelected && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleVersionChange(version.id);
                  }}
                  disabled={saving}
                  style={{
                    width: '100%',
                    padding: '10px',
                    backgroundColor: version.color,
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: saving ? 'not-allowed' : 'pointer',
                    opacity: saving ? 0.6 : 1,
                    transition: 'all 0.2s'
                  }}
                >
                  {saving ? t.saving : t.select}
                </button>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Info Message */}
      <div style={{
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#fff3cd',
        border: '1px solid #ffc107',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#856404'
      }}>
        💡 <strong>{lang === 'ru' ? 'Совет' : 'Tip'}:</strong>{' '}
        {lang === 'ru' 
          ? 'OCR v2.0 обеспечивает лучшую точность благодаря AI, но работает чуть медленнее. При ошибках v2.0 автоматически переключается на v1.0.' 
          : 'OCR v2.0 provides better accuracy with AI, but is slightly slower. If v2.0 fails, it automatically falls back to v1.0.'}
      </div>
    </div>
  );
};

export default OCRVersionToggle;


