import React, { useEffect, useState } from 'react';

export default function OCRSettings({ lang = 'ru' }) {
  const [providers, setProviders] = useState({ available: [], details: [] });
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState('auto');

  const t = lang === 'ru' ? {
    title: '🔍 Настройка OCR провайдеров',
    loading: 'Загрузка информации о провайдерах...',
    availableProviders: 'Доступные провайдеры',
    defaultProvider: 'Провайдер по умолчанию',
    auto: 'Авто (рекомендуется)',
    autoDesc: 'Система автоматически выберет лучший доступный провайдер',
    save: 'Сохранить',
    saved: 'Настройки сохранены!',
    providerInfo: 'Информация о провайдерах',
    priority: 'Приоритет',
    status: 'Статус',
    available: 'Доступен',
    requiresSetup: 'Требует настройки',
    confidence: 'Точность',
    cost: 'Стоимость',
    speed: 'Скорость',
    howToSetup: 'Как настроить',
    tesseractDesc: 'Локальный OCR, бесплатный, всегда доступен. Средняя точность.',
    parsioDesc: 'Облачный OCR специально для визитных карточек. Высокая точность.',
    googleDesc: 'Google Cloud Vision API. Очень высокая точность распознавания.',
    setupParsio: 'Создайте аккаунт на parsio.io, получите API ключ и добавьте в .env файл',
    setupGoogle: 'Создайте проект в Google Cloud, включите Vision API и добавьте ключ в .env',
    viewDocs: 'Смотреть документацию',
  } : {
    title: '🔍 OCR Provider Settings',
    loading: 'Loading provider information...',
    availableProviders: 'Available Providers',
    defaultProvider: 'Default Provider',
    auto: 'Auto (recommended)',
    autoDesc: 'System will automatically choose the best available provider',
    save: 'Save',
    saved: 'Settings saved!',
    providerInfo: 'Provider Information',
    priority: 'Priority',
    status: 'Status',
    available: 'Available',
    requiresSetup: 'Requires Setup',
    confidence: 'Accuracy',
    cost: 'Cost',
    speed: 'Speed',
    howToSetup: 'How to Setup',
    tesseractDesc: 'Local OCR, free, always available. Medium accuracy.',
    parsioDesc: 'Cloud OCR specialized for business cards. High accuracy.',
    googleDesc: 'Google Cloud Vision API. Very high accuracy.',
    setupParsio: 'Create account on parsio.io, get API key and add to .env file',
    setupGoogle: 'Create project in Google Cloud, enable Vision API and add key to .env',
    viewDocs: 'View Documentation',
  };

  useEffect(() => {
    loadProviders();
    const saved = localStorage.getItem('app.defaultProvider');
    if (saved) setSelectedProvider(saved);
  }, []);

  const loadProviders = async () => {
    try {
      const res = await fetch('/api/ocr/providers');
      if (res.ok) {
        const data = await res.json();
        setProviders(data);
      }
    } catch (e) {
      console.error('Failed to load providers:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    try {
      localStorage.setItem('app.defaultProvider', selectedProvider);
      alert(t.saved);
    } catch (e) {
      console.error('Failed to save:', e);
    }
  };

  const getProviderDetails = (name) => {
    const details = {
      'Tesseract': {
        confidence: '~70%',
        cost: lang === 'ru' ? 'Бесплатно' : 'Free',
        speed: lang === 'ru' ? 'Быстро' : 'Fast',
        desc: t.tesseractDesc,
        setup: '-',
        color: 'info'
      },
      'Parsio': {
        confidence: '~90%',
        cost: lang === 'ru' ? '$19+/мес' : '$19+/mo',
        speed: lang === 'ru' ? 'Средне' : 'Medium',
        desc: t.parsioDesc,
        setup: t.setupParsio,
        color: 'success'
      },
      'Google Vision': {
        confidence: '~95%',
        cost: lang === 'ru' ? '$1.50/1000*' : '$1.50/1000*',
        speed: lang === 'ru' ? 'Быстро' : 'Fast',
        desc: t.googleDesc,
        setup: t.setupGoogle,
        color: 'warning'
      }
    };
    return details[name] || {};
  };

  if (loading) {
    return (
      <div className="card">
        <h2>{t.title}</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '20px' }}>
          <div className="spinner"></div>
          <span>{t.loading}</span>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>{t.title}</h2>

        {/* Default Provider Selection */}
        <div className="form-group">
          <label>{t.defaultProvider}</label>
          <select 
            value={selectedProvider} 
            onChange={(e) => setSelectedProvider(e.target.value)}
            style={{ maxWidth: '400px' }}
          >
            <option value="auto">{t.auto}</option>
            <option value="tesseract">Tesseract</option>
            {providers.available.includes('Parsio') && (
              <option value="parsio">Parsio</option>
            )}
            {providers.available.includes('Google Vision') && (
              <option value="google">Google Vision</option>
            )}
          </select>
          {selectedProvider === 'auto' && (
            <div className="alert info" style={{ marginTop: '12px' }}>
              ℹ️ {t.autoDesc}
            </div>
          )}
        </div>

        <button onClick={handleSave} className="success">
          {t.save}
        </button>
      </div>

      {/* Provider Details Cards */}
      <div className="card">
        <h3>{t.providerInfo}</h3>
        
        <div className="grid grid-3">
          {providers.details.map((provider) => {
            const details = getProviderDetails(provider.name);
            const isAvailable = provider.available;
            
            return (
              <div 
                key={provider.name}
                style={{
                  border: '2px solid var(--border-color)',
                  borderRadius: 'var(--radius)',
                  padding: '16px',
                  backgroundColor: isAvailable ? 'var(--bg-color)' : 'var(--bg-secondary)',
                  opacity: isAvailable ? 1 : 0.7
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0 }}>{provider.name}</h4>
                  <span className={`badge ${isAvailable ? details.color : 'warning'}`}>
                    {isAvailable ? t.available : t.requiresSetup}
                  </span>
                </div>

                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  {details.desc}
                </p>

                <div style={{ fontSize: '13px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{t.priority}:</span>
                    <strong>{provider.priority}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{t.confidence}:</span>
                    <strong>{details.confidence}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{t.cost}:</span>
                    <strong>{details.cost}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{t.speed}:</span>
                    <strong>{details.speed}</strong>
                  </div>
                </div>

                {!isAvailable && details.setup !== '-' && (
                  <div className="alert warning" style={{ marginTop: '12px', fontSize: '12px', padding: '8px' }}>
                    <strong>{t.howToSetup}:</strong><br />
                    {details.setup}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Documentation Link */}
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <a 
            href="https://github.com/newwdead/CRM/blob/main/OCR_PROVIDERS.md" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ 
              color: 'var(--primary-color)', 
              textDecoration: 'none',
              fontSize: '14px',
              fontWeight: 500
            }}
          >
            📖 {t.viewDocs} →
          </a>
        </div>
      </div>
    </div>
  );
}

