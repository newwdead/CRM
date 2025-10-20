import React, { useEffect, useState } from 'react';
import ContactCard from './ContactCard';
import { ContactListSkeleton } from './SkeletonLoader';
import TableSettings from './TableSettings';
import { Tooltip } from 'react-tooltip';
import toast from 'react-hot-toast';

export default function ContactList({ lang = 'ru', onEdit }) {
  const [contacts, setContacts] = useState([]);
  const [selected, setSelected] = useState([]);
  const [showBulkEdit, setShowBulkEdit] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Image Modal State
  const [viewingImage, setViewingImage] = useState(null);
  
  // Contact Card Modal State
  const [viewingContact, setViewingContact] = useState(null);
  
  // Pagination States
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  
  // Search & Filter States
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);
  
  const [newContact, setNewContact] = useState({
    full_name: '', company: '', position: '', email: '',
    phone: '', address: '', comment: '', website: ''
  });
  const [showNewContact, setShowNewContact] = useState(false);
  const [stats, setStats] = useState({ total: 0, withEmail: 0, withPhone: 0 });
  
  // Table Settings State
  const [showTableSettings, setShowTableSettings] = useState(false);
  const [tableColumns, setTableColumns] = useState(() => {
    // Try to load from localStorage
    const saved = localStorage.getItem('table_columns');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse table columns:', e);
      }
    }
    
    // Default columns configuration
    return [
      { key: 'select', label: '☑️', visible: true, order: 0, width: '40' },
      { key: 'number', label: '№', visible: true, order: 1, width: '50' },
      { key: 'uid', label: lang === 'ru' ? 'UID' : 'UID', visible: true, order: 2, width: 'auto' },
      { key: 'name', label: lang === 'ru' ? 'Имя' : 'Name', visible: true, order: 3, width: 'auto' },
      { key: 'company', label: lang === 'ru' ? 'Компания' : 'Company', visible: true, order: 4, width: 'auto' },
      { key: 'position', label: lang === 'ru' ? 'Должность' : 'Position', visible: true, order: 5, width: 'auto' },
      { key: 'email', label: 'Email', visible: true, order: 6, width: 'auto' },
      { key: 'phone', label: lang === 'ru' ? 'Телефон' : 'Phone', visible: true, order: 7, width: 'auto' },
      { key: 'address', label: lang === 'ru' ? 'Адрес' : 'Address', visible: false, order: 8, width: 'auto' },
      { key: 'website', label: lang === 'ru' ? 'Сайт' : 'Website', visible: false, order: 9, width: 'auto' },
      { key: 'comment', label: lang === 'ru' ? 'Комментарий' : 'Comment', visible: false, order: 10, width: 'auto' },
      { key: 'photo', label: lang === 'ru' ? 'Фото' : 'Photo', visible: true, order: 11, width: 'auto' },
      { key: 'actions', label: lang === 'ru' ? 'Действия' : 'Actions', visible: true, order: 12, width: 'auto' },
    ];
  });

  const t = lang === 'ru' ? {
    contacts: 'Контакты',
    search: 'Поиск...',
    uid: 'UID',
    delete: 'Удалить выбранные',
    bulkEdit: 'Массовое редактирование',
    exportCSV: 'Экспорт CSV',
    exportXLSX: 'Экспорт XLSX',
    addNew: 'Добавить контакт',
    actions: 'Действия',
    name: 'Имя',
    company: 'Компания',
    position: 'Должность',
    email: 'Email',
    phone: 'Телефон',
    address: 'Адрес',
    website: 'Сайт',
    comment: 'Комментарий',
    photo: 'Фото',
    edit: 'Редактировать',
    copy: 'Скопировать',
    apply: 'Применить',
    cancel: 'Отмена',
    create: 'Создать',
    selectAll: 'Выбрать все',
    deselectAll: 'Снять выбор',
    selected: 'Выбрано',
    total: 'Всего',
    withEmail: 'С email',
    withPhone: 'С телефоном',
    confirmDelete: 'Удалить выбранные контакты?',
    nothingSelected: 'Ничего не выбрано',
    fillAtLeastOne: 'Заполните хотя бы одно поле',
    advancedFilters: 'Расширенные фильтры',
    hideFilters: 'Скрыть фильтры',
    clearFilters: 'Очистить фильтры',
    filterByCompany: 'Фильтр по компании',
    filterByPosition: 'Фильтр по должности',
    sortBy: 'Сортировка',
    sortOrder: 'Порядок',
    ascending: 'По возрастанию',
    descending: 'По убыванию',
  } : {
    contacts: 'Contacts',
    search: 'Search...',
    uid: 'UID',
    delete: 'Delete Selected',
    bulkEdit: 'Bulk Edit',
    exportCSV: 'Export CSV',
    exportXLSX: 'Export XLSX',
    addNew: 'Add Contact',
    actions: 'Actions',
    name: 'Name',
    company: 'Company',
    position: 'Position',
    email: 'Email',
    phone: 'Phone',
    address: 'Address',
    website: 'Website',
    comment: 'Comment',
    photo: 'Photo',
    edit: 'Edit',
    copy: 'Copy',
    apply: 'Apply',
    cancel: 'Cancel',
    create: 'Create',
    selectAll: 'Select All',
    deselectAll: 'Deselect All',
    selected: 'Selected',
    total: 'Total',
    withEmail: 'With Email',
    withPhone: 'With Phone',
    confirmDelete: 'Delete selected contacts?',
    nothingSelected: 'Nothing selected',
    fillAtLeastOne: 'Fill at least one field',
    advancedFilters: 'Advanced Filters',
    hideFilters: 'Hide Filters',
    clearFilters: 'Clear Filters',
    filterByCompany: 'Filter by Company',
    filterByPosition: 'Filter by Position',
    sortBy: 'Sort By',
    sortOrder: 'Sort Order',
    ascending: 'Ascending',
    descending: 'Descending',
  };

  const load = async () => {
    try {
      setLoading(true);
      
      // Build query params
      const params = new URLSearchParams();
      if (search) params.append('q', search);
      if (companyFilter) params.append('company', companyFilter);
      if (positionFilter) params.append('position', positionFilter);
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      params.append('page', page.toString());
      params.append('limit', limit.toString());

      const token = localStorage.getItem('token');
      const res = await fetch(`/api/contacts/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!res.ok) {
        console.error('Failed to load contacts:', res.status);
        toast.error(lang === 'ru' ? 'Ошибка загрузки контактов' : 'Failed to load contacts');
        return;
      }
      
    const data = await res.json();
      
      // Handle paginated response
      setContacts(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
      
      // Calculate stats
      setStats({
        total: data.total || 0,
        withEmail: (data.items || []).filter(c => c.email).length,
        withPhone: (data.items || []).filter(c => c.phone).length
      });
    } catch (error) {
      console.error('Error loading contacts:', error);
      toast.error(lang === 'ru' ? 'Ошибка загрузки' : 'Loading error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [search, companyFilter, positionFilter, sortBy, sortOrder, page]);
  
  // Reset to page 1 when filters change
  useEffect(() => {
    if (page !== 1) setPage(1);
  }, [search, companyFilter, positionFilter, sortBy, sortOrder]);

  useEffect(() => {
    const handler = () => load();
    window.addEventListener('refresh-contacts', handler);
    return () => window.removeEventListener('refresh-contacts', handler);
  }, []);

  const clearFilters = () => {
    setSearch('');
    setCompanyFilter('');
    setPositionFilter('');
    setSortBy('id');
    setSortOrder('desc');
  };

  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  const toggleAll = () => {
    if (selected.length === contacts.length) {
      setSelected([]);
    } else {
      setSelected(contacts.map(c => c.id));
    }
  };

  const exportSelected = async (format = 'csv') => {
    if (!selected.length) return alert(t.nothingSelected);
    const ids = selected.join(',');
    const url = format === 'xlsx'
      ? `/api/contacts/export/xlsx?ids=${encodeURIComponent(ids)}`
      : `/api/contacts/export?ids=${encodeURIComponent(ids)}`;
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement('a');
      const href = window.URL.createObjectURL(blob);
      a.href = href;
      a.download = format === 'xlsx' ? 'contacts.xlsx' : 'contacts.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(href);
    } catch (e) {
      alert('Export failed');
    }
  };

  const deleteSelected = async () => {
    if (!selected.length) return alert(t.nothingSelected);
    if (!window.confirm(`${t.confirmDelete} (${selected.length})`)) return;
    
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    await fetch('/api/contacts/delete_bulk', {
      method: 'POST',
      headers,
      body: JSON.stringify(selected)
    });
    setSelected([]);
    await load();
  };

  const applyBulkEdit = async () => {
    const fields = Object.fromEntries(
      Object.entries(bulkEditData).filter(([k, v]) => v && v.trim() !== '')
    );
    if (!Object.keys(fields).length) return alert(t.fillAtLeastOne);
    
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    await fetch('/api/contacts/update_bulk', {
      method: 'PUT',
      headers,
      body: JSON.stringify({ ids: selected, fields })
    });
    setSelected([]);
    setShowBulkEdit(false);
    setBulkEditData({});
    await load();
  };

  const createNew = async () => {
    const empty = Object.values(newContact).every(v => !v);
    if (empty) return alert(t.fillAtLeastOne);
    
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      const res = await fetch('/api/contacts/', {
        method: 'POST',
        headers,
        body: JSON.stringify(newContact)
      });
      
      if (!res.ok) {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Failed to create contact'}`);
        return;
      }
      
      setNewContact({
        full_name: '', company: '', position: '', email: '',
        phone: '', address: '', comment: '', website: ''
      });
      setShowNewContact(false);
      await load();
    } catch (error) {
      console.error('Error creating contact:', error);
      alert('Network error. Please try again.');
    }
  };

  // Handle table settings save
  const handleSaveTableSettings = (newColumns) => {
    setTableColumns(newColumns);
    localStorage.setItem('table_columns', JSON.stringify(newColumns));
  };

  // Get visible columns sorted by order
  const visibleColumns = tableColumns
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order);

  // Show skeleton while loading
  if (loading) {
    return <ContactListSkeleton rows={limit} />;
  }

  return (
    <div className="card">
      <Tooltip id="contact-tooltip" />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>📇 {t.contacts}</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge info">{t.total}: {stats.total}</span>
          <span className="badge success">{t.withEmail}: {stats.withEmail}</span>
          <span className="badge warning">{t.withPhone}: {stats.withPhone}</span>
        </div>
      </div>

      {/* Search & Filter */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <input
          placeholder={`🔍 ${t.search}`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: '200px' }}
        />
        <button 
          onClick={() => setShowTableSettings(true)}
          className="secondary"
          title={lang === 'ru' ? 'Настройка таблицы' : 'Table Settings'}
        >
          ⚙️ {lang === 'ru' ? 'Таблица' : 'Table'}
        </button>
        <button 
          onClick={() => setShowFilters(!showFilters)}
          className="secondary"
        >
          {showFilters ? '🔽 ' + t.hideFilters : '🔼 ' + t.advancedFilters}
        </button>
        {(search || companyFilter || positionFilter) && (
          <button onClick={clearFilters} className="secondary">
            ✖️ {t.clearFilters}
          </button>
        )}
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="alert info" style={{ marginBottom: '16px' }}>
          <h4 style={{ marginTop: 0, marginBottom: '16px' }}>🎯 {t.advancedFilters}</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            <div className="form-group">
              <label>{t.filterByCompany}</label>
              <input
                placeholder={t.company}
                value={companyFilter}
                onChange={(e) => setCompanyFilter(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>{t.filterByPosition}</label>
              <input
                placeholder={t.position}
                value={positionFilter}
                onChange={(e) => setPositionFilter(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>{t.sortBy}</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="id">ID</option>
                <option value="full_name">{t.name}</option>
                <option value="company">{t.company}</option>
                <option value="position">{t.position}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t.sortOrder}</label>
              <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
                <option value="desc">{t.descending}</option>
                <option value="asc">{t.ascending}</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button onClick={() => setShowNewContact(!showNewContact)} className="success">
          ➕ {t.addNew}
        </button>
        <button onClick={toggleAll} className="secondary">
          {selected.length === contacts.length ? '☑️ ' + t.deselectAll : '☐ ' + t.selectAll}
        </button>
        {selected.length > 0 && (
          <>
            <span className="badge info" style={{ padding: '10px 16px' }}>
              {t.selected}: {selected.length}
            </span>
            <button onClick={() => setShowBulkEdit(!showBulkEdit)}>
              ✏️ {t.bulkEdit}
            </button>
            <button onClick={deleteSelected} className="danger">
              🗑️ {t.delete}
            </button>
            <button onClick={() => exportSelected('csv')} className="secondary">
              ⬇️ {t.exportCSV}
            </button>
            <button onClick={() => exportSelected('xlsx')} className="secondary">
              📊 {t.exportXLSX}
            </button>
          </>
        )}
      </div>

      {/* Bulk Edit Form */}
      {showBulkEdit && (
        <div className="alert info" style={{ marginBottom: '16px' }}>
          <h4 style={{ marginTop: 0 }}>
            ✏️ {t.bulkEdit} ({selected.length} {t.contacts.toLowerCase()})
          </h4>
          <div className="grid grid-2">
            {['company', 'position', 'email', 'phone', 'address', 'website', 'comment'].map(field => (
              <div key={field} className="form-group">
                <label>{t[field] || field}</label>
                <input
                  placeholder={t[field] || field}
                  onChange={(e) => setBulkEditData({ ...bulkEditData, [field]: e.target.value })}
                />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={applyBulkEdit} className="success">
              {t.apply}
            </button>
            <button onClick={() => setShowBulkEdit(false)} className="secondary">
              {t.cancel}
            </button>
          </div>
        </div>
      )}

      {/* New Contact Form */}
      {showNewContact && (
        <div className="alert success" style={{ marginBottom: '16px' }}>
          <h4 style={{ marginTop: 0 }}>➕ {t.addNew}</h4>
          <div className="grid grid-2">
            <div className="form-group">
              <label>{t.name}</label>
              <input
                value={newContact.full_name}
                onChange={(e) => setNewContact({ ...newContact, full_name: e.target.value })}
                placeholder={t.name}
              />
            </div>
            <div className="form-group">
              <label>{t.company}</label>
              <input
                value={newContact.company}
                onChange={(e) => setNewContact({ ...newContact, company: e.target.value })}
                placeholder={t.company}
              />
            </div>
            <div className="form-group">
              <label>{t.position}</label>
              <input
                value={newContact.position}
                onChange={(e) => setNewContact({ ...newContact, position: e.target.value })}
                placeholder={t.position}
              />
            </div>
            <div className="form-group">
              <label>{t.email}</label>
              <input
                value={newContact.email}
                onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                placeholder={t.email}
                type="email"
              />
            </div>
            <div className="form-group">
              <label>{t.phone}</label>
              <input
                value={newContact.phone}
                onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                placeholder={t.phone}
              />
            </div>
            <div className="form-group">
              <label>{t.website}</label>
              <input
                value={newContact.website}
                onChange={(e) => setNewContact({ ...newContact, website: e.target.value })}
                placeholder={t.website}
                type="url"
              />
            </div>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>{t.address}</label>
              <input
                value={newContact.address}
                onChange={(e) => setNewContact({ ...newContact, address: e.target.value })}
                placeholder={t.address}
              />
            </div>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>{t.comment}</label>
              <textarea
                value={newContact.comment}
                onChange={(e) => setNewContact({ ...newContact, comment: e.target.value })}
                placeholder={t.comment}
                rows="3"
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={createNew} className="success">
              {t.create}
            </button>
            <button onClick={() => setShowNewContact(false)} className="secondary">
              {t.cancel}
            </button>
          </div>
        </div>
      )}

      {/* Contacts Table */}
      <div style={{ overflowX: 'auto' }}>
        <table>
        <thead>
            <tr>
              <th style={{ width: '40px' }}>
                <input
                  type="checkbox"
                  checked={selected.length === contacts.length && contacts.length > 0}
                  onChange={toggleAll}
                />
              </th>
              <th style={{ width: '50px' }}>№</th>
              <th>{t.uid}</th>
              <th>{t.name}</th>
              <th>{t.company}</th>
              <th>{t.position}</th>
              <th>{t.email}</th>
              <th>{t.phone}</th>
              <th>{t.address}</th>
              <th>{t.website}</th>
              <th>{t.comment}</th>
              <th>{t.photo}</th>
              <th>{t.actions}</th>
            </tr>
        </thead>
        <tbody>
            {contacts.length === 0 ? (
              <tr>
                <td colSpan="14" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                  {search || companyFilter || positionFilter ? '🔍 ' + (lang === 'ru' ? 'Ничего не найдено' : 'Nothing found') : '📭 ' + (lang === 'ru' ? 'Нет контактов' : 'No contacts')}
                </td>
              </tr>
            ) : (
              contacts.map((c, index) => (
                <tr 
                  key={c.id}
                  onClick={() => setViewingContact(c.id)}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selected.includes(c.id)}
                      onChange={() => toggle(c.id)}
                    />
                  </td>
                  <td style={{ textAlign: 'center', color: '#999' }}>
                    {(page - 1) * limit + index + 1}
                  </td>
                  <td>
                    {c.uid ? (
                      <code style={{ fontSize: '11px', color: '#666' }}>{c.uid.slice(0, 8)}</code>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    <strong>
                      {c.last_name || c.first_name ? (
                        `${c.last_name || ''} ${c.first_name || ''} ${c.middle_name || ''}`.trim()
                      ) : (
                        c.full_name || '—'
                      )}
                    </strong>
                  </td>
                  <td>{c.company || '—'}</td>
                  <td>{c.position || '—'}</td>
                  <td>
                    {c.email ? (
                      <a href={`mailto:${c.email}`} style={{ color: 'var(--primary-color)' }}>
                        {c.email}
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    {c.phone ? (
                      <a href={`tel:${c.phone}`} style={{ color: 'var(--primary-color)' }}>
                        {c.phone}
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>{c.address || '—'}</td>
                  <td>
                    {c.website ? (
                      <a
                        href={c.website}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: 'var(--primary-color)' }}
                      >
                        🔗
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {c.comment || '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                {c.photo_path ? (
                      <img
                        src={`/files/${c.thumbnail_path || c.photo_path}`}
                        alt="Thumbnail"
                        onClick={(e) => {
                          e.stopPropagation();
                          setViewingImage(c.photo_path);
                        }}
                        style={{
                          width: '40px',
                          height: '40px',
                          objectFit: 'cover',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          border: '1px solid #ddd'
                        }}
                        title={t.photo}
                      />
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit?.(c.id);
                      }} 
                      className="secondary" 
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      {t.edit}
                    </button>
              </td>
            </tr>
              ))
            )}
        </tbody>
      </table>
      </div>
      
      {/* Pagination */}
      {pages > 1 && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '10px',
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <button
            onClick={() => setPage(1)}
            disabled={page === 1}
            style={{
              padding: '6px 12px',
              fontSize: '14px',
              cursor: page === 1 ? 'not-allowed' : 'pointer',
              opacity: page === 1 ? 0.5 : 1
            }}
          >
            ⏮️ {lang === 'ru' ? 'Первая' : 'First'}
          </button>
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            style={{
              padding: '6px 12px',
              fontSize: '14px',
              cursor: page === 1 ? 'not-allowed' : 'pointer',
              opacity: page === 1 ? 0.5 : 1
            }}
          >
            ◀️ {lang === 'ru' ? 'Назад' : 'Previous'}
          </button>
          <span style={{
            padding: '0 15px',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            {lang === 'ru' ? 'Страница' : 'Page'} {page} {lang === 'ru' ? 'из' : 'of'} {pages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page === pages}
            style={{
              padding: '6px 12px',
              fontSize: '14px',
              cursor: page === pages ? 'not-allowed' : 'pointer',
              opacity: page === pages ? 0.5 : 1
            }}
          >
            {lang === 'ru' ? 'Вперед' : 'Next'} ▶️
          </button>
          <button
            onClick={() => setPage(pages)}
            disabled={page === pages}
            style={{
              padding: '6px 12px',
              fontSize: '14px',
              cursor: page === pages ? 'not-allowed' : 'pointer',
              opacity: page === pages ? 0.5 : 1
            }}
          >
            {lang === 'ru' ? 'Последняя' : 'Last'} ⏭️
          </button>
        </div>
      )}
      
      {/* Image Viewer Modal */}
      {viewingImage && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px'
          }}
          onClick={() => setViewingImage(null)}
        >
          <button
            onClick={() => setViewingImage(null)}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              background: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              fontSize: '24px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ✕
          </button>
          <img
            src={`/files/${viewingImage}`}
            alt="Full size"
            style={{
              maxWidth: '90%',
              maxHeight: '90%',
              objectFit: 'contain',
              borderRadius: '8px'
            }}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      {/* Contact Card Modal */}
      {viewingContact && (
        <ContactCard
          contactId={viewingContact}
          lang={lang}
          onClose={() => {
            setViewingContact(null);
            load(); // Reload in case of changes
          }}
        />
      )}

      {/* Table Settings Modal */}
      {showTableSettings && (
        <TableSettings
          columns={tableColumns}
          onSave={handleSaveTableSettings}
          onClose={() => setShowTableSettings(false)}
          lang={lang}
        />
      )}
    </div>
  );
}
