import React, { useEffect, useState } from 'react';
import ImportExport from './components/ImportExport';
import UploadCard from './components/UploadCard';
import ContactList from './components/ContactList';
import ContactEdit from './components/ContactEdit';
import Settings from './components/Settings';

const translations = {
  en: {
    title: 'Business Card CRM',
    home: 'Home',
    settings: 'Settings',
    contacts: 'Contacts',
    upload: 'Upload',
    version: 'Version',
  },
  ru: {
    title: 'CRM визиток',
    home: 'Главная',
    settings: 'Настройки',
    contacts: 'Контакты',
    upload: 'Загрузить',
    version: 'Версия',
  }
};

function App() {
  const [lang, setLang] = useState('ru');
  const [defaultProvider, setDefaultProvider] = useState('auto');
  const [route, setRoute] = useState('home');
  const [editId, setEditId] = useState(null);
  const [ver, setVer] = useState({ version: '', commit: '', message: '' });
  const [ocrProviders, setOcrProviders] = useState([]);
  const t = translations[lang];

  useEffect(() => {
    try {
      const lsLang = localStorage.getItem('app.lang');
      const lsProv = localStorage.getItem('app.defaultProvider');
      if (lsLang) setLang(lsLang);
      if (lsProv) setDefaultProvider(lsProv);
    } catch {}
    
    loadVersion();
    loadOCRProviders();
  }, []);

  const loadVersion = async () => {
    try {
      const res = await fetch('/api/version');
      if (res.ok) {
        setVer(await res.json());
      }
    } catch {}
  };

  const loadOCRProviders = async () => {
    try {
      const res = await fetch('/api/ocr/providers');
      if (res.ok) {
        const data = await res.json();
        setOcrProviders(data.available || []);
      }
    } catch {}
  };

  const handleLangChange = (newLang) => {
    setLang(newLang);
  };

  const handleProviderChange = (newProvider) => {
    setDefaultProvider(newProvider);
  };

  return (
    <div className="container">
      {/* Header */}
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 style={{ margin: 0 }}>{t.title}</h1>
          {ocrProviders.length > 0 && (
            <div style={{ display: 'flex', gap: '4px' }}>
              {ocrProviders.map(provider => (
                <span 
                  key={provider}
                  className="badge success"
                  title={`${provider} ${lang === 'ru' ? 'доступен' : 'available'}`}
                  style={{ fontSize: '10px' }}
                >
                  {provider === 'Tesseract' ? '🔧' : provider === 'Parsio' ? '☁️' : '🌐'}
                </span>
              ))}
            </div>
          )}
        </div>

        <nav>
          <button
            onClick={() => setRoute('home')}
            className={route === 'home' ? '' : 'secondary'}
            disabled={route === 'home'}
          >
            🏠 {t.home}
          </button>
          <button
            onClick={() => setRoute('settings')}
            className={route === 'settings' ? '' : 'secondary'}
            disabled={route === 'settings'}
          >
            ⚙️ {t.settings}
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1 }}>
        {route === 'home' && (
          <div>
            <div className="grid grid-2" style={{ marginBottom: '20px' }}>
              <UploadCard lang={lang} defaultProvider={defaultProvider} />
              <ImportExport />
            </div>
            <ContactList
              lang={lang}
              onEdit={(id) => {
                setEditId(id);
                setRoute('edit');
              }}
            />
          </div>
        )}

        {route === 'settings' && (
          <Settings
            lang={lang}
            defaultProvider={defaultProvider}
            onChangeLang={handleLangChange}
            onChangeProvider={handleProviderChange}
          />
        )}

        {route === 'edit' && (
          <ContactEdit
            id={editId}
            lang={lang}
            onBack={() => setRoute('home')}
          />
        )}
      </main>

      {/* Footer */}
      <footer>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <span style={{ marginRight: '8px' }}>
              {t.version}: <strong>{ver.version || 'n/a'}</strong>
            </span>
            {ver.commit && (
              <span style={{ fontSize: '11px', opacity: 0.7 }}>
                ({ver.commit.slice(0, 7)})
              </span>
            )}
          </div>
          {ver.message && (
            <div style={{ fontSize: '11px', opacity: 0.8 }}>
              {ver.message}
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}

export default App;
