import React, { useEffect, useState } from 'react';
import ContactCard from './ContactCard';

/**
 * Companies view - groups contacts by company
 */
export default function Companies({ lang = 'ru' }) {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedCompany, setExpandedCompany] = useState(null);
  const [selectedContact, setSelectedContact] = useState(null);

  const t = {
    ru: {
      title: 'Организации',
      noCompany: 'Без компании',
      totalContacts: 'Всего контактов',
      noData: 'Нет данных',
      loading: 'Загрузка...',
      contacts: 'контактов',
      contact: 'контакт',
      contact_2: 'контакта',
    },
    en: {
      title: 'Companies',
      noCompany: 'No Company',
      totalContacts: 'Total Contacts',
      noData: 'No data',
      loading: 'Loading...',
      contacts: 'contacts',
      contact: 'contact',
      contact_2: 'contacts',
    }
  }[lang] || {};

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      // Load all contacts
      const res = await fetch('/api/contacts/?limit=1000', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to load contacts');
      const data = await res.json();
      
      // Group by company
      const grouped = {};
      data.items.forEach(contact => {
        const companyName = contact.company || t.noCompany;
        if (!grouped[companyName]) {
          grouped[companyName] = [];
        }
        grouped[companyName].push(contact);
      });

      // Convert to array and sort by number of contacts
      const companiesArray = Object.entries(grouped).map(([name, contacts]) => ({
        name,
        contacts,
        count: contacts.length
      })).sort((a, b) => b.count - a.count);

      setCompanies(companiesArray);
    } catch (error) {
      console.error('Error loading companies:', error);
      alert('Error loading companies');
    } finally {
      setLoading(false);
    }
  };

  const getContactCountText = (count) => {
    if (lang === 'en') return `${count} ${count === 1 ? t.contact : t.contacts}`;
    
    // Russian plural forms
    const lastDigit = count % 10;
    const lastTwoDigits = count % 100;
    
    if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
      return `${count} ${t.contacts}`;
    }
    if (lastDigit === 1) {
      return `${count} ${t.contact}`;
    }
    if (lastDigit >= 2 && lastDigit <= 4) {
      return `${count} ${t.contact_2}`;
    }
    return `${count} ${t.contacts}`;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
        {t.loading}
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
        📭 {t.noData}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '20px' }}>🏢 {t.title}</h2>
      
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <strong>{t.totalContacts}:</strong> {companies.reduce((sum, c) => sum + c.count, 0)}
      </div>

      {companies.map((company, idx) => (
        <div
          key={idx}
          style={{
            marginBottom: '15px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            overflow: 'hidden',
            backgroundColor: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          {/* Company Header */}
          <div
            onClick={() => setExpandedCompany(expandedCompany === idx ? null : idx)}
            style={{
              padding: '15px 20px',
              backgroundColor: '#f8f9fa',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: expandedCompany === idx ? '1px solid #ddd' : 'none'
            }}
          >
            <div>
              <strong style={{ fontSize: '16px' }}>
                {company.name === t.noCompany ? (
                  <span style={{ color: '#999' }}>📋 {company.name}</span>
                ) : (
                  <span>🏢 {company.name}</span>
                )}
              </strong>
              <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                {getContactCountText(company.count)}
              </div>
            </div>
            <div style={{ fontSize: '20px', color: '#666' }}>
              {expandedCompany === idx ? '▼' : '▶'}
            </div>
          </div>

          {/* Contacts List */}
          {expandedCompany === idx && (
            <div style={{ padding: '15px 20px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '10px', textAlign: 'left' }}>
                      {lang === 'ru' ? 'Имя' : 'Name'}
                    </th>
                    <th style={{ padding: '10px', textAlign: 'left' }}>
                      {lang === 'ru' ? 'Должность' : 'Position'}
                    </th>
                    <th style={{ padding: '10px', textAlign: 'left' }}>
                      {lang === 'ru' ? 'Email' : 'Email'}
                    </th>
                    <th style={{ padding: '10px', textAlign: 'left' }}>
                      {lang === 'ru' ? 'Телефон' : 'Phone'}
                    </th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>
                      {lang === 'ru' ? 'Действия' : 'Actions'}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {company.contacts.map(contact => (
                    <tr
                      key={contact.id}
                      style={{
                        borderBottom: '1px solid #eee',
                        cursor: 'pointer'
                      }}
                      onClick={() => setSelectedContact(contact.id)}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                    >
                      <td style={{ padding: '10px' }}>
                        {contact.last_name || contact.first_name ? (
                          `${contact.last_name || ''} ${contact.first_name || ''} ${contact.middle_name || ''}`.trim()
                        ) : (
                          contact.full_name || '—'
                        )}
                      </td>
                      <td style={{ padding: '10px' }}>{contact.position || '—'}</td>
                      <td style={{ padding: '10px' }}>{contact.email || '—'}</td>
                      <td style={{ padding: '10px' }}>{contact.phone || '—'}</td>
                      <td style={{ padding: '10px', textAlign: 'center' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedContact(contact.id);
                          }}
                          style={{
                            padding: '5px 15px',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          {lang === 'ru' ? 'Открыть' : 'Open'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {/* Contact Card Modal */}
      {selectedContact && (
        <ContactCard
          contactId={selectedContact}
          lang={lang}
          onClose={() => {
            setSelectedContact(null);
            loadCompanies(); // Reload in case of changes
          }}
        />
      )}
    </div>
  );
}

