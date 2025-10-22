/**
 * ContactFilters Component
 * Панель фильтрации контактов
 */

import React from 'react';

export const ContactFilters = ({
  search,
  companyFilter,
  positionFilter,
  onSearchChange,
  onCompanyChange,
  onPositionChange,
  onReset,
  language = 'ru'
}) => {
  const translations = {
    en: {
      search: 'Search...',
      company: 'Company',
      position: 'Position',
      reset: 'Reset Filters'
    },
    ru: {
      search: 'Поиск...',
      company: 'Компания',
      position: 'Должность',
      reset: 'Сбросить фильтры'
    }
  };

  const t = translations[language];

  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      marginBottom: '20px',
      flexWrap: 'wrap'
    }}>
      {/* Search */}
      <input
        type="text"
        placeholder={t.search}
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        style={{
          flex: '1 1 300px',
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '14px'
        }}
      />

      {/* Company Filter */}
      <input
        type="text"
        placeholder={t.company}
        value={companyFilter}
        onChange={(e) => onCompanyChange(e.target.value)}
        style={{
          flex: '1 1 200px',
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '14px'
        }}
      />

      {/* Position Filter */}
      <input
        type="text"
        placeholder={t.position}
        value={positionFilter}
        onChange={(e) => onPositionChange(e.target.value)}
        style={{
          flex: '1 1 200px',
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '14px'
        }}
      />

      {/* Reset Button */}
      {(search || companyFilter || positionFilter) && (
        <button
          onClick={onReset}
          style={{
            padding: '10px 20px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          {t.reset}
        </button>
      )}
    </div>
  );
};

