import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { LoadingSpinner } from './common';
import { getDuplicatesContacts, mergeDuplicates } from '../modules/duplicates/api/duplicatesApi';

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

  // Загрузка всех контактов - изолированный микросервис
  const loadContacts = async () => {
    try {
      // Use isolated duplicates API microservice
      const data = await getDuplicatesContacts();
      setContacts(data);
      
      if (data.length === 0) {
        toast.error(lang === 'ru' ? 'Нет контактов для анализа' : 'No contacts to analyze');
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
      
      // Handle auth errors
      if (error.message === 'UNAUTHORIZED') {
        toast.error(lang === 'ru' ? 'Сессия истекла. Войдите снова' : 'Session expired. Please login');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
        return;
      }
      
      // Handle no token
      if (error.message === 'No authentication token') {
        toast.error(lang === 'ru' ? 'Необходима авторизация' : 'Authorization required');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
        return;
      }
      
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

  // Вычисление превью изменений
  const calculateMergePreview = (masterId, slaveIds) => {
    const master = selectedGroup.contacts.find(c => c.id === masterId);
    const slaves = selectedGroup.contacts.filter(c => slaveIds.includes(c.id));
    
    if (!master) return [];
    
    // ВСЕ поля Contact для сравнения
    const fields = [
      { key: 'full_name', label: t.name },
      { key: 'first_name', label: lang === 'ru' ? 'Имя' : 'First Name' },
      { key: 'last_name', label: lang === 'ru' ? 'Фамилия' : 'Last Name' },
      { key: 'middle_name', label: lang === 'ru' ? 'Отчество' : 'Middle Name' },
      { key: 'company', label: t.company },
      { key: 'position', label: t.position },
      { key: 'department', label: lang === 'ru' ? 'Отдел' : 'Department' },
      { key: 'email', label: t.email },
      { key: 'phone', label: t.phone },
      { key: 'phone_mobile', label: lang === 'ru' ? 'Мобильный' : 'Mobile Phone' },
      { key: 'phone_work', label: lang === 'ru' ? 'Рабочий тел.' : 'Work Phone' },
      { key: 'phone_additional', label: lang === 'ru' ? 'Доп. телефон' : 'Additional Phone' },
      { key: 'fax', label: lang === 'ru' ? 'Факс' : 'Fax' },
      { key: 'address', label: t.address },
      { key: 'address_additional', label: lang === 'ru' ? 'Доп. адрес' : 'Additional Address' },
      { key: 'website', label: t.website },
      { key: 'birthday', label: lang === 'ru' ? 'День рождения' : 'Birthday' },
      { key: 'source', label: lang === 'ru' ? 'Источник' : 'Source' },
      { key: 'status', label: lang === 'ru' ? 'Статус' : 'Status' },
      { key: 'priority', label: lang === 'ru' ? 'Приоритет' : 'Priority' },
      { key: 'comment', label: lang === 'ru' ? 'Комментарий' : 'Comment' },
      { key: 'qr_data', label: lang === 'ru' ? 'QR данные' : 'QR Data' }
    ];
    
    const changes = [];
    
    fields.forEach(field => {
      const masterValue = master[field.key] || '';
      
      // Проверяем каждый slave контакт
      slaves.forEach(slave => {
        const slaveValue = slave[field.key] || '';
        
        // Если у master пусто, а у slave есть значение (ДОБАВЛЕНИЕ - ЗЕЛЕНЫЙ)
        if (!masterValue && slaveValue) {
          changes.push({
            field: field.label,
            type: 'add',
            from: '',
            to: slaveValue,
            color: '#4caf50',
            icon: '➕',
            description: lang === 'ru' ? 'Добавится' : 'Will add'
          });
        }
        // Если у master есть, а у slave тоже есть но РАЗНОЕ (КОНФЛИКТ - СИНИЙ)
        // Master сохранит свое значение, slave значение будет потеряно
        else if (masterValue && slaveValue && masterValue !== slaveValue) {
          changes.push({
            field: field.label,
            type: 'conflict',
            masterValue: masterValue,
            slaveValue: slaveValue,
            color: '#2196f3',
            icon: '🔄',
            description: lang === 'ru' ? 'Конфликт (master сохранит свое)' : 'Conflict (master will keep its value)'
          });
        }
        // Если у master есть, а у slave пусто (ПОТЕРЯ - КРАСНЫЙ)
        // Slave контакт потеряет это поле
        else if (masterValue && !slaveValue) {
          changes.push({
            field: field.label,
            type: 'loss',
            masterValue: masterValue,
            slaveValue: '',
            color: '#f44336',
            icon: '⚠️',
            description: lang === 'ru' ? 'У удаляемого контакта пусто' : 'Deleted contact has no value'
          });
        }
      });
    });
    
    // Убираем дубликаты
    const uniqueChanges = changes.filter((change, index, self) =>
      index === self.findIndex(c => 
        c.field === change.field && 
        c.type === change.type && 
        (c.to === change.to || (c.masterValue === change.masterValue && c.slaveValue === change.slaveValue))
      )
    );
    
    return uniqueChanges;
  };

  // Объединение контактов
  const mergeContacts = async (masterId, slaveIds) => {
    setMerging(true);
    
    try {
      // Use isolated duplicates API microservice
      await mergeDuplicates(masterId, slaveIds);
      
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
      
      // Handle auth errors
      if (error.message === 'UNAUTHORIZED') {
        toast.error(lang === 'ru' ? 'Сессия истекла. Войдите снова' : 'Session expired. Please login');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
        return;
      }
      
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
          <div className="modal modern-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', width: '90%' }}>
            <h3>🔗 {t.merge}</h3>
            <p style={{ marginBottom: '20px', color: '#666' }}>
              {lang === 'ru' 
                ? '1️⃣ Выберите основной контакт (зеленым), 2️⃣ Отметьте какие контакты удалить (красным)' 
                : '1️⃣ Select master contact (green), 2️⃣ Check which contacts to delete (red)'}
            </p>
            
            <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              {selectedGroup.contacts.map((contact) => {
                const isMaster = mergeSelection.master === contact.id;
                const isSelectedForDeletion = mergeSelection.slavesToDelete?.includes(contact.id);
                
                return (
                  <div
                    key={contact.id}
                    style={{
                      padding: '16px',
                      border: `2px solid ${
                        isMaster ? '#4caf50' : 
                        isSelectedForDeletion ? '#f44336' : 
                        '#ddd'
                      }`,
                      borderRadius: '8px',
                      marginBottom: '12px',
                      backgroundColor: isMaster ? '#f0f8f0' : isSelectedForDeletion ? '#ffebee' : '#fff',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'start' }}>
                      {/* Master selection */}
                      <div 
                        style={{ 
                          cursor: 'pointer',
                          padding: '8px',
                          borderRadius: '4px',
                          backgroundColor: isMaster ? '#4caf50' : '#e0e0e0',
                          color: isMaster ? '#fff' : '#666',
                          fontWeight: '500',
                          fontSize: '14px',
                          minWidth: '80px',
                          textAlign: 'center'
                        }}
                        onClick={() => setMergeSelection({ 
                          master: contact.id,
                          slavesToDelete: mergeSelection.slavesToDelete || []
                        })}
                      >
                        {isMaster ? '✅ Master' : '👆 Master'}
                      </div>
                      
                      {/* Delete checkbox */}
                      {!isMaster && (
                        <div 
                          style={{ 
                            cursor: 'pointer',
                            padding: '8px',
                            borderRadius: '4px',
                            backgroundColor: isSelectedForDeletion ? '#f44336' : '#e0e0e0',
                            color: isSelectedForDeletion ? '#fff' : '#666',
                            fontWeight: '500',
                            fontSize: '14px',
                            minWidth: '80px',
                            textAlign: 'center'
                          }}
                          onClick={() => {
                            const currentSlaves = mergeSelection.slavesToDelete || [];
                            const newSlaves = isSelectedForDeletion
                              ? currentSlaves.filter(id => id !== contact.id)
                              : [...currentSlaves, contact.id];
                            setMergeSelection({
                              ...mergeSelection,
                              slavesToDelete: newSlaves
                            });
                          }}
                        >
                          {isSelectedForDeletion ? '🗑️ Удалить' : '☐ Удалить'}
                        </div>
                      )}
                      
                      {/* Contact info */}
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '500', marginBottom: '8px', fontSize: '16px' }}>
                          {contact.full_name || '—'}
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
                );
              })}
            </div>
            
            {/* Merge Preview */}
            {mergeSelection.master && mergeSelection.slavesToDelete && mergeSelection.slavesToDelete.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h4 style={{ marginBottom: '16px', color: '#333' }}>
                  📋 {lang === 'ru' ? `Превью изменений (удаляется: ${mergeSelection.slavesToDelete.length})` : `Changes Preview (deleting: ${mergeSelection.slavesToDelete.length})`}
                </h4>
                
                {(() => {
                  const slaveIds = mergeSelection.slavesToDelete || [];
                  const preview = calculateMergePreview(mergeSelection.master, slaveIds);
                  
                  if (preview.length === 0) {
                    return (
                      <div style={{ 
                        padding: '16px', 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: '8px',
                        textAlign: 'center',
                        color: '#666'
                      }}>
                        {lang === 'ru' ? 'Нет изменений для отображения' : 'No changes to display'}
                      </div>
                    );
                  }
                  
                  return (
                    <div style={{ 
                      maxHeight: '300px', 
                      overflowY: 'auto',
                      border: '1px solid #e0e0e0',
                      borderRadius: '8px',
                      backgroundColor: '#fafafa'
                    }}>
                      {preview.map((change, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '12px 16px',
                            borderBottom: idx < preview.length - 1 ? '1px solid #e0e0e0' : 'none',
                            display: 'flex',
                            alignItems: 'start',
                            gap: '12px',
                            backgroundColor: change.type === 'add' ? '#f0f8f0' : 
                                           change.type === 'conflict' ? '#e3f2fd' : 
                                           change.type === 'loss' ? '#ffebee' : '#fff'
                          }}
                        >
                          {/* Icon */}
                          <div style={{ fontSize: '20px', marginTop: '2px' }}>
                            {change.icon}
                          </div>
                          
                          {/* Content */}
                          <div style={{ flex: 1 }}>
                            <div style={{ 
                              fontWeight: '500', 
                              marginBottom: '6px',
                              fontSize: '14px',
                              color: '#333'
                            }}>
                              {change.field}
                            </div>
                            
                            {/* ДОБАВЛЕНИЕ (зеленый) */}
                            {change.type === 'add' && (
                              <div>
                                <div style={{ 
                                  color: change.color,
                                  fontWeight: '500',
                                  fontSize: '13px',
                                  marginBottom: '2px'
                                }}>
                                  {change.description}:
                                </div>
                                <div style={{ 
                                  fontSize: '13px',
                                  padding: '4px 8px',
                                  backgroundColor: '#fff',
                                  borderRadius: '4px',
                                  border: `1px solid ${change.color}`
                                }}>
                                  "{change.to}"
                                </div>
                              </div>
                            )}
                            
                            {/* КОНФЛИКТ (синий) */}
                            {change.type === 'conflict' && (
                              <div>
                                <div style={{ 
                                  color: change.color,
                                  fontWeight: '500',
                                  fontSize: '13px',
                                  marginBottom: '4px'
                                }}>
                                  {change.description}
                                </div>
                                <div style={{ fontSize: '13px' }}>
                                  <div style={{ 
                                    padding: '4px 8px',
                                    backgroundColor: '#fff',
                                    borderRadius: '4px',
                                    border: '1px solid #f44336',
                                    marginBottom: '4px',
                                    textDecoration: 'line-through',
                                    color: '#666'
                                  }}>
                                    {lang === 'ru' ? 'Удалится' : 'Will be lost'}: "{change.slaveValue}"
                                  </div>
                                  <div style={{ 
                                    padding: '4px 8px',
                                    backgroundColor: '#fff',
                                    borderRadius: '4px',
                                    border: `1px solid ${change.color}`,
                                    fontWeight: '500'
                                  }}>
                                    {lang === 'ru' ? 'Сохранится' : 'Will keep'}: "{change.masterValue}"
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* ПОТЕРЯ (красный) */}
                            {change.type === 'loss' && (
                              <div>
                                <div style={{ 
                                  color: change.color,
                                  fontWeight: '500',
                                  fontSize: '13px',
                                  marginBottom: '2px'
                                }}>
                                  {change.description}
                                </div>
                                <div style={{ 
                                  fontSize: '13px',
                                  padding: '4px 8px',
                                  backgroundColor: '#fff',
                                  borderRadius: '4px',
                                  border: `1px solid ${change.color}`
                                }}>
                                  {lang === 'ru' ? 'Сохранится master' : 'Master will keep'}: "{change.masterValue}"
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })()}
                
                <div style={{ 
                  marginTop: '12px', 
                  padding: '12px', 
                  backgroundColor: '#e3f2fd', 
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: '#1976d2'
                }}>
                  <strong>ℹ️ {lang === 'ru' ? 'Важно' : 'Important'}:</strong> {lang === 'ru' 
                    ? `Основной контакт сохранит все свои данные. Пустые поля будут заполнены из ${mergeSelection.slavesToDelete.length} удаляемых контактов. Не выбранные контакты (${selectedGroup.contacts.length - 1 - mergeSelection.slavesToDelete.length}) ОСТАНУТСЯ без изменений.` 
                    : `Master contact will keep all its data. Empty fields will be filled from ${mergeSelection.slavesToDelete.length} deleted contacts. Unselected contacts (${selectedGroup.contacts.length - 1 - mergeSelection.slavesToDelete.length}) will REMAIN unchanged.`}
                </div>
              </div>
            )}
            
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
                  
                  if (!mergeSelection.slavesToDelete || mergeSelection.slavesToDelete.length === 0) {
                    toast.error(lang === 'ru' ? 'Выберите контакты для удаления' : 'Select contacts to delete');
                    return;
                  }
                  
                  const slaveIds = mergeSelection.slavesToDelete;
                  
                  mergeContacts(mergeSelection.master, slaveIds);
                }}
                disabled={!mergeSelection.master || !mergeSelection.slavesToDelete || mergeSelection.slavesToDelete.length === 0 || merging}
                className="modern-btn modern-btn-success"
                style={{ flex: 1 }}
              >
                {merging ? '⏳ ' + t.analyzing : `🔗 ${lang === 'ru' ? 'Объединить' : 'Merge'} (${mergeSelection.slavesToDelete?.length || 0})`}
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
