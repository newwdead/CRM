import React, { useEffect, useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import toast, { Toaster } from 'react-hot-toast';

export default function UploadCard({ lang = 'ru', defaultProvider = 'auto' }) {
  const [file, setFile] = useState(null);
  const [provider, setProvider] = useState(defaultProvider || 'auto');
  const [uploading, setUploading] = useState(false);
  const [availableProviders, setAvailableProviders] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const t = lang === 'ru' ? {
    title: '📤 Загрузить визитку',
    chooseFile: 'Выберите файл',
    noFileChosen: 'Файл не выбран',
    provider: 'OCR Провайдер',
    auto: 'Авто (рекомендуется)',
    upload: 'Загрузить',
    uploading: 'Загрузка...',
    error: 'Ошибка',
    success: 'Успешно загружено!',
    copy: 'Скопировать',
    close: 'Закрыть',
    dragDrop: 'Перетащите файл сюда или кликните для выбора',
    fileSelected: 'Выбран файл',
    resultTitle: 'Результат OCR',
    usedProvider: 'Использован провайдер',
    confidence: 'Уверенность',
    extractedData: 'Извлеченные данные',
    viewContact: 'Посмотреть контакт',
  } : {
    title: '📤 Upload Business Card',
    chooseFile: 'Choose File',
    noFileChosen: 'No file chosen',
    provider: 'OCR Provider',
    auto: 'Auto (recommended)',
    upload: 'Upload',
    uploading: 'Uploading...',
    error: 'Error',
    success: 'Successfully uploaded!',
    copy: 'Copy',
    close: 'Close',
    dragDrop: 'Drag & drop file here or click to select',
    fileSelected: 'File selected',
    resultTitle: 'OCR Result',
    usedProvider: 'Provider Used',
    confidence: 'Confidence',
    extractedData: 'Extracted Data',
    viewContact: 'View Contact',
  };

  useEffect(() => {
    setProvider(defaultProvider || 'auto');
  }, [defaultProvider]);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const res = await fetch('/api/ocr/providers');
      if (res.ok) {
        const data = await res.json();
        setAvailableProviders(data.available || []);
      }
    } catch (e) {
      console.error('Failed to load providers:', e);
    }
  };

  // React Dropzone
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      toast.error(lang === 'ru' ? 'Только изображения разрешены!' : 'Only images are allowed!', {
        icon: '❌',
        duration: 3000
      });
      return;
    }
    
    if (acceptedFiles && acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      toast.success(lang === 'ru' ? `Файл выбран: ${acceptedFiles[0].name}` : `File selected: ${acceptedFiles[0].name}`, {
        icon: '📁',
        duration: 2000
      });
    }
  }, [lang]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    multiple: false,
    noClick: false,
    noKeyboard: false
  });

  const upload = async () => {
    if (!file) {
      toast.error(lang === 'ru' ? 'Выберите файл визитки!' : 'Choose a file!', {
        icon: '⚠️'
      });
      return;
    }

    setUploading(true);
    
    // Show loading toast
    const loadingToast = toast.loading(lang === 'ru' ? 'Обрабатываем визитку...' : 'Processing business card...');

    try {
      const fd = new FormData();
      fd.append('file', file);
      const url = `/api/upload/?provider=${encodeURIComponent(provider)}`;
      
      const token = localStorage.getItem('token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const res = await fetch(url, { 
        method: 'POST', 
        headers,
        body: fd 
      });

      if (res.ok) {
        const data = await res.json();
        setLastResult(data);
        setShowResult(true);
        setFile(null);
        window.dispatchEvent(new Event('refresh-contacts'));
        
        // Success toast
        toast.success(lang === 'ru' ? 'Контакт успешно создан!' : 'Contact created successfully!', {
          id: loadingToast,
          icon: '✅',
          duration: 4000
        });
        
      } else {
        let message = lang === 'ru' ? 'Ошибка загрузки' : 'Upload error';
        try {
          const err = await res.json();
          if (err && err.detail) {
            message = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
          }
        } catch (_) {}
        
        toast.error(message, {
          id: loadingToast,
          icon: '❌',
          duration: 5000
        });
      }
    } catch (e) {
      toast.error(e.message || 'Network error', {
        id: loadingToast,
        icon: '❌',
        duration: 5000
      });
    } finally {
      setUploading(false);
    }
  };

  const getProviderBadge = (providerName) => {
    const colors = {
      'Tesseract': 'info',
      'Parsio': 'success',
      'Google Vision': 'warning'
    };
    return colors[providerName] || 'info';
  };

  return (
    <div className="card">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-color)',
            color: 'var(--text-color)',
            border: '1px solid var(--border-color)',
          },
          success: {
            style: {
              background: 'var(--success-bg)',
              color: 'var(--success-color)',
            },
          },
          error: {
            style: {
              background: 'var(--error-bg)',
              color: 'var(--error-color)',
            },
          },
        }}
      />
      
      <h3>{t.title}</h3>

      {/* Drag & Drop Zone with react-dropzone */}
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--primary-color)' : 'var(--border-color)'}`,
          borderRadius: 'var(--radius)',
          padding: '32px',
          textAlign: 'center',
          backgroundColor: isDragActive ? 'var(--primary-light)' : (file ? 'var(--bg-secondary)' : 'var(--bg-color)'),
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          marginBottom: '16px',
          transform: isDragActive ? 'scale(1.02)' : 'scale(1)',
          boxShadow: isDragActive ? '0 4px 12px rgba(0,0,0,0.1)' : 'none'
        }}
      >
        <input {...getInputProps()} />
        <div style={{ fontSize: '48px', marginBottom: '12px', transition: 'transform 0.2s' }}>
          {isDragActive ? '📥' : (file ? '✅' : '📁')}
        </div>
        <div style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          {isDragActive ? (lang === 'ru' ? 'Отпустите файл здесь' : 'Drop file here') : (file ? t.fileSelected : t.dragDrop)}
        </div>
        {file && !isDragActive && (
          <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-color)' }}>
            {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}
      </div>

      {/* Provider Selection */}
      <div className="form-group">
        <label>{t.provider}</label>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          disabled={uploading}
          style={{ maxWidth: '400px' }}
        >
          <option value="auto">{t.auto}</option>
          <option value="tesseract">Tesseract</option>
          {availableProviders.includes('Parsio') && (
            <option value="parsio">Parsio</option>
          )}
          {availableProviders.includes('Google Vision') && (
            <option value="google">Google Vision</option>
          )}
        </select>
      </div>

      {/* Upload Button */}
      <button
        onClick={upload}
        disabled={!file || uploading}
        className="success"
        style={{ width: '100%', maxWidth: '400px' }}
      >
        {uploading ? (
          <>
            <div className="spinner" style={{ 
              width: '16px', 
              height: '16px', 
              display: 'inline-block', 
              marginRight: '8px',
              borderWidth: '2px'
            }}></div>
            {t.uploading}
          </>
        ) : (
          t.upload
        )}
      </button>

      {/* Success Result Modal */}
      {showResult && lastResult && (
        <div className="modal-overlay" onClick={() => setShowResult(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>{t.resultTitle}</h3>

            <div className="alert success">
              ✅ {t.success}
            </div>

            {/* Provider Badge */}
            {lastResult.ocr_provider && (
              <div style={{ marginBottom: '16px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                  {t.usedProvider}:
                </span>
                {' '}
                <span className={`badge ${getProviderBadge(lastResult.ocr_provider)}`}>
                  {lastResult.ocr_provider}
                </span>
                {lastResult.ocr_confidence && (
                  <>
                    {' • '}
                    <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                      {t.confidence}: {(lastResult.ocr_confidence * 100).toFixed(0)}%
                    </span>
                  </>
                )}
              </div>
            )}

            {/* Extracted Data */}
            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: 'var(--radius)' }}>
              <h4 style={{ marginTop: 0, marginBottom: '12px' }}>{t.extractedData}</h4>
              <div style={{ fontSize: '14px' }}>
                {lastResult.full_name && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>{lang === 'ru' ? 'Имя' : 'Name'}:</strong> {lastResult.full_name}
                  </div>
                )}
                {lastResult.company && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>{lang === 'ru' ? 'Компания' : 'Company'}:</strong> {lastResult.company}
                  </div>
                )}
                {lastResult.position && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>{lang === 'ru' ? 'Должность' : 'Position'}:</strong> {lastResult.position}
                  </div>
                )}
                {lastResult.email && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>Email:</strong> {lastResult.email}
                  </div>
                )}
                {lastResult.phone && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>{lang === 'ru' ? 'Телефон' : 'Phone'}:</strong> {lastResult.phone}
                  </div>
                )}
              </div>
            </div>

            <button onClick={() => setShowResult(false)} style={{ marginTop: '16px', width: '100%' }}>
              {t.close}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
