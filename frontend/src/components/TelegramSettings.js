import React, { useEffect, useState } from 'react';

export default function TelegramSettings({ lang='ru' }){
  const [enabled, setEnabled] = useState(false);
  const [token, setToken] = useState('');
  const [allowed, setAllowed] = useState('');
  const [provider, setProvider] = useState('tesseract');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(()=>{
    const load = async ()=>{
      try {
        setLoading(true);
        const res = await fetch('http://localhost:8000/settings/telegram');
        const data = await res.json();
        setEnabled(!!data.enabled);
        setToken(data.token || '');
        setAllowed(data.allowed_chats || '');
        setProvider(data.provider || 'tesseract');
      } finally {
        setLoading(false);
      }
    };
    load();
  },[]);

  const save = async ()=>{
    try {
      setSaving(true);
      await fetch('http://localhost:8000/settings/telegram', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled, token, allowed_chats: allowed, provider })
      });
      alert(lang==='ru' ? 'Сохранено' : 'Saved');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{paddingTop:10}}>
      <h2>{lang==='ru' ? '🤖 Настройки Telegram' : '🤖 Telegram Settings'}</h2>
      {loading ? (
        <div>{lang==='ru' ? 'Загрузка...' : 'Loading...'}</div>
      ) : (
        <>
          <div style={{display:'grid', gridTemplateColumns:'1fr 2fr', gap:12, maxWidth:700}}>
            <label>{lang==='ru' ? 'Включено' : 'Enabled'}</label>
            <div>
              <input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)} />
            </div>

            <label>Token</label>
            <input value={token} onChange={e=>setToken(e.target.value)} placeholder="123456:ABC-DEF..." />

            <label>{lang==='ru' ? 'Разрешённые чаты (ID через запятую)' : 'Allowed chat IDs (comma-separated)'}</label>
            <input value={allowed} onChange={e=>setAllowed(e.target.value)} placeholder="12345,67890" />

            <label>{lang==='ru' ? 'Провайдер OCR' : 'OCR Provider'}</label>
            <select value={provider} onChange={e=>setProvider(e.target.value)}>
              <option value="tesseract">Tesseract</option>
              <option value="parsio">Parsio</option>
            </select>
          </div>

          <div style={{marginTop:16}}>
            <button onClick={save} disabled={saving}>{lang==='ru' ? 'Сохранить' : 'Save'}</button>
          </div>

          <div style={{marginTop:20, fontSize:14, color:'#555'}}>
            <div style={{marginBottom:6}}>
              {lang==='ru'
                ? 'Чтобы бот присылал фото на распознавание, установите Webhook:'
                : 'To let the bot deliver photos for OCR, set the webhook:'}
            </div>
            <code style={{display:'block', whiteSpace:'pre-wrap'}}>
              {`https://api.telegram.org/bot<TOKEN>/setWebhook?url=<PUBLIC_BASE_URL>/telegram/webhook`}
            </code>
            <div style={{marginTop:6}}>
              {lang==='ru'
                ? 'Важно: нужен публичный адрес. Можете использовать ngrok или любой другой туннель.'
                : 'Note: you need a public URL. Use ngrok or any tunneling solution.'}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
