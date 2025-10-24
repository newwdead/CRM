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
  const [adminOpen, setAdminOpen] = useState(false);

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
        setAdminOpen(false);
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
    return ['/upload', '/batch-upload', '/import-export', '/duplicates'].some(path => 
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
                setAdminOpen(false);
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
                <div className="dropdown-divider"></div>
                <Link 
                  to="/duplicates" 
                  className={`dropdown-item ${isActive('/duplicates') ? 'active' : ''}`}
                >
                  🔍 {lang === 'ru' ? 'Поиск дубликатов' : 'Find Duplicates'}
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

          {/* Admin Dropdown */}
          {user?.is_admin && (
            <div className="dropdown">
              <button
                className={`nav-btn dropdown-trigger ${isActive('/admin') ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setAdminOpen(!adminOpen);
                  setActionsOpen(false);
                }}
                title={lang === 'ru' ? 'Административная панель' : 'Admin panel'}
              >
                🛡️ {t.adminPanel} ▾
              </button>
              {adminOpen && (
                <div className="dropdown-menu" onClick={() => setAdminOpen(false)}>
                  <Link 
                    to="/admin" 
                    className="dropdown-item"
                  >
                    📊 {lang === 'ru' ? 'Обзор' : 'Overview'}
                  </Link>
                  <div className="dropdown-divider"></div>
                  <div className="dropdown-header">
                    {lang === 'ru' ? 'Управление' : 'Management'}
                  </div>
                  <Link 
                    to="/admin?tab=users" 
                    className="dropdown-item"
                  >
                    👥 {lang === 'ru' ? 'Пользователи' : 'Users'}
                  </Link>
                  <Link 
                    to="/admin?tab=backups" 
                    className="dropdown-item"
                  >
                    💾 {lang === 'ru' ? 'Резервные копии' : 'Backups'}
                  </Link>
                  <div className="dropdown-divider"></div>
                  <div className="dropdown-header">
                    {lang === 'ru' ? 'Система' : 'System'}
                  </div>
                  <Link 
                    to="/admin?tab=settings" 
                    className="dropdown-item"
                  >
                    🔌 {lang === 'ru' ? 'Интеграции' : 'Integrations'}
                  </Link>
                  <Link 
                    to="/admin?tab=services" 
                    className="dropdown-item"
                  >
                    🎛️ {lang === 'ru' ? 'Сервисы' : 'Services'}
                  </Link>
                  <Link 
                    to="/admin?tab=resources" 
                    className="dropdown-item"
                  >
                    🖥️ {lang === 'ru' ? 'Ресурсы' : 'Resources'}
                  </Link>
                </div>
              )}
            </div>
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

      {/* Dropdown Styles */}
      <style jsx="true">{`
        .dropdown {
          position: relative;
          display: inline-block;
        }

        .dropdown-trigger {
          cursor: pointer;
          user-select: none;
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          left: 0;
          margin-top: 8px;
          min-width: 220px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          overflow: hidden;
          animation: slideDown 0.2s ease-out;
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .dropdown-item {
          display: block;
          padding: 10px 16px;
          color: #333;
          text-decoration: none;
          transition: background-color 0.2s;
          font-size: 14px;
        }

        .dropdown-item:hover {
          background-color: #f6f8fa;
        }

        .dropdown-item.active {
          background-color: #e7f3ff;
          color: #2563eb;
          font-weight: 600;
        }

        .dropdown-divider {
          height: 1px;
          background-color: #e1e4e8;
          margin: 6px 0;
        }

        .dropdown-header {
          padding: 8px 16px;
          font-size: 11px;
          font-weight: 700;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
          .dropdown-menu {
            position: fixed;
            left: 16px;
            right: 16px;
            width: auto;
            max-width: none;
          }
        }
      `}</style>
    </div>
  );
};

export default MainLayout;
