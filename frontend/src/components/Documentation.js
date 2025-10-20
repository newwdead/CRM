import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const Documentation = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docContent, setDocContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');

  const translations = {
    en: {
      title: 'Documentation',
      selectDoc: 'Select a document',
      loading: 'Loading...',
      error: 'Failed to load documentation',
      noDocuments: 'No documentation available',
      lastModified: 'Last modified',
      size: 'Size',
      category: 'Category',
      production: 'Production',
      readme: 'General',
      telegram: 'Telegram',
      whatsapp: 'WhatsApp',
      monitoring: 'Monitoring'
    },
    ru: {
      title: 'Документация',
      selectDoc: 'Выберите документ',
      loading: 'Загрузка...',
      error: 'Не удалось загрузить документацию',
      noDocuments: 'Документация недоступна',
      lastModified: 'Последнее изменение',
      size: 'Размер',
      category: 'Категория',
      production: 'Production',
      readme: 'Общая',
      telegram: 'Telegram',
      whatsapp: 'WhatsApp',
      monitoring: 'Мониторинг'
    }
  };

  const t = translations[language];

  useEffect(() => {
    fetchDocumentsList();
  }, []);

  const fetchDocumentsList = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/documentation', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch documents');

      const data = await response.json();
      setDocuments(data.documents || []);

      // Auto-select first document
      if (data.documents && data.documents.length > 0) {
        fetchDocumentContent(data.documents[0].filename);
        setSelectedDoc(data.documents[0].filename);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error(t.error);
    }
  };

  const fetchDocumentContent = async (filename) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/documentation/${filename}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch document content');

      const data = await response.json();
      setDocContent(data.content || '');
    } catch (error) {
      console.error('Error fetching document content:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentSelect = (filename) => {
    setSelectedDoc(filename);
    fetchDocumentContent(filename);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      production: '🚀',
      readme: '📖',
      telegram: '✈️',
      whatsapp: '💬',
      monitoring: '📊'
    };
    return icons[category] || '📄';
  };

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f5f7fa' }}>
      {/* Sidebar with document list */}
      <motion.div
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        style={{
          width: '320px',
          backgroundColor: '#fff',
          borderRight: '1px solid #e1e4e8',
          padding: '20px',
          overflowY: 'auto'
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: '24px', color: '#333' }}>
          {t.title}
        </h2>

        {documents.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
            {t.noDocuments}
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {documents.map((doc) => (
              <motion.div
                key={doc.filename}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleDocumentSelect(doc.filename)}
                style={{
                  padding: '16px',
                  backgroundColor: selectedDoc === doc.filename ? '#0366d6' : '#f6f8fa',
                  color: selectedDoc === doc.filename ? '#fff' : '#333',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  border: selectedDoc === doc.filename ? '2px solid #0366d6' : '1px solid #e1e4e8'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '20px' }}>{getCategoryIcon(doc.category)}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ 
                      fontSize: '14px', 
                      fontWeight: '600',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {doc.description}
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      opacity: 0.8,
                      marginTop: '4px'
                    }}>
                      {doc.filename}
                    </div>
                  </div>
                </div>
                <div style={{ 
                  fontSize: '11px', 
                  opacity: 0.7,
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span>{formatFileSize(doc.size)}</span>
                  <span>{new Date(doc.last_modified * 1000).toLocaleDateString()}</span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Main content area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ 
                textAlign: 'center', 
                padding: '40px',
                fontSize: '18px',
                color: '#666'
              }}
            >
              {t.loading}
            </motion.div>
          ) : selectedDoc ? (
            <motion.div
              key={selectedDoc}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              style={{
                backgroundColor: '#fff',
                padding: '40px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                maxWidth: '1200px',
                margin: '0 auto'
              }}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({node, ...props}) => <h1 style={{ fontSize: '32px', marginTop: '0', marginBottom: '24px', color: '#1a202c', borderBottom: '2px solid #e2e8f0', paddingBottom: '8px' }} {...props} />,
                  h2: ({node, ...props}) => <h2 style={{ fontSize: '26px', marginTop: '32px', marginBottom: '16px', color: '#2d3748' }} {...props} />,
                  h3: ({node, ...props}) => <h3 style={{ fontSize: '22px', marginTop: '24px', marginBottom: '12px', color: '#4a5568' }} {...props} />,
                  h4: ({node, ...props}) => <h4 style={{ fontSize: '18px', marginTop: '20px', marginBottom: '10px', color: '#718096' }} {...props} />,
                  p: ({node, ...props}) => <p style={{ fontSize: '16px', lineHeight: '1.6', marginBottom: '16px', color: '#2d3748' }} {...props} />,
                  code: ({node, inline, ...props}) => inline ? 
                    <code style={{ backgroundColor: '#f7fafc', padding: '2px 6px', borderRadius: '4px', fontSize: '14px', color: '#e53e3e', fontFamily: 'monospace' }} {...props} /> :
                    <code style={{ backgroundColor: '#2d3748', color: '#e2e8f0', padding: '16px', borderRadius: '8px', display: 'block', overflow: 'auto', fontSize: '14px', fontFamily: 'monospace', lineHeight: '1.5' }} {...props} />,
                  pre: ({node, ...props}) => <pre style={{ backgroundColor: '#2d3748', padding: '16px', borderRadius: '8px', overflow: 'auto', marginBottom: '16px' }} {...props} />,
                  ul: ({node, ...props}) => <ul style={{ marginBottom: '16px', paddingLeft: '24px' }} {...props} />,
                  ol: ({node, ...props}) => <ol style={{ marginBottom: '16px', paddingLeft: '24px' }} {...props} />,
                  li: ({node, ...props}) => <li style={{ marginBottom: '8px', lineHeight: '1.6' }} {...props} />,
                  blockquote: ({node, ...props}) => <blockquote style={{ borderLeft: '4px solid #cbd5e0', paddingLeft: '16px', marginLeft: '0', marginBottom: '16px', color: '#718096', fontStyle: 'italic' }} {...props} />,
                  table: ({node, ...props}) => <div style={{ overflowX: 'auto', marginBottom: '16px' }}><table style={{ borderCollapse: 'collapse', width: '100%' }} {...props} /></div>,
                  th: ({node, ...props}) => <th style={{ border: '1px solid #e2e8f0', padding: '12px', backgroundColor: '#f7fafc', textAlign: 'left', fontWeight: '600' }} {...props} />,
                  td: ({node, ...props}) => <td style={{ border: '1px solid #e2e8f0', padding: '12px' }} {...props} />,
                  a: ({node, ...props}) => <a style={{ color: '#3182ce', textDecoration: 'underline' }} {...props} />,
                  hr: ({node, ...props}) => <hr style={{ border: 'none', borderTop: '2px solid #e2e8f0', margin: '32px 0' }} {...props} />
                }}
              >
                {docContent}
              </ReactMarkdown>
            </motion.div>
          ) : (
            <motion.div
              key="select"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ 
                textAlign: 'center', 
                padding: '40px',
                fontSize: '18px',
                color: '#666'
              }}
            >
              {t.selectDoc}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Documentation;

