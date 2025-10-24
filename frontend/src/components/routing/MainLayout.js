import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Breadcrumbs from './Breadcrumbs';
import SearchOverlay from '../SearchOverlay';
import KeyboardHint from '../common/KeyboardHint';
import translations from '../../translations';
import logger from '../../utils/logger';

/**
 * Main Layout Component
 * Contains header, navigation, breadcrumbs, and footer
 */
const MainLayout = ({ children, lang, toggleLanguage, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [ver, setVer] = useState({ version: '', commit: '', message: '' });

  const t = translations[lang];

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (error) {
        logger.error('Failed to parse user:', error);
      }
    }

    // Fetch version info
    fetch('/api/version')
      .then(r => r.json())
      .then(data => setVer(data))
      .catch(err => logger.error('Failed to fetch version:', err));
  }, []);

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="logo">
                <span className="logo-icon">💼</span>
                <h1>ibbase</h1>
              </div>
            </Link>
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
            <button onClick={onLogout} className="btn btn-secondary">
              🚪 {t.logout}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="nav">
          <Link to="/" className={`nav-btn ${isActive('/') && location.pathname === '/' ? 'active' : ''}`}>
            🏠 {t.home}
          </Link>
          <Link to="/contacts" className={`nav-btn ${isActive('/contacts') ? 'active' : ''}`}>
            📇 {t.contacts}
          </Link>
          <Link to="/companies" className={`nav-btn ${isActive('/companies') ? 'active' : ''}`}>
            🏢 {t.companies || (lang === 'ru' ? 'Организации' : 'Companies')}
          </Link>
          <Link to="/duplicates" className={`nav-btn ${isActive('/duplicates') ? 'active' : ''}`}>
            🔍 {lang === 'ru' ? 'Дубликаты' : 'Duplicates'}
          </Link>
          <Link to="/upload" className={`nav-btn ${isActive('/upload') ? 'active' : ''}`}>
            📤 {t.uploadCard}
          </Link>
          <Link to="/batch-upload" className={`nav-btn ${isActive('/batch-upload') ? 'active' : ''}`}>
            📦 {lang === 'ru' ? 'Пакетная' : 'Batch'}
          </Link>
          <Link to="/import-export" className={`nav-btn ${isActive('/import-export') ? 'active' : ''}`}>
            📊 {t.importExport}
          </Link>
          <Link to="/settings" className={`nav-btn ${isActive('/settings') ? 'active' : ''}`}>
            ⚙️ {t.settings}
          </Link>
          {user?.is_admin && (
            <Link to="/admin" className={`nav-btn ${isActive('/admin') ? 'active' : ''}`}>
              🛡️ {t.adminPanel}
            </Link>
          )}
        </nav>
      </header>

      {/* Breadcrumbs */}
      <Breadcrumbs lang={lang} />

      {/* Main Content */}
      <main className="main">
        {children}
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
      <SearchOverlay 
        lang={lang} 
        onContactSelect={(contactId) => navigate(`/contacts/${contactId}`)}
      />

      {/* Keyboard Shortcuts Hint */}
      <KeyboardHint 
        shortcuts={[
          { keys: ['Ctrl', 'K'], description: lang === 'ru' ? 'Быстрый поиск' : 'Quick search' },
          { keys: ['Esc'], description: lang === 'ru' ? 'Закрыть модальное окно' : 'Close modal' },
        ]}
      />
    </div>
  );
};

export default MainLayout;

