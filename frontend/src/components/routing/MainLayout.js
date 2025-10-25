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
 * Enhanced with grouped navigation and dropdown menus in v4.4.0
 */
const MainLayout = ({ children, lang, toggleLanguage, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [ver, setVer] = useState({ version: '', commit: '', message: '' });
  const [actionsOpen, setActionsOpen] = useState(false);

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

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClick = (e) => {
      if (!e.target.closest('.dropdown')) {
        setActionsOpen(false);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const isActionsActive = () => {
    return ['/upload', '/batch-upload', '/import-export'].some(path => 
      location.pathname.startsWith(path)
    );
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
                <span className="logo-tagline">
                  {lang === 'ru' ? 'CRM Визиток' : 'Business Card CRM'}
                </span>
              </div>
            </Link>
          </div>

          <div className="header-right">
            <div className="user-info-compact">
              <span className="user-name">
                {user?.full_name || user?.username}
              </span>
              {user?.is_admin && (
                <span className="badge badge-admin" title={lang === 'ru' ? 'Администратор' : 'Administrator'}>
                  🛡️ {lang === 'ru' ? 'Админ' : 'Admin'}
                </span>
              )}
            </div>
            <button 
              onClick={toggleLanguage} 
              className="btn btn-icon"
              title={lang === 'en' ? 'Switch to Russian' : 'Переключить на English'}
              aria-label="Change language"
            >
              {lang === 'en' ? '🇷🇺' : '🇬🇧'}
            </button>
            <button 
              onClick={onLogout} 
              className="btn btn-icon"
              title={t.logout}
              aria-label="Logout"
            >
              🚪
            </button>
          </div>
        </div>

        {/* Enhanced Navigation with Groups */}
        <nav className="nav" style={{ position: 'relative' }}>
          {/* Home */}
          <Link 
            to="/" 
            className={`nav-btn ${isActive('/') && location.pathname === '/' ? 'active' : ''}`}
            title={lang === 'ru' ? 'Главная страница' : 'Home page'}
          >
            🏠 {t.home}
          </Link>

          {/* Data Section */}
          <Link 
            to="/contacts" 
            className={`nav-btn ${isActive('/contacts') ? 'active' : ''}`}
            title={lang === 'ru' ? 'Список контактов' : 'Contact list'}
          >
            📇 {t.contacts}
          </Link>
          <Link 
            to="/companies" 
            className={`nav-btn ${isActive('/companies') ? 'active' : ''}`}
            title={lang === 'ru' ? 'Список организаций' : 'Company list'}
          >
            🏢 {t.companies || (lang === 'ru' ? 'Организации' : 'Companies')}
          </Link>

          {/* Actions Dropdown */}
          <div className="dropdown">
            <button
              className={`nav-btn dropdown-trigger ${isActionsActive() ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                setActionsOpen(!actionsOpen);
              }}
              title={lang === 'ru' ? 'Действия с визитками' : 'Business card actions'}
            >
              ⚡ {lang === 'ru' ? 'Действия' : 'Actions'} ▾
            </button>
            {actionsOpen && (
              <div className="dropdown-menu" onClick={() => setActionsOpen(false)}>
                <Link 
                  to="/upload" 
                  className={`dropdown-item ${isActive('/upload') ? 'active' : ''}`}
                >
                  📤 {t.uploadCard}
                </Link>
                <Link 
                  to="/batch-upload" 
                  className={`dropdown-item ${isActive('/batch-upload') ? 'active' : ''}`}
                >
                  📦 {lang === 'ru' ? 'Пакетная загрузка' : 'Batch Upload'}
                </Link>
                <Link 
                  to="/import-export" 
                  className={`dropdown-item ${isActive('/import-export') ? 'active' : ''}`}
                >
                  📊 {t.importExport}
                </Link>
              </div>
            )}
          </div>

          {/* Settings */}
          <Link 
            to="/settings" 
            className={`nav-btn ${isActive('/settings') ? 'active' : ''}`}
            title={lang === 'ru' ? 'Мои настройки' : 'My preferences'}
          >
            👤 {lang === 'ru' ? 'Настройки' : 'Preferences'}
          </Link>

          {/* Admin Panel */}
          {user?.is_admin && (
            <Link 
              to="/admin" 
              className={`nav-btn ${isActive('/admin') ? 'active' : ''}`}
              title={lang === 'ru' ? 'Административная панель' : 'Admin panel'}
            >
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
