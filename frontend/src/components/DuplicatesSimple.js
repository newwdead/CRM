/**
 * DuplicatesSimple - Простой поиск и объединение дубликатов
 * Полностью переписанный функционал с нуля
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const DuplicatesSimple = () => {
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    findDuplicates();
  }, []);

  const findDuplicates = async () => {
    setSearching(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/contacts/find-duplicates', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to find duplicates');
      }

      const data = await response.json();
      setDuplicates(data.duplicates || []);
      
      if (data.duplicates.length === 0) {
        toast.success('Дубликаты не найдены!');
      } else {
        toast.success(`Найдено ${data.duplicates.length} групп дубликатов`);
      }
    } catch (error) {
      console.error('Error finding duplicates:', error);
      toast.error('Ошибка поиска дубликатов');
    } finally {
      setSearching(false);
    }
  };

  const mergeDuplicates = async (groupIndex) => {
    const group = duplicates[groupIndex];
    if (!group || group.contacts.length < 2) return;

    if (!window.confirm(`Объединить ${group.contacts.length} контактов?`)) {
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const contactIds = group.contacts.map(c => c.id);
      
      const response = await fetch('/api/contacts/merge-duplicates', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contact_ids: contactIds
        })
      });

      if (!response.ok) {
        throw new Error('Failed to merge');
      }

      const result = await response.json();
      toast.success(`Контакты объединены! ID: ${result.merged_contact_id}`);
      
      // Remove merged group
      setDuplicates(prev => prev.filter((_, idx) => idx !== groupIndex));
    } catch (error) {
      console.error('Error merging:', error);
      toast.error('Ошибка объединения');
    } finally {
      setLoading(false);
    }
  };

  const dismissGroup = (groupIndex) => {
    setDuplicates(prev => prev.filter((_, idx) => idx !== groupIndex));
    toast.success('Группа скрыта');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            🔍 Поиск дубликатов
          </h1>
          <p style={{ margin: '8px 0 0', color: '#666', fontSize: '14px' }}>
            Автоматический поиск по ФИО, email, телефону, компании
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={findDuplicates}
            disabled={searching}
            style={{
              padding: '10px 20px',
              backgroundColor: searching ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: searching ? 'not-allowed' : 'pointer',
              fontWeight: '500'
            }}
          >
            {searching ? '🔄 Поиск...' : '🔍 Искать заново'}
          </button>

          <button
            onClick={() => navigate(-1)}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            ← Назад
          </button>
        </div>
      </div>

      {/* Stats */}
      {!searching && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f3f4f6',
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          gap: '20px'
        }}>
          <div>
            <span style={{ fontSize: '14px', color: '#6b7280' }}>Найдено групп:</span>
            <span style={{ fontSize: '20px', fontWeight: 'bold', marginLeft: '10px' }}>
              {duplicates.length}
            </span>
          </div>
          <div>
            <span style={{ fontSize: '14px', color: '#6b7280' }}>Всего дубликатов:</span>
            <span style={{ fontSize: '20px', fontWeight: 'bold', marginLeft: '10px' }}>
              {duplicates.reduce((sum, group) => sum + group.contacts.length, 0)}
            </span>
          </div>
        </div>
      )}

      {/* Loading */}
      {searching && (
        <div style={{
          textAlign: 'center',
          padding: '60px',
          fontSize: '16px',
          color: '#6b7280'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔍</div>
          <div>Поиск дубликатов...</div>
        </div>
      )}

      {/* Empty State */}
      {!searching && duplicates.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '60px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '15px' }}>✅</div>
          <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            Дубликаты не найдены
          </div>
          <div style={{ color: '#6b7280', fontSize: '14px' }}>
            Все контакты уникальны
          </div>
        </div>
      )}

      {/* Duplicate Groups */}
      {!searching && duplicates.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {duplicates.map((group, groupIndex) => (
            <div
              key={groupIndex}
              style={{
                backgroundColor: 'white',
                border: '2px solid #f59e0b',
                borderRadius: '8px',
                padding: '20px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              {/* Group Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '15px',
                paddingBottom: '15px',
                borderBottom: '1px solid #e5e7eb'
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
                    Группа #{groupIndex + 1}
                  </h3>
                  <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#6b7280' }}>
                    Похожие поля: {group.match_reason || 'ФИО, email, телефон'}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => mergeDuplicates(groupIndex)}
                    disabled={loading}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: loading ? '#9ca3af' : '#10b981',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      fontWeight: '500',
                      fontSize: '14px'
                    }}
                  >
                    ✔️ Объединить
                  </button>

                  <button
                    onClick={() => dismissGroup(groupIndex)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#f3f4f6',
                      color: '#6b7280',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: '500',
                      fontSize: '14px'
                    }}
                  >
                    ✕ Скрыть
                  </button>
                </div>
              </div>

              {/* Contacts Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '15px'
              }}>
                {group.contacts.map((contact, contactIndex) => (
                  <div
                    key={contact.id}
                    onClick={() => navigate(`/contacts/${contact.id}`)}
                    style={{
                      padding: '15px',
                      backgroundColor: '#f9fafb',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#e3f2fd';
                      e.currentTarget.style.borderColor = '#2196f3';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#f9fafb';
                      e.currentTarget.style.borderColor = '#e5e7eb';
                    }}
                  >
                    {/* Contact Badge */}
                    <div style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      backgroundColor: contactIndex === 0 ? '#10b981' : '#6b7280',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      marginBottom: '10px'
                    }}>
                      {contactIndex === 0 ? 'ОСНОВНОЙ' : `Дубликат #${contactIndex}`}
                    </div>

                    {/* Contact Info */}
                    <div style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px' }}>
                      {contact.full_name || contact.first_name || contact.last_name || 'Без имени'}
                    </div>

                    {contact.company && (
                      <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>
                        🏢 {contact.company}
                      </div>
                    )}

                    {contact.position && (
                      <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>
                        💼 {contact.position}
                      </div>
                    )}

                    {contact.email && (
                      <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>
                        ✉️ {contact.email}
                      </div>
                    )}

                    {contact.phone && (
                      <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>
                        📞 {contact.phone}
                      </div>
                    )}

                    <div style={{
                      marginTop: '8px',
                      paddingTop: '8px',
                      borderTop: '1px solid #e5e7eb',
                      fontSize: '11px',
                      color: '#9ca3af'
                    }}>
                      ID: {contact.id} | Создан: {new Date(contact.created_at).toLocaleDateString('ru')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DuplicatesSimple;

