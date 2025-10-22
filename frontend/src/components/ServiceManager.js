import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const ServiceManager = () => {
  const [services, setServices] = useState([]);
  const [categorizedServices, setCategorizedServices] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedCategory, setExpandedCategory] = useState('core');
  const [selectedService, setSelectedService] = useState(null);
  const [logs, setLogs] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');

  const translations = {
    en: {
      title: 'Service Management',
      refresh: 'Refresh',
      categories: {
        core: 'Core Services',
        processing: 'Processing',
        monitoring: 'Monitoring',
        other: 'Other'
      },
      status: {
        running: 'Running',
        exited: 'Stopped',
        restarting: 'Restarting',
        unknown: 'Unknown'
      },
      actions: {
        restart: 'Restart',
        logs: 'View Logs',
        close: 'Close'
      },
      stats: {
        total: 'Total Services',
        running: 'Running',
        stopped: 'Stopped'
      },
      messages: {
        restarting: 'Restarting service...',
        restarted: 'Service restarted successfully',
        restartFailed: 'Failed to restart service',
        loadingLogs: 'Loading logs...',
        logsFailed: 'Failed to load logs'
      },
      noServices: 'No services found'
    },
    ru: {
      title: 'Управление Сервисами',
      refresh: 'Обновить',
      categories: {
        core: 'Основные Сервисы',
        processing: 'Обработка',
        monitoring: 'Мониторинг',
        other: 'Прочие'
      },
      status: {
        running: 'Запущен',
        exited: 'Остановлен',
        restarting: 'Перезапуск',
        unknown: 'Неизвестно'
      },
      actions: {
        restart: 'Перезапустить',
        logs: 'Просмотр логов',
        close: 'Закрыть'
      },
      stats: {
        total: 'Всего сервисов',
        running: 'Запущено',
        stopped: 'Остановлено'
      },
      messages: {
        restarting: 'Перезапуск сервиса...',
        restarted: 'Сервис успешно перезапущен',
        restartFailed: 'Не удалось перезапустить сервис',
        loadingLogs: 'Загрузка логов...',
        logsFailed: 'Не удалось загрузить логи'
      },
      noServices: 'Сервисы не найдены'
    }
  };

  const t = translations[language];

  useEffect(() => {
    fetchServicesStatus();
    const interval = setInterval(fetchServicesStatus, 10000); // Auto-refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchServicesStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/services/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch services');

      const data = await response.json();
      setServices(data.services || []);
      setCategorizedServices(data.categorized || {});
    } catch (error) {
      console.error('Error fetching services:', error);
      toast.error('Failed to fetch services');
    } finally {
      setLoading(false);
    }
  };

  const restartService = async (serviceName) => {
    const toastId = toast.loading(t.messages.restarting);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/services/${serviceName}/restart`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to restart service');

      toast.success(t.messages.restarted, { id: toastId });
      
      // Refresh status after 2 seconds
      setTimeout(fetchServicesStatus, 2000);
    } catch (error) {
      console.error('Error restarting service:', error);
      toast.error(t.messages.restartFailed, { id: toastId });
    }
  };

  const viewLogs = async (serviceName) => {
    setSelectedService(serviceName);
    setShowLogs(true);
    setLogs('');

    toast.loading(t.messages.loadingLogs);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/services/${serviceName}/logs?lines=200`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch logs');

      const data = await response.json();
      setLogs(data.logs || '');
      toast.dismiss();
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error(t.messages.logsFailed);
      setLogs('Failed to load logs');
    }
  };

  const getStatusColor = (state) => {
    const stateColors = {
      running: '#28a745',
      exited: '#dc3545',
      restarting: '#ffc107',
      unknown: '#6c757d'
    };
    return stateColors[state.toLowerCase()] || stateColors.unknown;
  };

  const getServiceIcon = (serviceName) => {
    const icons = {
      backend: '⚙️',
      frontend: '🌐',
      db: '🗄️',
      'celery-worker': '⚡',
      redis: '🔴',
      prometheus: '📊',
      grafana: '📈',
      'node-exporter': '💻',
      'postgres-exporter': '🔍',
      cadvisor: '📦'
    };
    return icons[serviceName] || '🔧';
  };

  const totalServices = services.length;
  const runningServices = services.filter(s => s.state.toLowerCase() === 'running').length;
  const stoppedServices = totalServices - runningServices;

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
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
        <h1 style={{ margin: 0, fontSize: '28px', color: '#333' }}>
          {t.title}
        </h1>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={fetchServicesStatus}
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

      {/* Stats Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            backgroundColor: '#fff',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            {t.stats.total}
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#333' }}>
            {totalServices}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            backgroundColor: '#fff',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            {t.stats.running}
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#28a745' }}>
            {runningServices}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            backgroundColor: '#fff',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            {t.stats.stopped}
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#dc3545' }}>
            {stoppedServices}
          </div>
        </motion.div>
      </div>

      {/* Services by Category */}
      {Object.entries(categorizedServices).map(([category, categoryServices]) => {
        if (categoryServices.length === 0) return null;

        return (
          <motion.div
            key={category}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              backgroundColor: '#fff',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '16px',
              overflow: 'hidden'
            }}
          >
            <div
              onClick={() => setExpandedCategory(expandedCategory === category ? null : category)}
              style={{
                padding: '16px 20px',
                backgroundColor: '#f8f9fa',
                borderBottom: '1px solid #e1e4e8',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#e9ecef'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
            >
              <h3 style={{ margin: 0, fontSize: '18px', color: '#333' }}>
                {t.categories[category]} ({categoryServices.length})
              </h3>
              <span style={{ fontSize: '20px' }}>
                {expandedCategory === category ? '▼' : '▶'}
              </span>
            </div>

            <AnimatePresence>
              {expandedCategory === category && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{ padding: '16px' }}>
                    {categoryServices.map((service) => (
                      <motion.div
                        key={service.name}
                        whileHover={{ scale: 1.01 }}
                        style={{
                          padding: '16px',
                          backgroundColor: '#f8f9fa',
                          borderRadius: '6px',
                          marginBottom: '12px',
                          border: '1px solid #e1e4e8'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '24px' }}>{getServiceIcon(service.name)}</span>
                            <div>
                              <div style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>
                                {service.name}
                              </div>
                              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                {service.container}
                              </div>
                            </div>
                          </div>

                          <div style={{ 
                            display: 'inline-block',
                            padding: '6px 12px',
                            backgroundColor: getStatusColor(service.state),
                            color: '#fff',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}>
                            {t.status[service.state.toLowerCase()] || service.state}
                          </div>
                        </div>

                        <div style={{ fontSize: '13px', color: '#666', marginBottom: '12px' }}>
                          {service.status}
                        </div>

                        <div style={{ display: 'flex', gap: '8px' }}>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => restartService(service.name)}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#ffc107',
                              color: '#000',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: '600'
                            }}
                          >
                            🔄 {t.actions.restart}
                          </motion.button>

                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => viewLogs(service.name)}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#6c757d',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: '600'
                            }}
                          >
                            📋 {t.actions.logs}
                          </motion.button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}

      {/* Logs Modal */}
      <AnimatePresence>
        {showLogs && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowLogs(false)}
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
                maxWidth: '1200px',
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
                  Logs: {selectedService}
                </h2>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setShowLogs(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#dc3545',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}
                >
                  {t.actions.close}
                </motion.button>
              </div>

              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '20px',
                backgroundColor: '#1e1e1e',
                fontFamily: 'monospace',
                fontSize: '13px',
                color: '#d4d4d4',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {logs}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ServiceManager;

