import React, { useState } from 'react';
import toast from 'react-hot-toast';

export default function DuplicateMergeModal({ lang = 'ru', contact, duplicates, onClose, onMerged }) {
  const [selectedDuplicate, setSelectedDuplicate] = useState(null);
  const [fieldSelections, setFieldSelections] = useState({});
  const [loading, setLoading] = useState(false);

  const t = lang === 'ru' ? {
    title: 'Объединение дубликатов',
    selectDuplicate: 'Выберите дубликат для объединения:',
    primaryContact: 'Основной контакт',
    duplicateContact: 'Дубликат',
    selectFields: 'Выберите, какие данные сохранить:',
    field: 'Поле',
    keepPrimary: 'Основной',
    keepDuplicate: 'Дубликат',
    merge: 'Объединить',
    cancel: 'Отмена',
    merging: 'Объединяю...',
    merged: 'Контакты успешно объединены',
    error: 'Ошибка при объединении',
    noDuplicates: 'Нет дубликатов для этого контакта',
    similarity: 'Похожесть',
    matchFields: 'Совпадающие поля'
  } : {
    title: 'Merge Duplicates',
    selectDuplicate: 'Select duplicate to merge:',
    primaryContact: 'Primary Contact',
    duplicateContact: 'Duplicate Contact',
    selectFields: 'Select which data to keep:',
    field: 'Field',
    keepPrimary: 'Primary',
    keepDuplicate: 'Duplicate',
    merge: 'Merge',
    cancel: 'Cancel',
    merging: 'Merging...',
    merged: 'Contacts merged successfully',
    error: 'Error merging contacts',
    noDuplicates: 'No duplicates found for this contact',
    similarity: 'Similarity',
    matchFields: 'Matching Fields'
  };

  // Get duplicates for this contact
  const contactDuplicates = duplicates.filter(
    dup => dup.contact_id_1 === contact.id || dup.contact_id_2 === contact.id
  );

  // Get the other contact from the duplicate pair
  const getOtherContact = (dup) => {
    return dup.contact_id_1 === contact.id ? dup.contact_2 : dup.contact_1;
  };

  // Fields that can be merged
  const mergeableFields = [
    { key: 'full_name', label: lang === 'ru' ? 'Полное имя' : 'Full Name' },
    { key: 'first_name', label: lang === 'ru' ? 'Имя' : 'First Name' },
    { key: 'last_name', label: lang === 'ru' ? 'Фамилия' : 'Last Name' },
    { key: 'middle_name', label: lang === 'ru' ? 'Отчество' : 'Middle Name' },
    { key: 'company', label: lang === 'ru' ? 'Компания' : 'Company' },
    { key: 'position', label: lang === 'ru' ? 'Должность' : 'Position' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: lang === 'ru' ? 'Телефон' : 'Phone' },
    { key: 'phone_mobile', label: lang === 'ru' ? 'Моб. телефон' : 'Mobile Phone' },
    { key: 'phone_work', label: lang === 'ru' ? 'Раб. телефон' : 'Work Phone' },
    { key: 'address', label: lang === 'ru' ? 'Адрес' : 'Address' },
    { key: 'website', label: lang === 'ru' ? 'Сайт' : 'Website' },
    { key: 'comment', label: lang === 'ru' ? 'Комментарий' : 'Comment' },
  ];

  const handleMerge = async () => {
    if (!selectedDuplicate) {
      toast.error(lang === 'ru' ? 'Выберите дубликат' : 'Select a duplicate');
      return;
    }

    setLoading(true);
    try {
      const otherContact = getOtherContact(selectedDuplicate);
      const token = localStorage.getItem('token');
      
      const res = await fetch(`/api/contacts/${contact.id}/merge/${otherContact.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selected_fields: fieldSelections })
      });

      if (res.ok) {
        toast.success(t.merged);
        onMerged?.();
        onClose();
      } else {
        const error = await res.json();
        toast.error(error.detail || t.error);
      }
    } catch (error) {
      console.error('Error merging contacts:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  if (contactDuplicates.length === 0) {
    return (
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        onClick={onClose}
      >
        <div
          style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            maxWidth: '400px',
            width: '90%'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <h3 style={{ marginTop: 0 }}>{t.title}</h3>
          <p>{t.noDuplicates}</p>
          <button onClick={onClose}>{t.cancel}</button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        overflowY: 'auto',
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          maxWidth: '900px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0, marginBottom: '20px' }}>{t.title}</h2>

        {/* Step 1: Select Duplicate */}
        <div style={{ marginBottom: '30px' }}>
          <h3>{t.selectDuplicate}</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {contactDuplicates.map(dup => {
              const otherContact = getOtherContact(dup);
              return (
                <div
                  key={dup.id}
                  onClick={() => setSelectedDuplicate(dup)}
                  style={{
                    padding: '15px',
                    border: `2px solid ${selectedDuplicate?.id === dup.id ? '#2196F3' : '#ddd'}`,
                    borderRadius: '8px',
                    cursor: 'pointer',
                    backgroundColor: selectedDuplicate?.id === dup.id ? '#e3f2fd' : 'white',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{otherContact.full_name || `${otherContact.first_name || ''} ${otherContact.last_name || ''}`.trim() || '—'}</strong>
                      <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                        {otherContact.company && <span>🏢 {otherContact.company}</span>}
                        {otherContact.email && <span style={{ marginLeft: '15px' }}>📧 {otherContact.email}</span>}
                        {otherContact.phone && <span style={{ marginLeft: '15px' }}>📞 {otherContact.phone}</span>}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{
                        padding: '4px 12px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        marginBottom: '5px'
                      }}>
                        {t.similarity}: {Math.round(dup.similarity_score * 100)}%
                      </div>
                      {dup.match_fields && (
                        <div style={{ fontSize: '11px', color: '#666' }}>
                          {t.matchFields}: {Object.keys(dup.match_fields).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step 2: Select Fields (only shown if duplicate is selected) */}
        {selectedDuplicate && (
          <div style={{ marginBottom: '30px' }}>
            <h3>{t.selectFields}</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f5f5f5' }}>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.field}</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.primaryContact}</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.duplicateContact}</th>
                    <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>{lang === 'ru' ? 'Выбор' : 'Selection'}</th>
                  </tr>
                </thead>
                <tbody>
                  {mergeableFields.map(field => {
                    const otherContact = getOtherContact(selectedDuplicate);
                    const primaryValue = contact[field.key] || '—';
                    const duplicateValue = otherContact[field.key] || '—';
                    
                    if (primaryValue === '—' && duplicateValue === '—') return null;
                    
                    return (
                      <tr key={field.key}>
                        <td style={{ padding: '10px', border: '1px solid #ddd', fontWeight: '500' }}>{field.label}</td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: fieldSelections[field.key] === 'primary' || !fieldSelections[field.key] ? '#000' : '#999' }}>
                          {primaryValue}
                        </td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: fieldSelections[field.key] === 'duplicate' ? '#000' : '#999' }}>
                          {duplicateValue}
                        </td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
                          <select
                            value={fieldSelections[field.key] || 'primary'}
                            onChange={(e) => setFieldSelections({ ...fieldSelections, [field.key]: e.target.value })}
                            style={{ padding: '6px 10px', borderRadius: '4px', border: '1px solid #ddd' }}
                          >
                            <option value="primary">{t.keepPrimary}</option>
                            <option value="duplicate">{t.keepDuplicate}</option>
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} disabled={loading} style={{ padding: '10px 20px' }}>
            {t.cancel}
          </button>
          <button
            onClick={handleMerge}
            disabled={!selectedDuplicate || loading}
            style={{
              padding: '10px 20px',
              backgroundColor: selectedDuplicate && !loading ? '#4CAF50' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedDuplicate && !loading ? 'pointer' : 'not-allowed'
            }}
          >
            {loading ? t.merging : t.merge}
          </button>
        </div>
      </div>
    </div>
  );
}

