/**
 * IntegrationCard Component
 */

import React, { useState } from 'react';

export const IntegrationCard = ({ integration, onToggle, onTest, onUpdateConfig, isTesting, language = 'ru' }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState({});

  const t = {
    en: { enabled: 'Enabled', disabled: 'Disabled', test: 'Test', testing: 'Testing...', configure: 'Configure', save: 'Save', cancel: 'Cancel', configured: 'Configured', notConfigured: 'Not Configured' },
    ru: { enabled: 'Включено', disabled: 'Отключено', test: 'Тест', testing: 'Тестирование...', configure: 'Настроить', save: 'Сохранить', cancel: 'Отмена', configured: 'Настроено', notConfigured: 'Не настроено' }
  }[language];

  const statusColor = integration.enabled ? '#28a745' : '#6c757d';
  const configColor = integration.configured ? '#17a2b8' : '#ffc107';

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div>
          <h4 style={{ margin: '0 0 5px 0' }}>{integration.name}</h4>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{ padding: '3px 8px', borderRadius: '12px', fontSize: '12px', color: 'white', backgroundColor: statusColor }}>
              {integration.enabled ? t.enabled : t.disabled}
            </span>
            <span style={{ padding: '3px 8px', borderRadius: '12px', fontSize: '12px', color: 'white', backgroundColor: configColor }}>
              {integration.configured ? t.configured : t.notConfigured}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => onToggle(integration.id, !integration.enabled)} style={{ padding: '6px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}>
            {integration.enabled ? t.disabled : t.enabled}
          </button>
          <button onClick={() => onTest(integration.id)} disabled={isTesting} style={{ padding: '6px 12px', backgroundColor: isTesting ? '#ccc' : '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: isTesting ? 'not-allowed' : 'pointer', fontSize: '13px' }}>
            {isTesting ? t.testing : t.test}
          </button>
          <button onClick={() => setShowConfig(!showConfig)} style={{ padding: '6px 12px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}>
            {t.configure}
          </button>
        </div>
      </div>
      {showConfig && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '13px' }}>Configuration:</p>
          <textarea value={JSON.stringify(config, null, 2)} onChange={(e) => { try { setConfig(JSON.parse(e.target.value)); } catch {} }} style={{ width: '100%', minHeight: '100px', padding: '8px', fontSize: '12px', fontFamily: 'monospace', border: '1px solid #ddd', borderRadius: '4px' }} />
          <div style={{ marginTop: '10px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button onClick={() => setShowConfig(false)} style={{ padding: '6px 12px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>{t.cancel}</button>
            <button onClick={() => { onUpdateConfig(integration.id, config); setShowConfig(false); }} style={{ padding: '6px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>{t.save}</button>
          </div>
        </div>
      )}
    </div>
  );
};

