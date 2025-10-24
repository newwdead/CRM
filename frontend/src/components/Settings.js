import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

/**
 * User Preferences Component
 * Modern UI for personal user settings
 * Redesigned in v4.3.0 with card-based layout, toast notifications, and loading states
 */
export default function Settings({ lang = 'ru', defaultProvider = 'auto', onChangeLang, onChangeProvider }) {
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
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('app.darkMode') === 'true'
  );
  const [tableDensity, setTableDensity] = useState(
    localStorage.getItem('app.tableDensity') || 'comfortable'
  );
  const [dateFormat, setDateFormat] = useState(
    localStorage.getItem('app.dateFormat') || 'DD.MM.YYYY'
  );
  const [itemsPerPage, setItemsPerPage] = useState(
    parseInt(localStorage.getItem('app.itemsPerPage') || '25')
  );
  const [saving, setSaving] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'ru');

  const translations = {
    en: {
      title: 'User Preferences',
      subtitle: 'Personal interface settings. Changes are saved in your browser.',
      interfaceLanguage: 'Interface Language',
      defaultProvider: 'Default OCR Provider',
      auto: 'Auto (recommended)',
      save: 'Save Changes',
      saved: 'Settings saved successfully!',
      notifications: 'Notifications',
      enableNotifications: 'Enable new contact notifications',
      autoRefresh: 'Auto Refresh',
      enableAutoRefresh: 'Automatically refresh contact list',
      refreshInterval: 'Refresh interval (seconds)',
      darkMode: 'Dark Mode',
      enableDarkMode: 'Enable dark theme',
      tableDensity: 'Table Density',
      compact: 'Compact',
      comfortable: 'Comfortable',
      spacious: 'Spacious',
      dateFormat: 'Date Format',
      itemsPerPage: 'Items per page',
      ocrNote: 'OCR provider configuration is available in Admin Panel → Integrations',
      adminNote: 'For system-wide settings, visit Admin Panel → Integrations (admin only)'
    },
    ru: {
      title: 'Мои Настройки',
      subtitle: 'Персональные настройки интерфейса. Изменения сохраняются в вашем браузере.',
      interfaceLanguage: 'Язык интерфейса',
      defaultProvider: 'Провайдер OCR по умолчанию',
      auto: 'Авто (рекомендуется)',
      save: 'Сохранить изменения',
      saved: 'Настройки успешно сохранены!',
      notifications: 'Уведомления',
      enableNotifications: 'Включить уведомления о новых контактах',
      autoRefresh: 'Автообновление',
      enableAutoRefresh: 'Автоматически обновлять список контактов',
      refreshInterval: 'Интервал обновления (секунды)',
      darkMode: 'Темная тема',
      enableDarkMode: 'Включить темную тему',
      tableDensity: 'Плотность таблиц',
      compact: 'Компактная',
      comfortable: 'Комфортная',
      spacious: 'Просторная',
      dateFormat: 'Формат даты',
      itemsPerPage: 'Элементов на странице',
      ocrNote: 'Настройка OCR провайдеров доступна в Админ Панели → Интеграции',
      adminNote: 'Для системных настроек посетите Админ Панель → Интеграции (только для админов)'
    }
  };

  const t = translations[language];

  const handleSave = async () => {
    setSaving(true);
    
    try {
      // Simulate async save (for UX)
      await new Promise(resolve => setTimeout(resolve, 500));
      
      onChangeLang?.(localLang);
      onChangeProvider?.(provider);
      
      localStorage.setItem('app.lang', localLang);
      localStorage.setItem('app.defaultProvider', provider);
      localStorage.setItem('app.notifications', String(notifications));
      localStorage.setItem('app.autoRefresh', String(autoRefresh));
      localStorage.setItem('app.refreshInterval', String(refreshInterval));
      localStorage.setItem('app.darkMode', String(darkMode));
      localStorage.setItem('app.tableDensity', tableDensity);
      localStorage.setItem('app.dateFormat', dateFormat);
      localStorage.setItem('app.itemsPerPage', String(itemsPerPage));
      localStorage.setItem('lang', localLang);
      localStorage.setItem('language', localLang);
      
      // Apply dark mode immediately
      if (darkMode) {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
      
      // Dispatch events for other components
      window.dispatchEvent(new CustomEvent('settings-changed', {
        detail: { darkMode, tableDensity, dateFormat, itemsPerPage }
      }));
      
      toast.success(t.saved, {
        duration: 3000,
        position: 'top-right',
        icon: '✅'
      });
      
      // Trigger refresh if auto-refresh settings changed
      if (autoRefresh) {
        window.dispatchEvent(new Event('settings-changed'));
      }
    } catch (e) {
      console.error('Failed to save settings:', e);
      toast.error(language === 'ru' ? 'Ошибка сохранения настроек' : 'Failed to save settings', {
        duration: 4000,
        position: 'top-right',
        icon: '❌'
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        style={{ marginBottom: '24px' }}
      >
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#333', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span>👤</span>
          {t.title}
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
          {t.subtitle}
        </p>
      </motion.div>

      {/* Settings Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '20px',
        marginBottom: '24px'
      }}>
        {/* Language Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🌐</span>
            {t.interfaceLanguage}
          </h3>
          <select
            value={localLang}
            onChange={(e) => setLocalLang(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              backgroundColor: '#fff',
              cursor: 'pointer',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#2563eb'}
            onBlur={(e) => e.target.style.borderColor = '#e1e4e8'}
          >
            <option value="ru">🇷🇺 Русский</option>
            <option value="en">🇬🇧 English</option>
          </select>
        </motion.div>

        {/* OCR Provider Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🤖</span>
            {t.defaultProvider}
          </h3>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              backgroundColor: '#fff',
              cursor: 'pointer',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#2563eb'}
            onBlur={(e) => e.target.style.borderColor = '#e1e4e8'}
          >
            <option value="auto">{t.auto}</option>
            <option value="tesseract">Tesseract</option>
            <option value="parsio">Parsio</option>
            <option value="google">Google Vision</option>
          </select>
          <div style={{
            marginTop: '12px',
            padding: '10px',
            backgroundColor: '#e7f3ff',
            borderRadius: '6px',
            fontSize: '12px',
            color: '#004085'
          }}>
            ℹ️ {t.ocrNote}
          </div>
        </motion.div>

        {/* Notifications Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.3 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🔔</span>
            {t.notifications}
          </h3>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '12px',
            borderRadius: '6px',
            transition: 'background-color 0.2s',
            userSelect: 'none'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f6f8fa'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <input
              type="checkbox"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              style={{
                width: '20px',
                height: '20px',
                marginRight: '12px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: '#333' }}>
              {t.enableNotifications}
            </span>
          </label>
        </motion.div>

        {/* Auto Refresh Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.4 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🔄</span>
            {t.autoRefresh}
          </h3>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '12px',
            borderRadius: '6px',
            transition: 'background-color 0.2s',
            marginBottom: autoRefresh ? '16px' : '0',
            userSelect: 'none'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f6f8fa'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{
                width: '20px',
                height: '20px',
                marginRight: '12px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: '#333' }}>
              {t.enableAutoRefresh}
            </span>
          </label>

          {autoRefresh && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600', color: '#333' }}>
                {t.refreshInterval}
              </label>
              <input
                type="number"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(parseInt(e.target.value) || 30)}
                min="10"
                max="300"
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '14px',
                  border: '1px solid #e1e4e8',
                  borderRadius: '6px',
                  backgroundColor: '#fff'
                }}
                onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                onBlur={(e) => e.target.style.borderColor = '#e1e4e8'}
              />
            </motion.div>
          )}
        </motion.div>

        {/* Dark Mode Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.5 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🌙</span>
            {t.darkMode}
          </h3>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '12px',
            borderRadius: '6px',
            transition: 'background-color 0.2s',
            userSelect: 'none'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f6f8fa'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <input
              type="checkbox"
              checked={darkMode}
              onChange={(e) => setDarkMode(e.target.checked)}
              style={{
                width: '20px',
                height: '20px',
                marginRight: '12px',
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '14px', color: '#333' }}>
              {t.enableDarkMode}
            </span>
          </label>
          <div style={{
            marginTop: '12px',
            padding: '10px',
            backgroundColor: '#fff3cd',
            borderRadius: '6px',
            fontSize: '12px',
            color: '#856404'
          }}>
            ⚠️ {language === 'ru' ? 'Темная тема будет добавлена в следующем обновлении' : 'Dark theme will be added in the next update'}
          </div>
        </motion.div>

        {/* Table Density Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.6 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>📊</span>
            {t.tableDensity}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {['compact', 'comfortable', 'spacious'].map((density) => (
              <label
                key={density}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  cursor: 'pointer',
                  padding: '12px',
                  borderRadius: '6px',
                  backgroundColor: tableDensity === density ? '#e7f3ff' : 'transparent',
                  border: tableDensity === density ? '2px solid #2563eb' : '2px solid transparent',
                  transition: 'all 0.2s',
                  userSelect: 'none'
                }}
                onMouseEnter={(e) => {
                  if (tableDensity !== density) e.currentTarget.style.backgroundColor = '#f6f8fa';
                }}
                onMouseLeave={(e) => {
                  if (tableDensity !== density) e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <input
                  type="radio"
                  name="tableDensity"
                  value={density}
                  checked={tableDensity === density}
                  onChange={(e) => setTableDensity(e.target.value)}
                  style={{
                    width: '20px',
                    height: '20px',
                    marginRight: '12px',
                    cursor: 'pointer'
                  }}
                />
                <span style={{ fontSize: '14px', color: '#333', fontWeight: tableDensity === density ? '600' : 'normal' }}>
                  {t[density]}
                </span>
              </label>
            ))}
          </div>
        </motion.div>

        {/* Date Format Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.7 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>📅</span>
            {t.dateFormat}
          </h3>
          <select
            value={dateFormat}
            onChange={(e) => setDateFormat(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              backgroundColor: '#fff',
              cursor: 'pointer',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#2563eb'}
            onBlur={(e) => e.target.style.borderColor = '#e1e4e8'}
          >
            <option value="DD.MM.YYYY">DD.MM.YYYY (24.10.2025)</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY (10/24/2025)</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD (2025-10-24)</option>
            <option value="DD MMM YYYY">DD MMM YYYY (24 Oct 2025)</option>
          </select>
        </motion.div>

        {/* Items Per Page Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.8 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '2px solid #e1e4e8'
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>📄</span>
            {t.itemsPerPage}
          </h3>
          <select
            value={itemsPerPage}
            onChange={(e) => setItemsPerPage(parseInt(e.target.value))}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              backgroundColor: '#fff',
              cursor: 'pointer',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#2563eb'}
            onBlur={(e) => e.target.style.borderColor = '#e1e4e8'}
          >
            <option value="10">10</option>
            <option value="25">25 {language === 'ru' ? '(рекомендуется)' : '(recommended)'}</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </motion.div>
      </div>

      {/* Admin Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.5 }}
        style={{
          padding: '16px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeeba',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '14px',
          color: '#856404'
        }}
      >
        <strong>💡 {language === 'ru' ? 'Подсказка:' : 'Tip:'}</strong> {t.adminNote}
      </motion.div>

      {/* Save Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleSave}
        disabled={saving}
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: '16px 32px',
          fontSize: '16px',
          fontWeight: '600',
          color: '#fff',
          backgroundColor: saving ? '#6c757d' : '#2563eb',
          border: 'none',
          borderRadius: '8px',
          cursor: saving ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}
      >
        {saving ? (
          <>
            <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
            {language === 'ru' ? 'Сохранение...' : 'Saving...'}
          </>
        ) : (
          <>
            💾 {t.save}
          </>
        )}
      </motion.button>
    </div>
  );
}
