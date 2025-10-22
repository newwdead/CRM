/**
 * ServicesPanel Component
 * Главная панель управления Docker сервисами
 * 
 * Объединяет функциональность ServiceManager + ServiceManagerSimple
 * в модульную архитектуру
 */

import React, { useState } from 'react';
import { useServices } from '../hooks/useServices';
import { ServiceCard } from './ServiceCard';

export const ServicesPanel = ({ language = 'ru' }) => {
  const [logsModal, setLogsModal] = useState(null);
  const [logs, setLogs] = useState('');

  const {
    services,
    loading,
    error,
    restarting,
    stats,
    refresh,
    restart,
    getLogs
  } = useServices(language);

  const translations = {
    en: {
      title: 'Service Management',
      refresh: 'Refresh',
      loading: 'Loading service statuses...',
      errorLoading: 'Error loading services',
      tryAgain: 'Try Again',
      noServices: 'No services found',
      stats: 'Total: {total} | Running: {running} | Stopped: {stopped}',
      logs: 'Logs: {service}',
      close: 'Close',
      loadingLogs: 'Loading logs...'
    },
    ru: {
      title: 'Управление Сервисами',
      refresh: 'Обновить',
      loading: 'Загрузка статусов сервисов...',
      errorLoading: 'Ошибка загрузки сервисов',
      tryAgain: 'Попробовать снова',
      noServices: 'Сервисы не найдены',
      stats: 'Всего: {total} | Работает: {running} | Остановлено: {stopped}',
      logs: 'Логи: {service}',
      close: 'Закрыть',
      loadingLogs: 'Загрузка логов...'
    }
  };

  const t = translations[language];

  const formatStats = (template, values) => {
    return template.replace(/{(\w+)}/g, (match, key) => values[key] || match);
  };

  const handleViewLogs = async (serviceName) => {
    setLogsModal(serviceName);
    setLogs(t.loadingLogs);
    const logsData = await getLogs(serviceName, 100);
    setLogs(logsData || t.errorLoading);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #007bff',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <p style={{ marginTop: '15px', color: '#666' }}>{t.loading}</p>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', color: '#dc3545' }}>
        <h3>{t.errorLoading}</h3>
        <p>{error}</p>
        <button
          onClick={refresh}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            marginTop: '15px'
          }}
        >
          {t.tryAgain}
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h2 style={{ margin: '0 0 5px 0' }}>{t.title}</h2>
          <p style={{
            margin: 0,
            color: '#666',
            fontSize: '14px'
          }}>
            {formatStats(t.stats, stats)}
          </p>
        </div>
        <button
          onClick={refresh}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          {t.refresh}
        </button>
      </div>

      {/* Services Grid */}
      {services.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#666', padding: '50px' }}>
          {t.noServices}
        </p>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
          gap: '15px'
        }}>
          {services.map((service, index) => {
            const serviceName = service.Service || service.Name || service.name;
            return (
              <ServiceCard
                key={index}
                service={service}
                onRestart={restart}
                onViewLogs={handleViewLogs}
                isRestarting={restarting === serviceName}
                language={language}
              />
            );
          })}
        </div>
      )}

      {/* Logs Modal */}
      {logsModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '20px',
            maxWidth: '800px',
            width: '90%',
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '15px'
            }}>
              <h3 style={{ margin: 0 }}>
                {t.logs.replace('{service}', logsModal)}
              </h3>
              <button
                onClick={() => setLogsModal(null)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {t.close}
              </button>
            </div>
            <pre style={{
              flex: 1,
              overflow: 'auto',
              backgroundColor: '#f8f9fa',
              padding: '15px',
              borderRadius: '4px',
              fontSize: '12px',
              fontFamily: 'monospace',
              margin: 0
            }}>
              {logs}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

