import React, { useEffect, useState } from 'react';
import ImportExport from './components/ImportExport';
import UploadCard from './components/UploadCard';
import ContactList from './components/ContactList';
import ContactEdit from './components/ContactEdit';
import Settings from './components/Settings';
import Login from './components/Login';
import Register from './components/Register';

const translations = {
  en: {
    title: 'Business Card CRM',
    home: 'Home',
    settings: 'Settings',
    contacts: 'Contacts',
    upload: 'Upload',
    version: 'Version',
    login: 'Login',
    logout: 'Logout',
    register: 'Register',
    profile: 'Profile',
    admin: 'Admin',
    welcome: 'Welcome',
  },
  ru: {
    title: 'CRM визиток',
    home: 'Главная',
    settings: 'Настройки',
    contacts: 'Контакты',
    upload: 'Загрузить',
    version: 'Версия',
    login: 'Вход',
    logout: 'Выход',
    register: 'Регистрация',
    profile: 'Профиль',
    admin: 'Админ',
    welcome: 'Добро пожаловать',
  }
};

function App() {
  const [lang, setLang] = useState('ru');
  const [defaultProvider, setDefaultProvider] = useState('auto');
  const [route, setRoute] = useState('home');
  const [editId, setEditId] = useState(null);
  const [ver, setVer] = useState({ version: '', commit: '', message: '' });
  const [ocrProviders, setOcrProviders] = useState([]);
  
  // Authentication state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  
  const t = translations[lang];

  // Load saved auth on mount
  useEffect(() => {
    try {
      const lsLang = localStorage.getItem('app.lang');
      const lsProv = localStorage.getItem('app.defaultProvider');
      const lsToken = localStorage.getItem('access_token');
      const lsUser = localStorage.getItem('user');
      
      if (lsLang) setLang(lsLang);
      if (lsProv) setDefaultProvider(lsProv);
      
      if (lsToken && lsUser) {
        setToken(lsToken);
        setUser(JSON.parse(lsUser));
        // Verify token is still valid
        verifyToken(lsToken);
      } else {
        setAuthLoading(false);
      }
    } catch {
      setAuthLoading(false);
    }
    
    loadVersion();
    loadOCRProviders();
  }, []);

  const verifyToken = async (tokenToVerify) => {
    try {
      const res = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${tokenToVerify}`
        }
      });
      
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        // Token invalid, clear auth
        handleLogout();
      }
    } catch (err) {
      console.error('Token verification failed:', err);
    } finally {
      setAuthLoading(false);
    }
  };

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

  const handleLogin = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    setShowLogin(false);
    setShowRegister(false);
    // Refresh page data if needed
    loadOCRProviders();
  };

  const handleRegister = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    setShowLogin(false);
    setShowRegister(false);
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setRoute('home');
  };

  const handleSwitchToRegister = () => {
    setShowLogin(false);
    setShowRegister(true);
  };

  const handleSwitchToLogin = () => {
    setShowRegister(false);
    setShowLogin(true);
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
          <div>{lang === 'ru' ? 'Загрузка...' : 'Loading...'}</div>
        </div>
      </div>
    );
  }

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

        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
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

          {/* Auth section */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
            {user ? (
              <>
                <span style={{ 
                  fontSize: '14px', 
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span className={user.is_admin ? 'badge danger' : 'badge info'}>
                    {user.is_admin ? '👑 ' + t.admin : '👤 ' + t.profile}
                  </span>
                  <strong>{user.username}</strong>
                </span>
                <button onClick={handleLogout} className="secondary" style={{ padding: '6px 12px' }}>
                  🚪 {t.logout}
                </button>
              </>
            ) : (
              <>
                <button onClick={() => setShowLogin(true)} style={{ padding: '6px 16px' }}>
                  🔐 {t.login}
                </button>
                <button onClick={() => setShowRegister(true)} className="success" style={{ padding: '6px 16px' }}>
                  📝 {t.register}
                </button>
              </>
            )}
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1 }}>
        {route === 'home' && (
          <div>
            {user && (
              <div className="alert info" style={{ marginBottom: '20px' }}>
                👋 {t.welcome}, <strong>{user.full_name || user.username}</strong>!
                {user.is_admin && (
                  <span style={{ marginLeft: '12px' }}>
                    👑 {lang === 'ru' ? 'Права администратора' : 'Administrator rights'}
                  </span>
                )}
              </div>
            )}
            
            <div className="grid grid-2" style={{ marginBottom: '20px' }}>
              <UploadCard lang={lang} defaultProvider={defaultProvider} />
              <ImportExport lang={lang} />
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

      {/* Auth Modals */}
      {showLogin && (
        <Login
          lang={lang}
          onLogin={handleLogin}
          onSwitchToRegister={handleSwitchToRegister}
        />
      )}

      {showRegister && (
        <Register
          lang={lang}
          onRegister={handleRegister}
          onSwitchToLogin={handleSwitchToLogin}
        />
      )}
    </div>
  );
}

export default App;
