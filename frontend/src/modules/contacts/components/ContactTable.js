/**
 * ContactTable Component
 * Таблица контактов с возможностью сортировки и выбора
 */

import React from 'react';

export const ContactTable = ({
  contacts,
  selected,
  allSelected,
  onToggleSelect,
  onToggleSelectAll,
  onSort,
  sortBy,
  sortOrder,
  onViewContact,
  language = 'ru'
}) => {
  const translations = {
    en: {
      select: 'Select',
      name: 'Name',
      company: 'Company',
      position: 'Position',
      phone: 'Phone',
      email: 'Email',
      date: 'Date',
      noContacts: 'No contacts found'
    },
    ru: {
      select: 'Выбрать',
      name: 'Имя',
      company: 'Компания',
      position: 'Должность',
      phone: 'Телефон',
      email: 'Email',
      date: 'Дата',
      noContacts: 'Контакты не найдены'
    }
  };

  const t = translations[language];

  const getSortIcon = (field) => {
    if (sortBy !== field) return '⇅';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  if (contacts.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '50px',
        color: '#666'
      }}>
        {t.noContacts}
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        backgroundColor: 'white'
      }}>
        <thead>
          <tr style={{ backgroundColor: '#f8f9fa' }}>
            <th style={{
              padding: '12px',
              textAlign: 'left',
              borderBottom: '2px solid #dee2e6',
              width: '50px'
            }}>
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleSelectAll}
                style={{ cursor: 'pointer' }}
              />
            </th>
            <th
              onClick={() => onSort('first_name')}
              style={{
                padding: '12px',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                cursor: 'pointer',
                userSelect: 'none'
              }}
            >
              {t.name} {getSortIcon('first_name')}
            </th>
            <th
              onClick={() => onSort('company')}
              style={{
                padding: '12px',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                cursor: 'pointer',
                userSelect: 'none'
              }}
            >
              {t.company} {getSortIcon('company')}
            </th>
            <th style={{
              padding: '12px',
              textAlign: 'left',
              borderBottom: '2px solid #dee2e6'
            }}>
              {t.position}
            </th>
            <th style={{
              padding: '12px',
              textAlign: 'left',
              borderBottom: '2px solid #dee2e6'
            }}>
              {t.phone}
            </th>
            <th style={{
              padding: '12px',
              textAlign: 'left',
              borderBottom: '2px solid #dee2e6'
            }}>
              {t.email}
            </th>
            <th
              onClick={() => onSort('created_at')}
              style={{
                padding: '12px',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                cursor: 'pointer',
                userSelect: 'none'
              }}
            >
              {t.date} {getSortIcon('created_at')}
            </th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr
              key={contact.id}
              onClick={() => onViewContact(contact)}
              style={{
                cursor: 'pointer',
                backgroundColor: selected.includes(contact.id) ? '#e3f2fd' : 'white',
                ':hover': { backgroundColor: '#f8f9fa' }
              }}
              onMouseEnter={(e) => {
                if (!selected.includes(contact.id)) {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                }
              }}
              onMouseLeave={(e) => {
                if (!selected.includes(contact.id)) {
                  e.currentTarget.style.backgroundColor = 'white';
                }
              }}
            >
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6'
              }}>
                <input
                  type="checkbox"
                  checked={selected.includes(contact.id)}
                  onChange={(e) => {
                    e.stopPropagation();
                    onToggleSelect(contact.id);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  style={{ cursor: 'pointer' }}
                />
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6',
                fontWeight: 'bold'
              }}>
                {contact.first_name} {contact.last_name}
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6'
              }}>
                {contact.company || '-'}
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6'
              }}>
                {contact.position || '-'}
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6'
              }}>
                {contact.phone || '-'}
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6'
              }}>
                {contact.email || '-'}
              </td>
              <td style={{
                padding: '12px',
                borderBottom: '1px solid #dee2e6',
                fontSize: '13px',
                color: '#666'
              }}>
                {contact.created_at ? new Date(contact.created_at).toLocaleDateString() : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

