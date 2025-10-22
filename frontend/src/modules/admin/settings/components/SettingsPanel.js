/**
 * SettingsPanel Component
 */

import React from 'react';
import { useIntegrations } from '../hooks/useIntegrations';
import { IntegrationCard } from './IntegrationCard';

export const SettingsPanel = ({ language = 'ru' }) => {
  const { integrations, loading, testing, refresh, toggle, test, updateConfig } = useIntegrations(language);

  const t = {
    en: { title: 'System Settings', subtitle: 'Configure integrations and system parameters', refresh: 'Refresh', loading: 'Loading...', noIntegrations: 'No integrations found' },
    ru: { title: 'Системные настройки', subtitle: 'Настройка интеграций и системных параметров', refresh: 'Обновить', loading: 'Загрузка...', noIntegrations: 'Интеграции не найдены' }
  }[language];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px', color: '#666' }}>{t.loading}</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 5px 0' }}>{t.title}</h2>
          <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>{t.subtitle}</p>
        </div>
        <button onClick={refresh} style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
          {t.refresh}
        </button>
      </div>
      {integrations.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#666', padding: '50px' }}>{t.noIntegrations}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '15px' }}>
          {integrations.map((integration) => (
            <IntegrationCard key={integration.id} integration={integration} onToggle={toggle} onTest={test} onUpdateConfig={updateConfig} isTesting={testing === integration.id} language={language} />
          ))}
        </div>
      )}
    </div>
  );
};

