import React, { useEffect, useState } from 'react';

/**
 * Full contact card (CRM-style) - displays all contact information
 * Opens when clicking on a contact in the list
 */
export default function ContactCard({ contactId, lang = 'ru', onClose }) {
  const [contact, setContact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});

  const t = {
    ru: {
      title: 'Карточка контакта',
      edit: 'Редактировать',
      save: 'Сохранить',
      cancel: 'Отмена',
      close: 'Закрыть',
      delete: 'Удалить',
      confirmDelete: 'Вы уверены?',
      // Personal Info
      personalInfo: 'Личная информация',
      lastName: 'Фамилия',
      firstName: 'Имя',
      middleName: 'Отчество',
      fullName: 'Полное имя',
      birthday: 'День рождения',
      // Company Info
      companyInfo: 'Информация о компании',
      company: 'Компания',
      position: 'Должность',
      department: 'Отдел',
      // Contact Details
      contactDetails: 'Контактные данные',
      email: 'Email',
      phone: 'Телефон',
      phoneMobile: 'Мобильный',
      phoneWork: 'Рабочий',
      fax: 'Факс',
      website: 'Веб-сайт',
      address: 'Адрес',
      // CRM Fields
      crmInfo: 'CRM данные',
      status: 'Статус',
      priority: 'Приоритет',
      source: 'Источник',
      createdAt: 'Дата создания',
      updatedAt: 'Обновлено',
      // Other
      comment: 'Комментарий',
      photo: 'Фото',
      tags: 'Теги',
      groups: 'Группы',
      uid: 'UID',
      // Statuses
      active: 'Активный',
      inactive: 'Неактивный',
      lead: 'Лид',
      client: 'Клиент',
      // Priorities
      low: 'Низкий',
      medium: 'Средний',
      high: 'Высокий',
      vip: 'VIP',
    },
    en: {
      title: 'Contact Card',
      edit: 'Edit',
      save: 'Save',
      cancel: 'Cancel',
      close: 'Close',
      delete: 'Delete',
      confirmDelete: 'Are you sure?',
      // Personal Info
      personalInfo: 'Personal Information',
      lastName: 'Last Name',
      firstName: 'First Name',
      middleName: 'Middle Name',
      fullName: 'Full Name',
      birthday: 'Birthday',
      // Company Info
      companyInfo: 'Company Information',
      company: 'Company',
      position: 'Position',
      department: 'Department',
      // Contact Details
      contactDetails: 'Contact Details',
      email: 'Email',
      phone: 'Phone',
      phoneMobile: 'Mobile',
      phoneWork: 'Work Phone',
      fax: 'Fax',
      website: 'Website',
      address: 'Address',
      // CRM Fields
      crmInfo: 'CRM Data',
      status: 'Status',
      priority: 'Priority',
      source: 'Source',
      createdAt: 'Created',
      updatedAt: 'Updated',
      // Other
      comment: 'Comment',
      photo: 'Photo',
      tags: 'Tags',
      groups: 'Groups',
      uid: 'UID',
      // Statuses
      active: 'Active',
      inactive: 'Inactive',
      lead: 'Lead',
      client: 'Client',
      // Priorities
      low: 'Low',
      medium: 'Medium',
      high: 'High',
      vip: 'VIP',
    }
  }[lang] || {};

  useEffect(() => {
    loadContact();
  }, [contactId]);

  const loadContact = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/contacts/${contactId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to load contact');
      const data = await res.json();
      setContact(data);
      setFormData(data);
    } catch (error) {
      console.error('Error loading contact:', error);
      alert('Error loading contact');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/contacts/${contactId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error('Failed to save');
      await loadContact();
      setEditing(false);
      alert(lang === 'ru' ? 'Сохранено!' : 'Saved!');
    } catch (error) {
      console.error('Error saving:', error);
      alert('Error saving contact');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(t.confirmDelete)) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/contacts/${contactId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete');
      alert(lang === 'ru' ? 'Удалено' : 'Deleted');
      onClose?.();
    } catch (error) {
      console.error('Error deleting:', error);
      alert('Error deleting contact');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const renderField = (label, value, field) => {
    if (editing && field) {
      return (
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#555' }}>
            {label}
          </label>
          <input
            type="text"
            value={formData[field] || ''}
            onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          />
        </div>
      );
    }
    return (
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#555' }}>
          {label}
        </label>
        <div style={{ padding: '8px 0', color: '#333' }}>
          {value || '—'}
        </div>
      </div>
    );
  };

  const renderSelectField = (label, value, field, options) => {
    if (editing && field) {
      return (
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#555' }}>
            {label}
          </label>
          <select
            value={formData[field] || ''}
            onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <option value="">—</option>
            {options.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      );
    }
    return renderField(label, value || '—');
  };

  if (loading) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }}>
        <div style={{ color: 'white', fontSize: '20px' }}>
          {lang === 'ru' ? 'Загрузка...' : 'Loading...'}
        </div>
      </div>
    );
  }

  if (!contact) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }} onClick={onClose}>
        <div style={{ color: 'white', fontSize: '20px' }}>
          {lang === 'ru' ? 'Контакт не найден' : 'Contact not found'}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px',
        overflow: 'auto'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          maxWidth: '900px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px 30px',
          borderBottom: '1px solid #eee',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#f8f9fa'
        }}>
          <h2 style={{ margin: 0, color: '#333' }}>{t.title}</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#999',
              padding: '0 10px'
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '30px' }}>
          {/* Photo */}
          {contact.photo_path && (
            <div style={{ marginBottom: '30px', textAlign: 'center' }}>
              <img
                src={`/files/${contact.photo_path}`}
                alt="Business card"
                style={{
                  maxWidth: '100%',
                  maxHeight: '300px',
                  borderRadius: '8px',
                  border: '1px solid #ddd'
                }}
              />
            </div>
          )}

          {/* Personal Info */}
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#0066cc', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>
              📋 {t.personalInfo}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              {renderField(t.lastName, contact.last_name, 'last_name')}
              {renderField(t.firstName, contact.first_name, 'first_name')}
            </div>
            {renderField(t.middleName, contact.middle_name, 'middle_name')}
            {renderField(t.fullName, contact.full_name, 'full_name')}
            {renderField(t.birthday, contact.birthday, 'birthday')}
          </div>

          {/* Company Info */}
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#0066cc', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>
              🏢 {t.companyInfo}
            </h3>
            {renderField(t.company, contact.company, 'company')}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              {renderField(t.position, contact.position, 'position')}
              {renderField(t.department, contact.department, 'department')}
            </div>
          </div>

          {/* Contact Details */}
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#0066cc', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>
              📞 {t.contactDetails}
            </h3>
            {renderField(t.email, contact.email, 'email')}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
              {renderField(t.phone, contact.phone, 'phone')}
              {renderField(t.phoneMobile, contact.phone_mobile, 'phone_mobile')}
              {renderField(t.phoneWork, contact.phone_work, 'phone_work')}
            </div>
            {renderField(t.fax, contact.fax, 'fax')}
            {renderField(t.website, contact.website, 'website')}
            {renderField(t.address, contact.address, 'address')}
          </div>

          {/* CRM Info */}
          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#0066cc', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>
              💼 {t.crmInfo}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
              {renderSelectField(t.status, t[contact.status] || contact.status, 'status', [
                { value: 'active', label: t.active },
                { value: 'inactive', label: t.inactive },
                { value: 'lead', label: t.lead },
                { value: 'client', label: t.client }
              ])}
              {renderSelectField(t.priority, t[contact.priority] || contact.priority, 'priority', [
                { value: 'low', label: t.low },
                { value: 'medium', label: t.medium },
                { value: 'high', label: t.high },
                { value: 'vip', label: t.vip }
              ])}
              {renderField(t.source, contact.source, 'source')}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '15px' }}>
              {renderField(t.createdAt, formatDate(contact.created_at))}
              {renderField(t.updatedAt, formatDate(contact.updated_at))}
            </div>
          </div>

          {/* Comment */}
          {renderField(t.comment, contact.comment, 'comment')}

          {/* UID */}
          <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <small style={{ color: '#666' }}>{t.uid}: <code>{contact.uid}</code></small>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '20px 30px',
          borderTop: '1px solid #eee',
          display: 'flex',
          justifyContent: 'space-between',
          backgroundColor: '#f8f9fa'
        }}>
          <div>
            <button
              onClick={handleDelete}
              style={{
                padding: '10px 20px',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              {t.delete}
            </button>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            {editing ? (
              <>
                <button
                  onClick={() => {
                    setEditing(false);
                    setFormData(contact);
                  }}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  {t.cancel}
                </button>
                <button
                  onClick={handleSave}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  {t.save}
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditing(true)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                {t.edit}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

