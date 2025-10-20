import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Page Title Component
 * Updates document.title based on current route
 */
const PageTitle = ({ title, lang = 'ru' }) => {
  const location = useLocation();

  const defaultTitles = {
    '/': lang === 'ru' ? 'Главная' : 'Home',
    '/contacts': lang === 'ru' ? 'Контакты' : 'Contacts',
    '/companies': lang === 'ru' ? 'Организации' : 'Organizations',
    '/duplicates': lang === 'ru' ? 'Дубликаты' : 'Duplicates',
    '/upload': lang === 'ru' ? 'Загрузка визитки' : 'Upload Card',
    '/batch-upload': lang === 'ru' ? 'Пакетная загрузка' : 'Batch Upload',
    '/import-export': lang === 'ru' ? 'Импорт/Экспорт' : 'Import/Export',
    '/settings': lang === 'ru' ? 'Настройки' : 'Settings',
    '/admin': lang === 'ru' ? 'Админ-панель' : 'Admin Panel'
  };

  useEffect(() => {
    const pageTitle = title || defaultTitles[location.pathname] || 'ibbase';
    document.title = `${pageTitle} - ibbase`;

    // Set meta description
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.content = lang === 'ru' 
        ? 'ibbase - Система управления визитками и контактами'
        : 'ibbase - Business Card and Contact Management System';
    }
  }, [title, location.pathname, lang, defaultTitles]);

  return null;
};

export default PageTitle;

