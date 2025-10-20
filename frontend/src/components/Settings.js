import React, { useState } from 'react';
import OCRSettings from './OCRSettings';

export default function Settings({ lang = 'ru', defaultProvider = 'auto', onChangeLang, onChangeProvider }) {
  const [activeTab, setActiveTab] = useState('general');

  const t = lang === 'ru' ? {
    title: '⚙️ Настройки',
    generalTab: 'Общие',
    ocrTab: 'OCR Провайдеры',
    interfaceLanguage: 'Язык интерфейса',
    defaultProvider: 'Провайдер OCR по умолчанию',
    auto: 'Авто (рекомендуется)',
    save: 'Сохранить',
    saved: 'Настройки сохранены!',
    hint: 'Подсказка: настройки сохраняются в браузере (localStorage).',
    darkMode: 'Темная тема',
    notifications: 'Уведомления',
    enableNotifications: 'Включить уведомления о новых контактах',
    autoRefresh: 'Автообновление',
    enableAutoRefresh: 'Автоматически обновлять список контактов',
    refreshInterval: 'Интервал обновления (сек)',
  } : {
    title: '⚙️ Settings',
    generalTab: 'General',
    ocrTab: 'OCR Providers',
    interfaceLanguage: 'Interface Language',
    defaultProvider: 'Default OCR Provider',
    auto: 'Auto (recommended)',
    save: 'Save',
    saved: 'Settings saved!',
    hint: 'Note: settings are saved in browser localStorage.',
    darkMode: 'Dark Mode',
    notifications: 'Notifications',
    enableNotifications: 'Enable new contact notifications',
    autoRefresh: 'Auto Refresh',
    enableAutoRefresh: 'Automatically refresh contact list',
    refreshInterval: 'Refresh interval (sec)',
  };

  const [localLang, setLocalLang] = useState(lang);
  const [provider, setProvider] = useState(defaultProvider);
  const [notifications, setNotifications] = useState(
    localStorage.getItem('app.notifications') === 'true'
  );
  const [autoRefresh, setAutoRefresh] = useState(
    localStorage.getItem('app.autoRefresh') === 'true'
  );
  const [refreshInterval, setRefreshInterval] = useState(
    parseInt(localStorage.getItem('app.refreshInterval') || '30')
  );

  const handleSave = () => {
    onChangeLang?.(localLang);
    onChangeProvider?.(provider);
    
    try {
      localStorage.setItem('app.lang', localLang);
      localStorage.setItem('app.defaultProvider', provider);
      localStorage.setItem('app.notifications', String(notifications));
      localStorage.setItem('app.autoRefresh', String(autoRefresh));
      localStorage.setItem('app.refreshInterval', String(refreshInterval));
      
      alert(t.saved);
      
      // Trigger refresh if auto-refresh settings changed
      if (autoRefresh) {
        window.dispatchEvent(new Event('settings-changed'));
      }
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  };

  return (
    <div>
      <div className="card">
        <h2>{t.title}</h2>
        
        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            {t.generalTab}
          </button>
          <button
            className={`tab ${activeTab === 'ocr' ? 'active' : ''}`}
            onClick={() => setActiveTab('ocr')}
          >
            {t.ocrTab}
          </button>
        </div>
        
        <div className="alert info" style={{ marginTop: '16px', marginBottom: '16px' }}>
          ℹ️ {lang === 'ru' ? 'Настройки Telegram теперь доступны в Админ Панели → System Settings' : 'Telegram settings are now available in Admin Panel → System Settings'}
        </div>

        {/* Tab Content */}
        {activeTab === 'general' && (
          <div>
            {/* Language */}
            <div className="form-group">
              <label>{t.interfaceLanguage}</label>
              <select 
                value={localLang} 
                onChange={(e) => setLocalLang(e.target.value)}
                style={{ maxWidth: '300px' }}
              >
                <option value="ru">🇷🇺 Русский</option>
                <option value="en">🇬🇧 English</option>
              </select>
            </div>

            {/* Default Provider */}
            <div className="form-group">
              <label>{t.defaultProvider}</label>
              <select 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)}
                style={{ maxWidth: '300px' }}
              >
                <option value="auto">{t.auto}</option>
                <option value="tesseract">Tesseract</option>
                <option value="parsio">Parsio</option>
                <option value="google">Google Vision</option>
              </select>
            </div>

            {/* Notifications */}
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={notifications}
                  onChange={(e) => setNotifications(e.target.checked)}
                />
                {t.enableNotifications}
              </label>
            </div>

            {/* Auto Refresh */}
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                {t.enableAutoRefresh}
              </label>
            </div>

            {autoRefresh && (
              <div className="form-group" style={{ marginLeft: '28px' }}>
                <label>{t.refreshInterval}</label>
                <input
                  type="number"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(parseInt(e.target.value) || 30)}
                  min="10"
                  max="300"
                  style={{ maxWidth: '150px' }}
                />
              </div>
            )}

            <button onClick={handleSave} className="success">
              {t.save}
            </button>

            <div className="alert info" style={{ marginTop: '16px' }}>
              ℹ️ {t.hint}
            </div>
          </div>
        )}

        {activeTab === 'ocr' && (
          <div>
            <OCRSettings lang={lang} />
          </div>
        )}
      </div>
    </div>
  );
}
