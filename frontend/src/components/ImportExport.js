import React, { useState } from 'react';

export default function ImportExport({ lang = 'ru' }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [importing, setImporting] = useState(false);
  const [showStatus, setShowStatus] = useState(false);

  const t = lang === 'ru' ? {
    title: '📊 Импорт / Экспорт',
    exportAll: 'Экспортировать все',
    exportCSV: 'CSV формат',
    exportXLSX: 'Excel формат',
    import: 'Импортировать',
    chooseFile: 'Выбрать файл',
    importing: 'Импорт...',
    success: 'Успешно импортировано!',
    error: 'Ошибка импорта',
    close: 'Закрыть',
    dragDrop: 'Перетащите CSV/XLSX файл сюда',
    fileSelected: 'Файл выбран',
    supportedFormats: 'Поддерживаемые форматы: CSV, XLS, XLSX',
  } : {
    title: '📊 Import / Export',
    exportAll: 'Export All',
    exportCSV: 'CSV Format',
    exportXLSX: 'Excel Format',
    import: 'Import',
    chooseFile: 'Choose File',
    importing: 'Importing...',
    success: 'Successfully imported!',
    error: 'Import error',
    close: 'Close',
    dragDrop: 'Drag & drop CSV/XLSX file here',
    fileSelected: 'File selected',
    supportedFormats: 'Supported formats: CSV, XLS, XLSX',
  };

  const handleExportCSV = () => window.open('/api/contacts/export', '_blank');
  const handleExportXLSX = () => window.open('/api/contacts/export/xlsx', '_blank');

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleImport = async () => {
    if (!file) return alert(t.chooseFile);
    
    setImporting(true);
    setStatus('');
    
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch('/api/contacts/import', { method: 'POST', body: fd });
      const data = await res.json();
      
      if (res.ok) {
        setStatus(`${t.success}\n${data.message || data.imported || JSON.stringify(data)}`);
      } else {
        setStatus(`${t.error}\n${data.error || data.detail || JSON.stringify(data)}`);
      }
      
      setShowStatus(true);
      setFile(null);
      window.dispatchEvent(new Event('refresh-contacts'));
    } catch (e) {
      setStatus(`${t.error}\n${e.message}`);
      setShowStatus(true);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="card">
      <h3>{t.title}</h3>

      {/* Export Section */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', marginBottom: '12px', fontWeight: 500 }}>
          ⬇️ {t.exportAll}
        </label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button onClick={handleExportCSV} className="secondary">
            📄 {t.exportCSV}
          </button>
          <button onClick={handleExportXLSX} className="secondary">
            📊 {t.exportXLSX}
          </button>
        </div>
      </div>

      {/* Import Section */}
      <div>
        <label style={{ display: 'block', marginBottom: '12px', fontWeight: 500 }}>
          ⬆️ {t.import}
        </label>
        
        {/* Drag & Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => document.getElementById('import-file-input').click()}
          style={{
            border: '2px dashed var(--border-color)',
            borderRadius: 'var(--radius)',
            padding: '24px',
            textAlign: 'center',
            backgroundColor: file ? 'var(--bg-secondary)' : 'var(--bg-color)',
            cursor: 'pointer',
            transition: 'all 0.2s',
            marginBottom: '12px'
          }}
        >
          <input
            id="import-file-input"
            type="file"
            accept=".csv,.xls,.xlsx"
            onChange={(e) => setFile(e.target.files[0])}
            style={{ display: 'none' }}
          />
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>
            {file ? '📋' : '📁'}
          </div>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            {file ? t.fileSelected : t.dragDrop}
          </div>
          {file && (
            <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-color)' }}>
              {file.name}
            </div>
          )}
          {!file && (
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
              {t.supportedFormats}
            </div>
          )}
        </div>

        <button
          onClick={handleImport}
          disabled={!file || importing}
          className="success"
          style={{ width: '100%' }}
        >
          {importing ? (
            <>
              <div className="spinner" style={{
                width: '16px',
                height: '16px',
                display: 'inline-block',
                marginRight: '8px',
                borderWidth: '2px'
              }}></div>
              {t.importing}
            </>
          ) : (
            `⬆️ ${t.import}`
          )}
        </button>
      </div>

      {/* Status Modal */}
      {showStatus && (
        <div className="modal-overlay" onClick={() => setShowStatus(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>{status.includes(t.success) ? t.success : t.error}</h3>
            <pre style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              backgroundColor: 'var(--bg-secondary)',
              padding: '12px',
              borderRadius: 'var(--radius)',
              maxHeight: '300px',
              overflow: 'auto',
              fontSize: '13px'
            }}>
              {status}
            </pre>
            <button onClick={() => setShowStatus(false)} style={{ marginTop: '16px', width: '100%' }}>
              {t.close}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
