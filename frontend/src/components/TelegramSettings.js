import React, { useEffect, useState } from 'react';

export default function TelegramSettings({ lang = 'ru' }) {
  const [enabled, setEnabled] = useState(false);
  const [token, setToken] = useState('');
  const [allowed, setAllowed] = useState('');
  const [provider, setProvider] = useState('auto');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [availableProviders, setAvailableProviders] = useState([]);

  const t = lang === 'ru' ? {
    title: '🤖 Настройки Telegram',
    loading: 'Загрузка...',
    enabled: 'Включено',
    token: 'Bot Token',
    tokenPlaceholder: '123456:ABC-DEF...',
    allowedChats: 'Разрешённые чаты',
    allowedChatsPlaceholder: 'ID через запятую: 12345,67890',
    ocrProvider: 'OCR Провайдер',
    auto: 'Авто (рекомендуется)',
    save: 'Сохранить',
    saved: 'Настройки сохранены!',
    webhookTitle: '🔗 Настройка Webhook',
    webhookDesc: 'Для получения фотографий от бота используйте Telegram Polling сервис или настройте webhook вручную:',
    pollingTitle: '🔄 Telegram Polling (рекомендуется)',
    pollingDesc: 'Polling автоматически проверяет обновления и работает даже без публичного адреса.',
    checkStatus: 'Проверить статус',
    startService: 'Запустить сервис',
    stopService: 'Остановить сервис',
    viewLogs: 'Просмотреть логи',
    webhookManual: 'Ручная настройка webhook',
    webhookNote: 'Требуется публичный HTTPS URL. Используйте ngrok или подобное решение.',
    docsLink: 'Документация по настройке',
  } : {
    title: '🤖 Telegram Settings',
    loading: 'Loading...',
    enabled: 'Enabled',
    token: 'Bot Token',
    tokenPlaceholder: '123456:ABC-DEF...',
    allowedChats: 'Allowed Chats',
    allowedChatsPlaceholder: 'Comma-separated IDs: 12345,67890',
    ocrProvider: 'OCR Provider',
    auto: 'Auto (recommended)',
    save: 'Save',
    saved: 'Settings saved!',
    webhookTitle: '🔗 Webhook Setup',
    webhookDesc: 'To receive photos from bot, use Telegram Polling service or set up webhook manually:',
    pollingTitle: '🔄 Telegram Polling (recommended)',
    pollingDesc: 'Polling automatically checks for updates and works without public URL.',
    checkStatus: 'Check Status',
    startService: 'Start Service',
    stopService: 'Stop Service',
    viewLogs: 'View Logs',
    webhookManual: 'Manual webhook setup',
    webhookNote: 'Requires public HTTPS URL. Use ngrok or similar solution.',
    docsLink: 'Setup Documentation',
  };

  useEffect(() => {
    loadSettings();
    loadProviders();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/settings/telegram');
      const data = await res.json();
      setEnabled(!!data.enabled);
      setToken(data.token || '');
      setAllowed(data.allowed_chats || '');
      setProvider(data.provider || 'auto');
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const res = await fetch('/api/ocr/providers');
      if (res.ok) {
        const data = await res.json();
        setAvailableProviders(data.available || []);
      }
    } catch (e) {
      console.error('Failed to load providers:', e);
    }
  };

  const save = async () => {
    try {
      setSaving(true);
      await fetch('/api/settings/telegram', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled, token, allowed_chats: allowed, provider })
      });
      alert(t.saved);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
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
      <h2>{t.title}</h2>

      {/* Main Settings */}
      <div style={{ marginBottom: '20px' }}>
        {/* Enabled */}
        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={enabled}
              onChange={e => setEnabled(e.target.checked)}
            />
            {t.enabled}
          </label>
        </div>

        {/* Token */}
        <div className="form-group">
          <label>{t.token}</label>
          <input
            value={token}
            onChange={e => setToken(e.target.value)}
            placeholder={t.tokenPlaceholder}
            type="password"
            autoComplete="off"
          />
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {lang === 'ru' 
              ? 'Получите токен у @BotFather в Telegram' 
              : 'Get token from @BotFather in Telegram'}
          </div>
        </div>

        {/* Allowed Chats */}
        <div className="form-group">
          <label>{t.allowedChats}</label>
          <input
            value={allowed}
            onChange={e => setAllowed(e.target.value)}
            placeholder={t.allowedChatsPlaceholder}
          />
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {lang === 'ru'
              ? 'Оставьте пустым для разрешения всех чатов (не рекомендуется)'
              : 'Leave empty to allow all chats (not recommended)'}
          </div>
        </div>

        {/* OCR Provider */}
        <div className="form-group">
          <label>{t.ocrProvider}</label>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            style={{ maxWidth: '400px' }}
          >
            <option value="auto">{t.auto}</option>
            <option value="tesseract">Tesseract</option>
            {availableProviders.includes('Parsio') && (
              <option value="parsio">Parsio</option>
            )}
            {availableProviders.includes('Google Vision') && (
              <option value="google">Google Vision</option>
            )}
          </select>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {lang === 'ru'
              ? 'Auto режим автоматически выберет лучший доступный провайдер'
              : 'Auto mode will automatically choose the best available provider'}
          </div>
        </div>

        {/* Save Button */}
        <button onClick={save} disabled={saving} className="success">
          {saving ? (
            <>
              <div className="spinner" style={{
                width: '16px',
                height: '16px',
                display: 'inline-block',
                marginRight: '8px',
                borderWidth: '2px'
              }}></div>
              {t.loading}
            </>
          ) : (
            t.save
          )}
        </button>
      </div>

      {/* Polling Info */}
      <div className="alert info">
        <h4 style={{ marginTop: 0 }}>{t.pollingTitle}</h4>
        <p style={{ marginBottom: '12px' }}>{t.pollingDesc}</p>
        <div style={{ fontSize: '13px' }}>
          <strong>{lang === 'ru' ? 'Команды управления:' : 'Management commands:'}</strong>
          <pre style={{
            backgroundColor: 'var(--bg-color)',
            padding: '12px',
            borderRadius: 'var(--radius)',
            marginTop: '8px',
            fontSize: '12px',
            overflowX: 'auto'
          }}>
{`# ${lang === 'ru' ? 'Проверить статус' : 'Check status'}
sudo systemctl status telegram-polling

# ${lang === 'ru' ? 'Запустить' : 'Start service'}
sudo systemctl start telegram-polling

# ${lang === 'ru' ? 'Остановить' : 'Stop service'}
sudo systemctl stop telegram-polling

# ${lang === 'ru' ? 'Просмотреть логи' : 'View logs'}
sudo journalctl -u telegram-polling -f`}
          </pre>
        </div>
        <a
          href="https://github.com/newwdead/CRM/blob/main/TELEGRAM_SETUP.md"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: 'var(--primary-color)',
            textDecoration: 'none',
            fontSize: '14px',
            fontWeight: 500
          }}
        >
          📖 {t.docsLink} →
        </a>
      </div>

      {/* Webhook Info (Alternative) */}
      <div className="alert warning" style={{ marginTop: '16px' }}>
        <h4 style={{ marginTop: 0 }}>{t.webhookManual}</h4>
        <p style={{ marginBottom: '12px' }}>{t.webhookNote}</p>
        <pre style={{
          backgroundColor: 'var(--bg-color)',
          padding: '12px',
          borderRadius: 'var(--radius)',
          fontSize: '12px',
          overflowX: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all'
        }}>
{`https://api.telegram.org/bot<TOKEN>/setWebhook?url=<PUBLIC_URL>/api/telegram/webhook`}
        </pre>
      </div>
    </div>
  );
}
