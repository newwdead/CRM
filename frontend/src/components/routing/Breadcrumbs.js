import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

/**
 * Breadcrumbs Component
 * Shows navigation path
 */
const Breadcrumbs = ({ lang = 'ru', contactName = null }) => {
  const location = useLocation();
  const params = useParams();

  const t = {
    en: {
      home: 'Home',
      contacts: 'Contacts',
      companies: 'Organizations',
      duplicates: 'Duplicates',
      upload: 'Upload Card',
      'batch-upload': 'Batch Upload',
      'import-export': 'Import/Export',
      settings: 'Settings',
      admin: 'Admin Panel',
      users: 'Users',
      integrations: 'Integrations',
      services: 'Services',
      documentation: 'Documentation',
      edit: 'Edit'
    },
    ru: {
      home: 'Главная',
      contacts: 'Контакты',
      companies: 'Организации',
      duplicates: 'Дубликаты',
      upload: 'Загрузка визитки',
      'batch-upload': 'Пакетная загрузка',
      'import-export': 'Импорт/Экспорт',
      settings: 'Настройки',
      admin: 'Админ-панель',
      users: 'Пользователи',
      integrations: 'Интеграции',
      services: 'Сервисы',
      documentation: 'Документация',
      edit: 'Редактирование'
    }
  };

  const text = t[lang];

  // Parse path into breadcrumb parts
  const pathParts = location.pathname.split('/').filter(Boolean);
  
  // Don't show breadcrumbs on home or login page
  if (pathParts.length === 0 || location.pathname === '/login') {
    return null;
  }

  const breadcrumbs = [
    { path: '/', label: text.home }
  ];

  let currentPath = '';
  pathParts.forEach((part, index) => {
    currentPath += `/${part}`;
    
    // Skip if it's a parameter (UUID, ID, etc.)
    if (part.match(/^[a-f0-9-]{32,36}$/i) || part.match(/^\d+$/)) {
      if (contactName) {
        breadcrumbs.push({ path: currentPath, label: contactName, isLast: index === pathParts.length - 1 });
      }
      return;
    }

    const label = text[part] || part;
    breadcrumbs.push({ 
      path: currentPath, 
      label, 
      isLast: index === pathParts.length - 1 
    });
  });

  return (
    <div style={{
      padding: '12px 20px',
      backgroundColor: '#f9fafb',
      borderBottom: '1px solid #e5e7eb',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '14px',
      color: '#6b7280'
    }}>
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.path}>
          {index > 0 && <span style={{ color: '#d1d5db' }}>›</span>}
          {crumb.isLast ? (
            <span style={{ 
              color: '#111827',
              fontWeight: '500'
            }}>
              {crumb.label}
            </span>
          ) : (
            <Link 
              to={crumb.path}
              style={{
                color: '#4f46e5',
                textDecoration: 'none',
                transition: 'color 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.color = '#6366f1'}
              onMouseLeave={(e) => e.target.style.color = '#4f46e5'}
            >
              {crumb.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default Breadcrumbs;

