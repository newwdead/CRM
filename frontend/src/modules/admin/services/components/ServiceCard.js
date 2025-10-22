/**
 * ServiceCard Component
 * Карточка отдельного сервиса
 */

import React, { useState } from 'react';

export const ServiceCard = ({
  service,
  onRestart,
  onViewLogs,
  isRestarting,
  language = 'ru'
}) => {
  const [expanded, setExpanded] = useState(false);

  const translations = {
    en: {
      restart: 'Restart',
      restarting: 'Restarting...',
      logs: 'Logs',
      details: 'Details',
      hideDetails: 'Hide Details',
      name: 'Service Name',
      state: 'State',
      status: 'Status',
      ports: 'Ports',
      image: 'Image',
      created: 'Created',
      id: 'Container ID',
      running: 'Running',
      stopped: 'Stopped',
      exited: 'Exited',
      restarting_state: 'Restarting'
    },
    ru: {
      restart: 'Перезапустить',
      restarting: 'Перезапуск...',
      logs: 'Логи',
      details: 'Подробности',
      hideDetails: 'Скрыть',
      name: 'Имя сервиса',
      state: 'Состояние',
      status: 'Статус',
      ports: 'Порты',
      image: 'Образ',
      created: 'Создан',
      id: 'ID контейнера',
      running: 'Работает',
      stopped: 'Остановлен',
      exited: 'Завершен',
      restarting_state: 'Перезапускается'
    }
  };

  const t = translations[language];

  const getStatusColor = (state) => {
    if (!state) return '#6c757d';
    const stateLower = state.toLowerCase();
    if (stateLower.includes('running')) return '#28a745';
    if (stateLower.includes('exited') || stateLower.includes('stopped')) return '#dc3545';
    if (stateLower.includes('restarting')) return '#ffc107';
    return '#6c757d';
  };

  const getStatusText = (state) => {
    if (!state) return t.stopped;
    const stateLower = state.toLowerCase();
    if (stateLower.includes('running')) return t.running;
    if (stateLower.includes('exited')) return t.exited;
    if (stateLower.includes('restarting')) return t.restarting_state;
    return state;
  };

  const serviceName = service.Service || service.Name || service.name;
  const serviceState = service.State || service.state;
  const statusColor = getStatusColor(serviceState);
  const statusText = getStatusText(serviceState);

  return (
    <div style={{
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '15px',
      backgroundColor: '#fff',
      transition: 'box-shadow 0.2s',
      ':hover': {
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '10px'
      }}>
        <div style={{ flex: 1 }}>
          <h4 style={{
            margin: '0 0 5px 0',
            fontSize: '16px',
            fontWeight: 'bold'
          }}>
            {serviceName}
          </h4>
          <div style={{
            display: 'inline-block',
            padding: '3px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: 'white',
            backgroundColor: statusColor
          }}>
            {statusText}
          </div>
        </div>

        {/* Actions */}
        <div style={{
          display: 'flex',
          gap: '8px'
        }}>
          <button
            onClick={() => onRestart(serviceName)}
            disabled={isRestarting}
            style={{
              padding: '6px 12px',
              backgroundColor: isRestarting ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isRestarting ? 'not-allowed' : 'pointer',
              fontSize: '13px'
            }}
          >
            {isRestarting ? t.restarting : t.restart}
          </button>
          <button
            onClick={() => onViewLogs(serviceName)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            {t.logs}
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#f8f9fa',
              color: '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            {expanded ? t.hideDetails : t.details}
          </button>
        </div>
      </div>

      {/* Details */}
      {expanded && (
        <div style={{
          marginTop: '15px',
          padding: '10px',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          fontSize: '13px'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {service.Status && (
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold', width: '30%' }}>{t.status}:</td>
                  <td style={{ padding: '5px' }}>{service.Status}</td>
                </tr>
              )}
              {service.Ports && (
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold' }}>{t.ports}:</td>
                  <td style={{ padding: '5px' }}>{service.Ports}</td>
                </tr>
              )}
              {service.Image && (
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold' }}>{t.image}:</td>
                  <td style={{ padding: '5px', wordBreak: 'break-all' }}>{service.Image}</td>
                </tr>
              )}
              {service.CreatedAt && (
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold' }}>{t.created}:</td>
                  <td style={{ padding: '5px' }}>{service.CreatedAt}</td>
                </tr>
              )}
              {service.ID && (
                <tr>
                  <td style={{ padding: '5px', fontWeight: 'bold' }}>{t.id}:</td>
                  <td style={{ padding: '5px', fontFamily: 'monospace', fontSize: '11px' }}>
                    {service.ID}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

