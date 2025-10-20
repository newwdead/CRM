import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const SystemSettings = () => {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingIntegration, setEditingIntegration] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [checkingStatus, setCheckingStatus] = useState(null);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');

  const translations = {
    en: {
      title: 'System Settings',
      subtitle: 'Configure and manage system integrations',
      refresh: 'Refresh',
      enabled: 'Enabled',
      disabled: 'Disabled',
      configured: 'Configured',
      notConfigured: 'Not Configured',
      checkConnection: 'Test Connection',
      configure: 'Configure',
      cancel: 'Cancel',
      save: 'Save Changes',
      enable: 'Enable',
      disable: 'Disable',
      status: 'Status',
      lastChecked: 'Last checked',
      never: 'Never',
      checking: 'Checking...',
      saving: 'Saving...',
      success: 'Integration updated successfully',
      error: 'Failed to update integration',
      connectionSuccess: 'Connection test successful',
      connectionFailed: 'Connection test failed',
      categories: {
        ocr: 'OCR Recognition',
        telegram: 'Telegram Integration',
        whatsapp: 'WhatsApp Integration',
        auth: 'Authentication',
        backup: 'Backup & Recovery',
        monitoring: 'Monitoring',
        celery: 'Background Tasks',
        redis: 'Cache & Queue'
      },
      descriptions: {
        ocr: 'Business card text recognition using multiple providers',
        telegram: 'Receive business cards via Telegram bot',
        whatsapp: 'Receive business cards via WhatsApp Business',
        auth: 'User authentication and authorization settings',
        backup: 'Automatic database backup configuration',
        monitoring: 'Prometheus and Grafana monitoring',
        celery: 'Asynchronous task processing',
        redis: 'Redis cache and message broker'
      }
    },
    ru: {
      title: 'Системные Настройки',
      subtitle: 'Настройка и управление интеграциями системы',
      refresh: 'Обновить',
      enabled: 'Включено',
      disabled: 'Отключено',
      configured: 'Настроено',
      notConfigured: 'Не настроено',
      checkConnection: 'Проверить',
      configure: 'Настроить',
      cancel: 'Отмена',
      save: 'Сохранить',
      enable: 'Включить',
      disable: 'Отключить',
      status: 'Статус',
      lastChecked: 'Проверено',
      never: 'Никогда',
      checking: 'Проверка...',
      saving: 'Сохранение...',
      success: 'Интеграция успешно обновлена',
      error: 'Не удалось обновить интеграцию',
      connectionSuccess: 'Подключение успешно',
      connectionFailed: 'Ошибка подключения',
      categories: {
        ocr: 'Распознавание OCR',
        telegram: 'Интеграция Telegram',
        whatsapp: 'Интеграция WhatsApp',
        auth: 'Аутентификация',
        backup: 'Резервное копирование',
        monitoring: 'Мониторинг',
        celery: 'Фоновые задачи',
        redis: 'Кеш и очередь'
      },
      descriptions: {
        ocr: 'Распознавание текста с визиток через несколько провайдеров',
        telegram: 'Получение визиток через Telegram бота',
        whatsapp: 'Получение визиток через WhatsApp Business',
        auth: 'Настройки аутентификации и авторизации пользователей',
        backup: 'Автоматическое резервное копирование базы данных',
        monitoring: 'Мониторинг с Prometheus и Grafana',
        celery: 'Асинхронная обработка задач',
        redis: 'Кеш Redis и брокер сообщений'
      }
    }
  };

  const t = translations[language];

  useEffect(() => {
    fetchIntegrationStatus();
  }, []);

  const fetchIntegrationStatus = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/settings/integrations/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch integration status');

      const data = await response.json();
      setIntegrations(data.integrations || []);
    } catch (error) {
      console.error('Error fetching integration status:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const toggleIntegration = async (integration) => {
    const newStatus = !integration.enabled;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/settings/integrations/${integration.id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled: newStatus })
      });

      if (!response.ok) throw new Error('Failed to toggle integration');

      toast.success(newStatus ? `✅ ${t.enabled}` : `⏸️ ${t.disabled}`);
      fetchIntegrationStatus();
    } catch (error) {
      console.error('Error toggling integration:', error);
      toast.error(t.error);
    }
  };

  const checkConnection = async (integration) => {
    setCheckingStatus(integration.id);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/settings/integrations/${integration.id}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        toast.success(`✅ ${t.connectionSuccess}: ${data.message || ''}`);
      } else {
        toast.error(`❌ ${t.connectionFailed}: ${data.error || ''}`);
      }
      
      fetchIntegrationStatus();
    } catch (error) {
      console.error('Error checking connection:', error);
      toast.error(t.connectionFailed);
    } finally {
      setCheckingStatus(null);
    }
  };

  const openEditModal = (integration) => {
    setEditingIntegration(integration);
    setEditForm(integration.config || {});
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/settings/integrations/${editingIntegration.id}/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config: editForm })
      });

      if (!response.ok) throw new Error('Failed to update configuration');

      toast.success(t.success);
      setEditingIntegration(null);
      setEditForm({});
      fetchIntegrationStatus();
    } catch (error) {
      console.error('Error updating configuration:', error);
      toast.error(t.error);
    }
  };

  const getStatusBadge = (integration) => {
    if (!integration.enabled) {
      return { color: '#6c757d', text: t.disabled, icon: '⏸️' };
    }
    if (!integration.configured) {
      return { color: '#ffc107', text: t.notConfigured, icon: '⚠️' };
    }
    if (integration.connection_ok) {
      return { color: '#28a745', text: t.configured, icon: '✅' };
    }
    return { color: '#dc3545', text: 'Error', icon: '❌' };
  };

  const getIntegrationIcon = (id) => {
    const icons = {
      ocr: '🤖',
      telegram: '✈️',
      whatsapp: '💬',
      auth: '🔐',
      backup: '💾',
      monitoring: '📊',
      celery: '⚡',
      redis: '🔴'
    };
    return icons[id] || '⚙️';
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        fontSize: '18px',
        color: '#666'
      }}>
        {t.checking}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#333' }}>
            {t.title}
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
            {t.subtitle}
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={fetchIntegrationStatus}
          style={{
            padding: '10px 20px',
            backgroundColor: '#0366d6',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          🔄 {t.refresh}
        </motion.button>
      </div>

      {/* Integration Cards Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
        gap: '20px'
      }}>
        {integrations.map((integration) => {
          const badge = getStatusBadge(integration);
          
          return (
            <motion.div
              key={integration.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ scale: 1.02 }}
              style={{
                backgroundColor: '#fff',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                border: `2px solid ${integration.enabled ? badge.color : '#e1e4e8'}`,
                transition: 'all 0.2s'
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ fontSize: '32px', marginRight: '12px' }}>
                  {getIntegrationIcon(integration.id)}
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#333' }}>
                    {t.categories[integration.id] || integration.name}
                  </h3>
                  <p style={{ margin: 0, fontSize: '13px', color: '#666', lineHeight: '1.4' }}>
                    {t.descriptions[integration.id] || integration.description}
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                marginBottom: '16px'
              }}>
                <span style={{ 
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  backgroundColor: badge.color,
                  color: '#fff',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: '600'
                }}>
                  {badge.icon} {badge.text}
                </span>
                
                {integration.last_checked && (
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {t.lastChecked}: {new Date(integration.last_checked * 1000).toLocaleString()}
                  </span>
                )}
              </div>

              {/* Configuration Summary */}
              {integration.config_summary && (
                <div style={{ 
                  marginBottom: '16px',
                  padding: '12px',
                  backgroundColor: '#f6f8fa',
                  borderRadius: '6px',
                  fontSize: '13px',
                  color: '#586069'
                }}>
                  {Object.entries(integration.config_summary).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '4px' }}>
                      <strong>{key}:</strong> {String(value).substring(0, 30)}{String(value).length > 30 ? '...' : ''}
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => toggleIntegration(integration)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: integration.enabled ? '#ffc107' : '#28a745',
                    color: integration.enabled ? '#000' : '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600',
                    flex: 1
                  }}
                >
                  {integration.enabled ? `⏸️ ${t.disable}` : `▶️ ${t.enable}`}
                </motion.button>

                {integration.enabled && (
                  <>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => checkConnection(integration)}
                      disabled={checkingStatus === integration.id}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#0366d6',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: checkingStatus === integration.id ? 'not-allowed' : 'pointer',
                        fontSize: '13px',
                        fontWeight: '600',
                        opacity: checkingStatus === integration.id ? 0.6 : 1,
                        flex: 1
                      }}
                    >
                      {checkingStatus === integration.id ? t.checking : `🔍 ${t.checkConnection}`}
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => openEditModal(integration)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#6c757d',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600',
                        flex: 1
                      }}
                    >
                      ⚙️ {t.configure}
                    </motion.button>
                  </>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Edit Configuration Modal */}
      <AnimatePresence>
        {editingIntegration && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setEditingIntegration(null)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: 1000,
              padding: '20px'
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                backgroundColor: '#fff',
                borderRadius: '12px',
                width: '100%',
                maxWidth: '600px',
                maxHeight: '80vh',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
              }}
            >
              <div style={{
                padding: '20px',
                borderBottom: '1px solid #e1e4e8',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <h2 style={{ margin: 0, fontSize: '20px', color: '#333' }}>
                  {getIntegrationIcon(editingIntegration.id)} {t.configure}: {t.categories[editingIntegration.id]}
                </h2>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setEditingIntegration(null)}
                  style={{
                    padding: '8px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ✕
                </motion.button>
              </div>

              <form onSubmit={handleSaveConfig} style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                {/* Configuration fields will be dynamically rendered */}
                {Object.keys(editingIntegration.config || {}).map((key) => (
                  <div key={key} style={{ marginBottom: '16px' }}>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '8px',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#333'
                    }}>
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </label>
                    <input
                      type={key.toLowerCase().includes('password') || key.toLowerCase().includes('token') || key.toLowerCase().includes('key') ? 'password' : 'text'}
                      value={editForm[key] || ''}
                      onChange={(e) => setEditForm({ ...editForm, [key]: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px',
                        border: '1px solid #e1e4e8',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontFamily: key.toLowerCase().includes('password') || key.toLowerCase().includes('token') ? 'monospace' : 'inherit'
                      }}
                      placeholder={`Enter ${key.replace(/_/g, ' ')}`}
                    />
                  </div>
                ))}

                <div style={{ 
                  display: 'flex', 
                  gap: '12px',
                  marginTop: '24px',
                  paddingTop: '20px',
                  borderTop: '1px solid #e1e4e8'
                }}>
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setEditingIntegration(null)}
                    style={{
                      flex: 1,
                      padding: '12px',
                      backgroundColor: '#f6f8fa',
                      color: '#333',
                      border: '1px solid #e1e4e8',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '600'
                    }}
                  >
                    {t.cancel}
                  </motion.button>
                  <motion.button
                    type="submit"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      backgroundColor: '#28a745',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '600'
                    }}
                  >
                    💾 {t.save}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SystemSettings;

