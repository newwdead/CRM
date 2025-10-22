/**
 * ContactListContainer Component
 * Главный контейнер для списка контактов
 * Объединяет все компоненты и хуки
 */

import React, { useState } from 'react';
import { useContacts } from '../hooks/useContacts';
import { useContactFilters } from '../hooks/useContactFilters';
import { ContactFilters } from './ContactFilters';
import { ContactActions } from './ContactActions';
import { ContactTable } from './ContactTable';
import { exportContacts } from '../api/contactsApi';
import toast from 'react-hot-toast';

export const ContactListContainer = ({ 
  language = 'ru',
  onViewContact,
  onBulkEditOpen,
  onExportComplete
}) => {
  const [exporting, setExporting] = useState(false);

  // Используем хуки
  const filters = useContactFilters();
  const filterParams = filters.getFilterParams();
  
  const {
    contacts,
    selected,
    loading,
    total,
    pages,
    refresh,
    bulkUpdate,
    bulkDelete,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    selectedCount,
    allSelected
  } = useContacts(filterParams, language);

  const translations = {
    en: {
      title: 'Contacts',
      showing: 'Showing {start}-{end} of {total}',
      exportSuccess: 'Export completed',
      exportError: 'Export failed',
      deleteConfirm: 'Delete {count} contacts?',
      loading: 'Loading...'
    },
    ru: {
      title: 'Контакты',
      showing: 'Показано {start}-{end} из {total}',
      exportSuccess: 'Экспорт завершен',
      exportError: 'Ошибка экспорта',
      deleteConfirm: 'Удалить {count} контактов?',
      loading: 'Загрузка...'
    }
  };

  const t = translations[language];

  // Экспорт
  const handleExport = async () => {
    try {
      setExporting(true);
      const blob = await exportContacts('csv', filterParams);
      
      // Download blob
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contacts_${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(t.exportSuccess);
      if (onExportComplete) onExportComplete();
    } catch (error) {
      console.error('Export error:', error);
      toast.error(t.exportError);
    } finally {
      setExporting(false);
    }
  };

  // Массовое удаление с подтверждением
  const handleBulkDelete = async () => {
    const confirmMessage = t.deleteConfirm.replace('{count}', selectedCount);
    if (window.confirm(confirmMessage)) {
      await bulkDelete();
    }
  };

  // Пагинация
  const start = (filters.page - 1) * filters.limit + 1;
  const end = Math.min(filters.page * filters.limit, total);

  if (loading && contacts.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '50px',
        color: '#666'
      }}>
        {t.loading}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h2 style={{ margin: '0 0 5px 0' }}>{t.title}</h2>
          <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
            {t.showing
              .replace('{start}', start)
              .replace('{end}', end)
              .replace('{total}', total)}
          </p>
        </div>
      </div>

      {/* Filters */}
      <ContactFilters
        search={filters.search}
        companyFilter={filters.companyFilter}
        positionFilter={filters.positionFilter}
        onSearchChange={filters.setSearch}
        onCompanyChange={filters.setCompanyFilter}
        onPositionChange={filters.setPositionFilter}
        onReset={filters.resetFilters}
        language={language}
      />

      {/* Actions */}
      <ContactActions
        selectedCount={selectedCount}
        onBulkEdit={() => onBulkEditOpen && onBulkEditOpen(selected)}
        onBulkDelete={handleBulkDelete}
        onExport={handleExport}
        onRefresh={refresh}
        language={language}
      />

      {/* Table */}
      <ContactTable
        contacts={contacts}
        selected={selected}
        allSelected={allSelected}
        onToggleSelect={toggleSelect}
        onToggleSelectAll={toggleSelectAll}
        onSort={filters.handleSort}
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
        onViewContact={onViewContact}
        language={language}
      />

      {/* Pagination */}
      {pages > 1 && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '10px',
          marginTop: '20px'
        }}>
          <button
            onClick={() => filters.setPage(filters.page - 1)}
            disabled={filters.page === 1}
            style={{
              padding: '8px 16px',
              backgroundColor: filters.page === 1 ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: filters.page === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            ← Previous
          </button>
          <span style={{
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center'
          }}>
            Page {filters.page} of {pages}
          </span>
          <button
            onClick={() => filters.setPage(filters.page + 1)}
            disabled={filters.page === pages}
            style={{
              padding: '8px 16px',
              backgroundColor: filters.page === pages ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: filters.page === pages ? 'not-allowed' : 'pointer'
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

