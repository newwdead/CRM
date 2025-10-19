import React, { useEffect, useState } from 'react';

export default function ContactList({ lang = 'ru', onEdit }) {
  const [contacts, setContacts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [selected, setSelected] = useState([]);
  const [showBulkEdit, setShowBulkEdit] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({});
  const [search, setSearch] = useState('');
  const [uidFilter, setUidFilter] = useState('');
  const [newContact, setNewContact] = useState({
    full_name: '', company: '', position: '', email: '',
    phone: '', address: '', comment: '', website: ''
  });
  const [showNewContact, setShowNewContact] = useState(false);
  const [stats, setStats] = useState({ total: 0, withEmail: 0, withPhone: 0 });

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
  };

  const load = async () => {
    const res = await fetch('/api/contacts/');
    const data = await res.json();
    setContacts(data);
    setFiltered(data);
    
    // Calculate stats
    setStats({
      total: data.length,
      withEmail: data.filter(c => c.email).length,
      withPhone: data.filter(c => c.phone).length
    });
  };

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener('refresh-contacts', handler);
    return () => window.removeEventListener('refresh-contacts', handler);
  }, []);

  const applyFilters = (q, uidQ) => {
    const ql = (q || '').toLowerCase();
    const ul = (uidQ || '').toLowerCase();
    let base = contacts.filter(c =>
      (c.full_name || '').toLowerCase().includes(ql) ||
      (c.email || '').toLowerCase().includes(ql) ||
      (c.phone || '').toLowerCase().includes(ql) ||
      (c.company || '').toLowerCase().includes(ql) ||
      (c.comment || '').toLowerCase().includes(ql) ||
      (c.website || '').toLowerCase().includes(ql)
    );
    if (ul) base = base.filter(c => (c.uid || '').toLowerCase().includes(ul));
    setFiltered(base);
  };

  const handleSearch = (e) => {
    const q = e.target.value;
    setSearch(q);
    applyFilters(q, uidFilter);
  };

  const handleUidFilter = (e) => {
    const val = e.target.value;
    setUidFilter(val);
    applyFilters(search, val);
  };

  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  const toggleAll = () => {
    if (selected.length === filtered.length) {
      setSelected([]);
    } else {
      setSelected(filtered.map(c => c.id));
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
    await fetch('/api/contacts/delete_bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    await fetch('/api/contacts/update_bulk', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
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
    await fetch('/api/contacts/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newContact)
    });
    setNewContact({
      full_name: '', company: '', position: '', email: '',
      phone: '', address: '', comment: '', website: ''
    });
    setShowNewContact(false);
    await load();
  };

  return (
    <div className="card">
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
          onChange={handleSearch}
          style={{ flex: 1, minWidth: '200px' }}
        />
        <input
          placeholder={`🔑 ${t.uid}`}
          value={uidFilter}
          onChange={handleUidFilter}
          style={{ width: '200px' }}
        />
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button onClick={() => setShowNewContact(!showNewContact)} className="success">
          ➕ {t.addNew}
        </button>
        <button onClick={toggleAll} className="secondary">
          {selected.length === filtered.length ? '☑️ ' + t.deselectAll : '☐ ' + t.selectAll}
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
                  checked={selected.length === filtered.length && filtered.length > 0}
                  onChange={toggleAll}
                />
              </th>
              <th>{t.actions}</th>
              <th>{t.uid}</th>
              <th>{t.name}</th>
              <th>{t.company}</th>
              <th>{t.position}</th>
              <th>{t.email}</th>
              <th>{t.phone}</th>
              <th>{t.address}</th>
              <th>{t.website}</th>
              <th>{t.comment}</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="11" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                  {search || uidFilter ? '🔍 ' + (lang === 'ru' ? 'Ничего не найдено' : 'Nothing found') : '📭 ' + (lang === 'ru' ? 'Нет контактов' : 'No contacts')}
                </td>
              </tr>
            ) : (
              filtered.map(c => (
                <tr key={c.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.includes(c.id)}
                      onChange={() => toggle(c.id)}
                    />
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {c.photo_path && (
                      <a
                        href={`/files/${c.photo_path}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ marginRight: '8px', textDecoration: 'none' }}
                        title={t.photo}
                      >
                        🖼️
                      </a>
                    )}
                    <button onClick={() => onEdit?.(c.id)} className="secondary" style={{ padding: '4px 8px', fontSize: '12px' }}>
                      {t.edit}
                    </button>
                  </td>
                  <td>
                    {c.uid ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <code style={{ fontSize: '11px' }}>{c.uid.slice(0, 8)}</code>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard?.writeText(String(c.uid));
                          }}
                          className="secondary"
                          style={{ padding: '2px 6px', fontSize: '11px' }}
                        >
                          📋
                        </button>
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td><strong>{c.full_name || '—'}</strong></td>
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
