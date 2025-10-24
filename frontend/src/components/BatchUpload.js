import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

export default function BatchUpload({ lang = 'ru' }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(null);

  const t = {
    ru: {
      title: 'Пакетная загрузка визиток',
      subtitle: 'Загрузите ZIP архив с несколькими визитками для автоматической обработки',
      dragDrop: 'Перетащите ZIP файл сюда или нажмите для выбора',
      fileSelected: 'Файл выбран',
      upload: 'Загрузить',
      processing: 'Обработка...',
      waiting: 'Ожидание в очереди...',
      completed: 'Завершено!',
      failed: 'Ошибка',
      cancel: 'Отмена',
      total: 'Всего',
      success: 'Успешно',
      errors: 'Ошибки',
      processed: 'Обработано',
      currentFile: 'Текущий файл',
      requirements: 'Требования к архиву',
      req1: '✓ Формат: ZIP',
      req2: '✓ Макс. размер: 100 MB',
      req3: '✓ Поддерживаемые форматы изображений: JPG, PNG, GIF, BMP, TIFF',
      req4: '✓ Рекомендуется: до 50 изображений в архиве',
      viewResults: 'Просмотреть результаты',
      backToUpload: 'Загрузить еще',
    },
    en: {
      title: 'Batch Upload Business Cards',
      subtitle: 'Upload a ZIP archive with multiple business cards for automatic processing',
      dragDrop: 'Drag & drop ZIP file here or click to select',
      fileSelected: 'File selected',
      upload: 'Upload',
      processing: 'Processing...',
      waiting: 'Waiting in queue...',
      completed: 'Completed!',
      failed: 'Failed',
      cancel: 'Cancel',
      total: 'Total',
      success: 'Success',
      errors: 'Errors',
      processed: 'Processed',
      currentFile: 'Current file',
      requirements: 'Archive Requirements',
      req1: '✓ Format: ZIP',
      req2: '✓ Max size: 100 MB',
      req3: '✓ Supported image formats: JPG, PNG, GIF, BMP, TIFF',
      req4: '✓ Recommended: up to 50 images per archive',
      viewResults: 'View Results',
      backToUpload: 'Upload More',
    }
  }[lang] || {};

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      toast.error(lang === 'ru' ? 'Только ZIP файлы разрешены!' : 'Only ZIP files allowed!', {
        icon: '❌',
        duration: 3000
      });
      return;
    }

    if (acceptedFiles && acceptedFiles.length > 0) {
      const zipFile = acceptedFiles[0];
      if (zipFile.size > 100 * 1024 * 1024) {
        toast.error(lang === 'ru' ? 'Файл слишком большой! Максимум 100 MB' : 'File too large! Maximum 100 MB', {
          icon: '⚠️',
          duration: 3000
        });
        return;
      }
      setFile(zipFile);
      toast.success(lang === 'ru' ? `ZIP файл выбран: ${zipFile.name}` : `ZIP file selected: ${zipFile.name}`, {
        icon: '📦',
        duration: 2000
      });
    }
  }, [lang]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    multiple: false,
    noClick: false,
    noKeyboard: false
  });

  const handleUpload = async () => {
    if (!file) {
      toast.error(t.dragDrop, { icon: '⚠️' });
      return;
    }

    setUploading(true);
    setProgress({ status: t.waiting, progress: 0 });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', 'auto');

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/ocr/batch-upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setTaskId(data.task_id);
        toast.success(lang === 'ru' ? 'Пакетная обработка запущена!' : 'Batch processing started!', {
          icon: '🚀',
          duration: 3000
        });

        // Start polling for progress
        pollProgress(data.task_id);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Upload failed', { icon: '❌', duration: 5000 });
        setUploading(false);
        setProgress(null);
      }
    } catch (e) {
      toast.error(e.message || 'Network error', { icon: '❌', duration: 5000 });
      setUploading(false);
      setProgress(null);
    }
  };

  const pollProgress = async (taskId) => {
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/ocr/batch-status/${taskId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
          const data = await res.json();
          setProgress(data);

          if (data.state === 'SUCCESS') {
            clearInterval(interval);
            setUploading(false);
            toast.success(
              `${t.completed} ${data.result.success} ${lang === 'ru' ? 'из' : 'of'} ${data.result.total}`,
              { icon: '✅', duration: 5000 }
            );
            // Refresh contact list
            window.dispatchEvent(new Event('refresh-contacts'));
          } else if (data.state === 'FAILURE') {
            clearInterval(interval);
            setUploading(false);
            toast.error(data.error || t.failed, { icon: '❌', duration: 5000 });
          }
        }
      } catch (e) {
        console.error('Failed to poll progress:', e);
      }
    }, 1000); // Poll every second

    // Cleanup on unmount
    return () => clearInterval(interval);
  };

  const resetForm = () => {
    setFile(null);
    setTaskId(null);
    setProgress(null);
    setUploading(false);
  };

  return (
    <div className="modern-card">
      <h3>{t.title}</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        {t.subtitle}
      </p>

      {!uploading && !progress ? (
        <>
          {/* Drag & Drop Zone */}
          <div
            {...getRootProps()}
            style={{
              border: `2px dashed ${isDragActive ? 'var(--primary-color)' : 'var(--border-color)'}`,
              borderRadius: 'var(--radius)',
              padding: '48px',
              textAlign: 'center',
              backgroundColor: isDragActive ? 'var(--primary-light)' : (file ? 'var(--bg-secondary)' : 'var(--bg-color)'),
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              marginBottom: '24px',
              transform: isDragActive ? 'scale(1.02)' : 'scale(1)'
            }}
          >
            <input {...getInputProps()} />
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>
              {isDragActive ? '📥' : (file ? '📦' : '🗂️')}
            </div>
            <div style={{ fontSize: '18px', marginBottom: '12px', fontWeight: 500 }}>
              {isDragActive ? (lang === 'ru' ? 'Отпустите файл здесь' : 'Drop file here') : (file ? t.fileSelected : t.dragDrop)}
            </div>
            {file && !isDragActive && (
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}
          </div>

          {/* Requirements */}
          <div className="modern-alert modern-alert-info" style={{ marginBottom: '24px' }}>
            <h4 style={{ marginTop: 0 }}>📋 {t.requirements}</h4>
            <ul style={{ marginBottom: 0, paddingLeft: '20px' }}>
              <li>{t.req1}</li>
              <li>{t.req2}</li>
              <li>{t.req3}</li>
              <li>{t.req4}</li>
            </ul>
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!file}
            style={{
              width: '100%',
              padding: '16px',
              fontSize: '16px',
              fontWeight: 600
            }}
          >
            📤 {t.upload}
          </button>
        </>
      ) : (
        <>
          {/* Progress Display */}
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              style={{
                padding: '32px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius)',
                textAlign: 'center'
              }}
            >
              {/* Status Icon */}
              <div style={{ fontSize: '64px', marginBottom: '16px' }}>
                {progress?.state === 'SUCCESS' ? '✅' : progress?.state === 'FAILURE' ? '❌' : '⏳'}
              </div>

              {/* Status Text */}
              <h3 style={{ marginBottom: '8px' }}>
                {progress?.state === 'SUCCESS' ? t.completed : progress?.state === 'FAILURE' ? t.failed : t.processing}
              </h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                {progress?.status || t.waiting}
              </p>

              {/* Progress Bar */}
              {progress && progress.state !== 'FAILURE' && (
                <>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'var(--border-color)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    marginBottom: '16px'
                  }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progress.progress || 0}%` }}
                      transition={{ duration: 0.3 }}
                      style={{
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--primary-color), var(--success-color))',
                        borderRadius: '4px'
                      }}
                    />
                  </div>

                  {/* Progress Stats */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '16px',
                    marginBottom: '16px',
                    textAlign: 'left'
                  }}>
                    {progress.total !== undefined && (
                      <>
                        <div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{t.total}</div>
                          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{progress.total}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{t.processed}</div>
                          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{progress.processed || 0}</div>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Current File */}
                  {progress.current_file && (
                    <div style={{
                      padding: '12px',
                      background: 'white',
                      borderRadius: 'var(--radius)',
                      fontSize: '14px',
                      marginBottom: '16px'
                    }}>
                      <strong>{t.currentFile}:</strong> {progress.current_file}
                    </div>
                  )}

                  {/* Results Summary */}
                  {progress.state === 'SUCCESS' && progress.result && (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: '12px',
                      marginBottom: '16px'
                    }}>
                      <div className="modern-alert modern-alert-info" style={{ margin: 0, padding: '16px' }}>
                        <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{progress.result.total}</div>
                        <div style={{ fontSize: '12px' }}>{t.total}</div>
                      </div>
                      <div className="modern-alert modern-alert-success" style={{ margin: 0, padding: '16px' }}>
                        <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{progress.result.success}</div>
                        <div style={{ fontSize: '12px' }}>{t.success}</div>
                      </div>
                      <div className="modern-alert modern-alert-danger" style={{ margin: 0, padding: '16px' }}>
                        <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{progress.result.failed}</div>
                        <div style={{ fontSize: '12px' }}>{t.errors}</div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Action Button */}
              {progress?.state === 'SUCCESS' || progress?.state === 'FAILURE' ? (
                <button onClick={resetForm} style={{ width: '100%' }}>
                  {t.backToUpload}
                </button>
              ) : null}
            </motion.div>
          </AnimatePresence>
        </>
      )}
    </div>
  );
}

