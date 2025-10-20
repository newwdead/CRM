import React, { useEffect, useState } from 'react';
import LoginPage from './components/LoginPage';
import ImportExport from './components/ImportExport';
import UploadCard from './components/UploadCard';
import ContactList from './components/ContactList';
import ContactEdit from './components/ContactEdit';
import Companies from './components/Companies';
import Settings from './components/Settings';
import AdminPanel from './components/AdminPanel';
import SearchOverlay from './components/SearchOverlay';
import translations from './translations';

function App() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'ru');
  
  const [route, setRoute] = useState('home');
  const [editId, setEditId] = useState(null);
  const [ver, setVer] = useState({ version: '', commit: '', message: '' });
  
  const t = translations[lang];

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        setIsAuthenticated(true);
        
        // Verify token is still valid
        fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => {
          if (!response.ok) {
            // Token expired or invalid
            handleLogout();
          }
        })
        .catch(() => {
          handleLogout();
        });
      } catch (error) {
        handleLogout();
      }
    }
    
    setAuthLoading(false);
  }, []);

  // Fetch version info
  useEffect(() => {
    if (isAuthenticated) {
      fetch('/api/version')
        .then(r => r.json())
        .then(data => setVer(data))
        .catch(err => console.error('Failed to fetch version:', err));
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    setRoute('home');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
    setRoute('home');
  };

  const toggleLanguage = () => {
    const newLang = lang === 'en' ? 'ru' : 'en';
    setLang(newLang);
    localStorage.setItem('lang', newLang);
  };

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontSize: '18px'
      }}>
        Loading...
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} lang={lang} t={t} />;
  }

  // Main application (authenticated)
  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <span className="logo-icon">💼</span>
              <h1>ibbase</h1>
            </div>
            {ver.version && (
              <span className="badge badge-primary version-badge">v{ver.version}</span>
            )}
          </div>

          <div className="header-right">
            <button 
              onClick={toggleLanguage} 
              className="btn btn-secondary lang-btn"
              title={lang === 'en' ? 'Switch to Russian' : 'Переключить на English'}
            >
              🌐 {lang === 'en' ? 'RU' : 'EN'}
            </button>
            <div className="user-info">
              <span className="user-welcome">
                👋 {t.welcome}, <strong>{user?.full_name || user?.username}</strong>
              </span>
              {user?.is_admin && (
                <span className="badge badge-primary">{t.admin}</span>
              )}
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              🚪 {t.logout}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="nav">
          <button
            className={`nav-btn ${route === 'home' ? 'active' : ''}`}
            onClick={() => setRoute('home')}
          >
            🏠 {t.home}
          </button>
          <button
            className={`nav-btn ${route === 'contacts' ? 'active' : ''}`}
            onClick={() => setRoute('contacts')}
          >
            📇 {t.contacts}
          </button>
          <button
            className={`nav-btn ${route === 'companies' ? 'active' : ''}`}
            onClick={() => setRoute('companies')}
          >
            🏢 {t.companies || (lang === 'ru' ? 'Организации' : 'Companies')}
          </button>
          <button
            className={`nav-btn ${route === 'upload' ? 'active' : ''}`}
            onClick={() => setRoute('upload')}
          >
            📤 {t.uploadCard}
          </button>
          <button
            className={`nav-btn ${route === 'import-export' ? 'active' : ''}`}
            onClick={() => setRoute('import-export')}
          >
            📊 {t.importExport}
          </button>
          <button
            className={`nav-btn ${route === 'settings' ? 'active' : ''}`}
            onClick={() => setRoute('settings')}
          >
            ⚙️ {t.settings}
          </button>
          {user?.is_admin && (
            <button
              className={`nav-btn ${route === 'admin' ? 'active' : ''}`}
              onClick={() => setRoute('admin')}
            >
              🛡️ {t.adminPanel}
            </button>
          )}
        </nav>
      </header>

      {/* Main Content */}
      <main className="main">
        {route === 'home' && (
          <div className="home-dashboard">
            <div className="dashboard-header">
              <h2>📊 {t.dashboardTitle}</h2>
              <p>{t.dashboardSubtitle}</p>
            </div>
            
            <div className="dashboard-grid">
              <div className="dashboard-card" onClick={() => setRoute('upload')}>
                <div className="dashboard-icon">📤</div>
                <h3>{t.uploadCard}</h3>
                <p>{t.uploadCardDesc}</p>
              </div>

              <div className="dashboard-card" onClick={() => setRoute('contacts')}>
                <div className="dashboard-icon">📇</div>
                <h3>{t.viewContacts}</h3>
                <p>{t.viewContactsDesc}</p>
              </div>

              <div className="dashboard-card" onClick={() => setRoute('import-export')}>
                <div className="dashboard-icon">📊</div>
                <h3>{t.importExport}</h3>
                <p>{t.importExportDesc}</p>
              </div>

              <div className="dashboard-card" onClick={() => setRoute('settings')}>
                <div className="dashboard-icon">⚙️</div>
                <h3>{t.settings}</h3>
                <p>{t.settingsDesc}</p>
              </div>

              {user?.is_admin && (
                <div className="dashboard-card" onClick={() => setRoute('admin')}>
                  <div className="dashboard-icon">🛡️</div>
                  <h3>{t.adminPanel}</h3>
                  <p>{t.adminPanelDesc}</p>
                </div>
              )}
            </div>

            {ver.message && (
              <div className="dashboard-info">
                <h3>ℹ️ {t.latestUpdate}</h3>
                <p>{ver.message}</p>
              </div>
            )}
          </div>
        )}

        {route === 'contacts' && (
          <ContactList onEdit={(id) => { setEditId(id); setRoute('edit'); }} t={t} lang={lang} />
        )}

        {route === 'companies' && (
          <Companies lang={lang} />
        )}

        {route === 'upload' && (
          <UploadCard t={t} lang={lang} />
        )}

        {route === 'import-export' && (
          <ImportExport t={t} lang={lang} />
        )}

        {route === 'settings' && (
          <Settings t={t} lang={lang} />
        )}

        {route === 'edit' && editId && (
          <ContactEdit id={editId} onBack={() => setRoute('contacts')} t={t} lang={lang} />
        )}

        {route === 'admin' && user?.is_admin && (
          <AdminPanel t={t} lang={lang} />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 ibbase - {t.footerText}</p>
        {ver.version && (
          <p className="text-xs text-secondary">
            {t.version} {ver.version} {ver.commit && `(${ver.commit.substring(0, 7)})`}
          </p>
        )}
      </footer>

      {/* Global Search Overlay (Ctrl+K) */}
      {isAuthenticated && (
        <SearchOverlay 
          lang={lang} 
          onContactSelect={(contactId) => {
            setEditId(contactId);
            setRoute('edit');
          }}
        />
      )}
    </div>
  );
}

export default App;
