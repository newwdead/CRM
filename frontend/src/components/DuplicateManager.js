import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { LoadingSpinner } from './common';
import { getAccessToken } from '../utils/tokenManager';

/**
 * Независимый модуль для управления дубликатами контактов
 * Работает полностью автономно, не зависит от общих конфигурационных файлов
 */
const DuplicateManager = ({ lang = 'ru' }) => {
  const [contacts, setContacts] = useState([]);
  const [duplicateGroups, setDuplicateGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [merging, setMerging] = useState(false);
  const [threshold, setThreshold] = useState(0.7); // Порог схожести 70%
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [mergeSelection, setMergeSelection] = useState({});
  
  const t = lang === 'ru' ? {
    title: 'Управление дубликатами',
    subtitle: 'Поиск и объединение повторяющихся контактов',
    threshold: 'Порог схожести',
    analyze: 'Анализировать',
    analyzing: 'Анализ...',
    noData: 'Загрузка данных...',
    noDuplicates: 'Дубликаты не найдены',
    foundGroups: 'Найдено групп дубликатов',
    similarity: 'Схожесть',
    contacts: 'контакта(ов)',
    merge: 'Объединить',
    cancel: 'Отмена',
    mergeSelected: 'Объединить выбранные',
    selectMaster: 'Выберите основной контакт',
    name: 'Имя',
    company: 'Компания',
    position: 'Должность',
    email: 'Email',
    phone: 'Телефон',
    address: 'Адрес',
    website: 'Сайт',
    mergeSuccess: 'Контакты успешно объединены',
    mergeError: 'Ошибка при объединении',
    loadError: 'Ошибка загрузки',
  } : {
    title: 'Duplicate Management',
    subtitle: 'Find and merge duplicate contacts',
    threshold: 'Similarity Threshold',
    analyze: 'Analyze',
    analyzing: 'Analyzing...',
    noData: 'Loading data...',
    noDuplicates: 'No duplicates found',
    foundGroups: 'Found duplicate groups',
    similarity: 'Similarity',
    contacts: 'contact(s)',
    merge: 'Merge',
    cancel: 'Cancel',
    mergeSelected: 'Merge Selected',
    selectMaster: 'Select master contact',
    name: 'Name',
    company: 'Company',
    position: 'Position',
    email: 'Email',
    phone: 'Phone',
    address: 'Address',
    website: 'Website',
    mergeSuccess: 'Contacts merged successfully',
    mergeError: 'Error merging contacts',
    loadError: 'Loading error',
  };

  // Загрузка всех контактов
  const loadContacts = async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        toast.error(lang === 'ru' ? 'Необходима авторизация' : 'Authorization required');
        // Redirect to login if no token
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
        return;
      }
      
      const response = await fetch('/api/contacts/?skip=0&limit=10000', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          toast.error(lang === 'ru' ? 'Сессия истекла. Войдите снова' : 'Session expired. Please login');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
          return;
        }
        throw new Error('Failed to load contacts');
      }
      
      const data = await response.json();
      setContacts(data.items || []);
    } catch (error) {
      console.error('Error loading contacts:', error);
      toast.error(t.loadError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContacts();
  }, []);

  // Функция сравнения строк (Levenshtein distance similarity)
  const stringSimilarity = (str1, str2) => {
    if (!str1 || !str2) return 0;
    
    str1 = str1.toLowerCase().trim();
    str2 = str2.toLowerCase().trim();
    
    if (str1 === str2) return 1.0;
    
    const len1 = str1.length;
    const len2 = str2.length;
    const maxLen = Math.max(len1, len2);
    
    if (maxLen === 0) return 1.0;
    
    // Простое сравнение по подстрокам
    const longer = len1 > len2 ? str1 : str2;
    const shorter = len1 > len2 ? str2 : str1;
    
    if (longer.includes(shorter)) {
      return shorter.length / longer.length;
    }
    
    // Levenshtein distance
    const matrix = Array(len2 + 1).fill(null).map(() => 
      Array(len1 + 1).fill(null)
    );
    
    for (let i = 0; i <= len1; i++) matrix[0][i] = i;
    for (let j = 0; j <= len2; j++) matrix[j][0] = j;
    
    for (let j = 1; j <= len2; j++) {
      for (let i = 1; i <= len1; i++) {
        const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1,
          matrix[j - 1][i - 1] + indicator
        );
      }
    }
    
    const distance = matrix[len2][len1];
    return 1 - (distance / maxLen);
  };

  // Нормализация телефона
  const normalizePhone = (phone) => {
    if (!phone) return '';
    return phone.replace(/[^\d]/g, '');
  };

  // Вычисление схожести двух контактов
  const calculateSimilarity = (contact1, contact2) => {
    const weights = {
      email: 0.4,    // Email - самый важный
      phone: 0.3,    // Телефон
      name: 0.2,     // Имя
      company: 0.1   // Компания
    };
    
    let totalScore = 0;
    let totalWeight = 0;
    
    // Email
    if (contact1.email && contact2.email) {
      if (contact1.email.toLowerCase() === contact2.email.toLowerCase()) {
        totalScore += weights.email;
      }
      totalWeight += weights.email;
    }
    
    // Phone
    if (contact1.phone && contact2.phone) {
      const phone1 = normalizePhone(contact1.phone);
      const phone2 = normalizePhone(contact2.phone);
      if (phone1 && phone2) {
        const phoneSimilarity = phone1.includes(phone2) || phone2.includes(phone1) ? 1.0 : 0.0;
        totalScore += phoneSimilarity * weights.phone;
        totalWeight += weights.phone;
      }
    }
    
    // Name
    if (contact1.full_name && contact2.full_name) {
      const nameSimilarity = stringSimilarity(contact1.full_name, contact2.full_name);
      totalScore += nameSimilarity * weights.name;
      totalWeight += weights.name;
    }
    
    // Company
    if (contact1.company && contact2.company) {
      const companySimilarity = stringSimilarity(contact1.company, contact2.company);
      totalScore += companySimilarity * weights.company;
      totalWeight += weights.company;
    }
    
    return totalWeight > 0 ? totalScore / totalWeight : 0;
  };

  // Анализ дубликатов
  const analyzeDuplicates = () => {
    setAnalyzing(true);
    
    setTimeout(() => {
      const groups = [];
      const processed = new Set();
      
      for (let i = 0; i < contacts.length; i++) {
        if (processed.has(contacts[i].id)) continue;
        
        const group = [contacts[i]];
        const similarities = [1.0];
        
        for (let j = i + 1; j < contacts.length; j++) {
          if (processed.has(contacts[j].id)) continue;
          
          const similarity = calculateSimilarity(contacts[i], contacts[j]);
          
          if (similarity >= threshold) {
            group.push(contacts[j]);
            similarities.push(similarity);
            processed.add(contacts[j].id);
          }
        }
        
        if (group.length > 1) {
          groups.push({
            contacts: group,
            similarities: similarities,
            avgSimilarity: similarities.reduce((a, b) => a + b, 0) / similarities.length
          });
          processed.add(contacts[i].id);
        }
      }
      
      // Сортируем по убыванию схожести
      groups.sort((a, b) => b.avgSimilarity - a.avgSimilarity);
      
      setDuplicateGroups(groups);
      setAnalyzing(false);
      
      if (groups.length === 0) {
        toast.success(t.noDuplicates);
      } else {
        toast.success(`${t.foundGroups}: ${groups.length}`);
      }
    }, 500);
  };

  // Объединение контактов
  const mergeContacts = async (masterId, slaveIds) => {
    setMerging(true);
    
    try {
      const token = getAccessToken();
      if (!token) {
        toast.error(lang === 'ru' ? 'Необходима авторизация' : 'Authorization required');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
        return;
      }
      
      const response = await fetch('/api/contacts/merge', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          master_id: masterId,
          slave_ids: slaveIds
        })
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          toast.error(lang === 'ru' ? 'Сессия истекла. Войдите снова' : 'Session expired. Please login');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
          return;
        }
        throw new Error('Failed to merge contacts');
      }
      
      toast.success(t.mergeSuccess);
      
      // Перезагружаем данные
      await loadContacts();
      
      // Закрываем модальное окно
      setSelectedGroup(null);
      setMergeSelection({});
      
      // Повторный анализ
      setTimeout(() => analyzeDuplicates(), 500);
      
    } catch (error) {
      console.error('Error merging contacts:', error);
      toast.error(t.mergeError);
    } finally {
      setMerging(false);
    }
  };

  if (loading) {
    return (
      <div className="modern-page">
        <h2>{t.title}</h2>
        <LoadingSpinner />
        <p style={{ textAlign: 'center', marginTop: '20px' }}>{t.noData}</p>
      </div>
    );
  }

  return (
    <div className="modern-page">
      <h2>🔍 {t.title}</h2>
      <p style={{ color: '#666', marginBottom: '24px' }}>{t.subtitle}</p>
      
      {/* Controls */}
      <div className="modern-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              {t.threshold}: {Math.round(threshold * 100)}%
            </label>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666', marginTop: '4px' }}>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
          
          <button
            onClick={analyzeDuplicates}
            disabled={analyzing || contacts.length === 0}
            className="modern-btn modern-btn-primary"
            style={{ padding: '12px 24px' }}
          >
            {analyzing ? '⏳ ' + t.analyzing : '🔍 ' + t.analyze}
          </button>
        </div>
        
        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '14px', color: '#666' }}>Всего контактов: </span>
              <strong style={{ fontSize: '18px' }}>{contacts.length}</strong>
            </div>
            <div>
              <span style={{ fontSize: '14px', color: '#666' }}>Групп дубликатов: </span>
              <strong style={{ fontSize: '18px', color: duplicateGroups.length > 0 ? '#f44336' : '#4caf50' }}>
                {duplicateGroups.length}
              </strong>
            </div>
          </div>
        </div>
      </div>
      
      {/* Duplicate Groups */}
      {duplicateGroups.length > 0 && (
        <div className="modern-grid" style={{ gridTemplateColumns: '1fr' }}>
          {duplicateGroups.map((group, groupIndex) => (
            <div key={groupIndex} className="modern-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '18px' }}>
                    Группа #{groupIndex + 1}
                  </h3>
                  <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
                    {group.contacts.length} {t.contacts} • {t.similarity}: {Math.round(group.avgSimilarity * 100)}%
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedGroup(group);
                    setMergeSelection({});
                  }}
                  className="modern-btn modern-btn-warning"
                >
                  🔗 {t.merge}
                </button>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
                {group.contacts.map((contact, idx) => (
                  <div
                    key={contact.id}
                    style={{
                      padding: '12px',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      backgroundColor: '#f9f9f9'
                    }}
                  >
                    <div style={{ fontSize: '14px' }}>
                      <div style={{ fontWeight: '500', marginBottom: '8px' }}>
                        {contact.full_name || '—'}
                      </div>
                      {contact.company && (
                        <div style={{ color: '#666', fontSize: '13px' }}>
                          🏢 {contact.company}
                        </div>
                      )}
                      {contact.email && (
                        <div style={{ color: '#666', fontSize: '13px' }}>
                          📧 {contact.email}
                        </div>
                      )}
                      {contact.phone && (
                        <div style={{ color: '#666', fontSize: '13px' }}>
                          📱 {contact.phone}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Merge Modal */}
      {selectedGroup && (
        <div className="modal-overlay" onClick={() => setSelectedGroup(null)}>
          <div className="modal modern-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
            <h3>🔗 {t.merge}</h3>
            <p style={{ marginBottom: '20px', color: '#666' }}>{t.selectMaster}</p>
            
            <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              {selectedGroup.contacts.map((contact) => (
                <div
                  key={contact.id}
                  onClick={() => setMergeSelection({ master: contact.id })}
                  style={{
                    padding: '16px',
                    border: `2px solid ${mergeSelection.master === contact.id ? '#4caf50' : '#ddd'}`,
                    borderRadius: '8px',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    backgroundColor: mergeSelection.master === contact.id ? '#f0f8f0' : '#fff',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500', marginBottom: '8px', fontSize: '16px' }}>
                        {mergeSelection.master === contact.id && '✅ '} {contact.full_name || '—'}
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', fontSize: '14px', color: '#666' }}>
                        {contact.company && <div>🏢 {contact.company}</div>}
                        {contact.position && <div>💼 {contact.position}</div>}
                        {contact.email && <div>📧 {contact.email}</div>}
                        {contact.phone && <div>📱 {contact.phone}</div>}
                        {contact.address && <div>📍 {contact.address}</div>}
                        {contact.website && <div>🔗 {contact.website}</div>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button
                onClick={() => setSelectedGroup(null)}
                className="modern-btn modern-btn-secondary"
                style={{ flex: 1 }}
              >
                {t.cancel}
              </button>
              <button
                onClick={() => {
                  if (!mergeSelection.master) {
                    toast.error(t.selectMaster);
                    return;
                  }
                  
                  const slaveIds = selectedGroup.contacts
                    .filter(c => c.id !== mergeSelection.master)
                    .map(c => c.id);
                  
                  mergeContacts(mergeSelection.master, slaveIds);
                }}
                disabled={!mergeSelection.master || merging}
                className="modern-btn modern-btn-success"
                style={{ flex: 1 }}
              >
                {merging ? '⏳ ' + t.analyzing : '🔗 ' + t.mergeSelected}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {duplicateGroups.length === 0 && !analyzing && (
        <div className="modern-card" style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✨</div>
          <p style={{ fontSize: '18px', color: '#666' }}>{t.noDuplicates}</p>
        </div>
      )}
    </div>
  );
};

export default DuplicateManager;
