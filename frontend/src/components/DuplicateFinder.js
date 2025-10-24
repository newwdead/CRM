import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

export default function DuplicateFinder({ lang = 'ru' }) {
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(0.6);
  const [merging, setMerging] = useState(null);

  const t = {
    ru: {
      title: 'Поиск дубликатов',
      subtitle: 'Автоматическое обнаружение похожих контактов',
      threshold: 'Порог схожести',
      thresholdHelp: 'Чем выше значение, тем строже поиск (0.0 - 1.0)',
      findDuplicates: 'Найти дубликаты',
      loading: 'Поиск дубликатов...',
      noDuplicates: 'Дубликаты не найдены',
      duplicatesFound: 'Найдено групп дубликатов',
      group: 'Группа',
      similarity: 'Схожесть',
      reasons: 'Причины',
      merge: 'Объединить',
      merging: 'Объединение...',
      selectPrimary: 'Выберите основной контакт (который оставить)',
      cancel: 'Отмена',
      confirmMerge: 'Подтвердить объединение',
      mergeSuccess: 'Контакты успешно объединены!',
      mergeError: 'Ошибка объединения контактов',
      loadError: 'Ошибка загрузки дубликатов',
      phone: 'Телефон',
      email: 'Email',
      company: 'Компания',
      position: 'Должность',
      identicalPhone: 'Одинаковый телефон',
      identicalMobile: 'Одинаковый мобильный',
      identicalEmail: 'Одинаковый email',
      similarName: 'Похожие имена',
      sameCompany: 'Одна компания',
    },
    en: {
      title: 'Duplicate Finder',
      subtitle: 'Automatic detection of similar contacts',
      threshold: 'Similarity threshold',
      thresholdHelp: 'Higher value = stricter search (0.0 - 1.0)',
      findDuplicates: 'Find Duplicates',
      loading: 'Searching for duplicates...',
      noDuplicates: 'No duplicates found',
      duplicatesFound: 'Duplicate groups found',
      group: 'Group',
      similarity: 'Similarity',
      reasons: 'Reasons',
      merge: 'Merge',
      merging: 'Merging...',
      selectPrimary: 'Select primary contact (to keep)',
      cancel: 'Cancel',
      confirmMerge: 'Confirm Merge',
      mergeSuccess: 'Contacts merged successfully!',
      mergeError: 'Error merging contacts',
      loadError: 'Error loading duplicates',
      phone: 'Phone',
      email: 'Email',
      company: 'Company',
      position: 'Position',
      identicalPhone: 'Identical phone',
      identicalMobile: 'Identical mobile',
      identicalEmail: 'Identical email',
      similarName: 'Similar names',
      sameCompany: 'Same company',
    }
  }[lang] || {};

  const loadDuplicates = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/duplicates/?threshold=${threshold}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Failed to load duplicates');
      
      const data = await res.json();
      setDuplicates(data.duplicates || []);
      
      if (data.total_groups === 0) {
        toast.success(t.noDuplicates, { icon: '✅', duration: 3000 });
      } else {
        toast.success(`${t.duplicatesFound}: ${data.total_groups}`, { icon: '🔍', duration: 3000 });
      }
    } catch (error) {
      console.error('Error loading duplicates:', error);
      toast.error(t.loadError, { icon: '❌' });
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async (group, primaryIndex) => {
    const primary = group.contacts[primaryIndex];
    const secondaries = group.contacts.filter((_, idx) => idx !== primaryIndex);

    if (secondaries.length === 0) return;

    try {
      setMerging(group.group_id);
      
      const token = localStorage.getItem('token');
      
      // Merge all secondaries into primary (one by one)
      for (const secondary of secondaries) {
        const res = await fetch('/api/duplicates/merge', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            primary_id: primary.contact.id,
            secondary_id: secondary.contact.id
          })
        });

        if (!res.ok) {
          const error = await res.json();
          throw new Error(error.detail || 'Merge failed');
        }
      }

      toast.success(t.mergeSuccess, { icon: '✅', duration: 4000 });
      
      // Reload duplicates
      await loadDuplicates();
      
      // Refresh contacts list
      window.dispatchEvent(new Event('refresh-contacts'));
      
    } catch (error) {
      console.error('Error merging contacts:', error);
      toast.error(`${t.mergeError}: ${error.message}`, { icon: '❌', duration: 5000 });
    } finally {
      setMerging(null);
    }
  };

  const translateReason = (reason) => {
    if (reason.includes('identical_phone')) return t.identicalPhone;
    if (reason.includes('identical_mobile')) return t.identicalMobile;
    if (reason.includes('identical_email')) return t.identicalEmail;
    if (reason.includes('similar_name')) return t.similarName;
    if (reason.includes('same_company')) return t.sameCompany;
    return reason;
  };

  return (
    <div className="modern-card">
      <h2 style={{ marginBottom: '8px' }}>🔍 {t.title}</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>{t.subtitle}</p>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', marginBottom: '24px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            {t.threshold}: <strong>{threshold.toFixed(2)}</strong>
          </label>
          <input
            type="range"
            min="0.3"
            max="0.9"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            style={{ width: '100%' }}
          />
          <small style={{ color: 'var(--text-secondary)' }}>{t.thresholdHelp}</small>
        </div>

        <button 
          onClick={loadDuplicates} 
          disabled={loading}
          style={{ 
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: 500
          }}
        >
          {loading ? `⏳ ${t.loading}` : `🔍 ${t.findDuplicates}`}
        </button>
      </div>

      {/* Results */}
      {duplicates.length === 0 && !loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          color: 'var(--text-secondary)',
          fontSize: '18px'
        }}>
          📭 {t.noDuplicates}
        </div>
      ) : (
        <AnimatePresence>
          {duplicates.map((group, groupIdx) => (
            <DuplicateGroup
              key={group.group_id}
              group={group}
              groupIdx={groupIdx}
              onMerge={handleMerge}
              merging={merging === group.group_id}
              translateReason={translateReason}
              t={t}
            />
          ))}
        </AnimatePresence>
      )}
    </div>
  );
}

function DuplicateGroup({ group, groupIdx, onMerge, merging, translateReason, t }) {
  const [selectedPrimary, setSelectedPrimary] = useState(0);
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ delay: groupIdx * 0.1 }}
      style={{
        border: '2px solid var(--border-color)',
        borderRadius: 'var(--radius)',
        padding: '20px',
        marginBottom: '20px',
        background: 'var(--bg-secondary)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0 }}>
          {t.group} #{groupIdx + 1} 
          <span style={{ 
            marginLeft: '12px', 
            fontSize: '14px', 
            padding: '4px 12px',
            background: 'var(--primary-color)',
            color: 'white',
            borderRadius: '12px'
          }}>
            {t.similarity}: {(group.max_score * 100).toFixed(0)}%
          </span>
        </h3>
        
        {!showMergeConfirm && (
          <button 
            onClick={() => setShowMergeConfirm(true)}
            className="secondary"
            disabled={merging}
          >
            🔗 {t.merge}
          </button>
        )}
      </div>

      {/* Contacts in group */}
      <div style={{ display: 'grid', gap: '12px' }}>
        {group.contacts.map((item, idx) => {
          const c = item.contact;
          const isSelected = idx === selectedPrimary;
          
          return (
            <motion.div
              key={c.id}
              onClick={() => showMergeConfirm && setSelectedPrimary(idx)}
              style={{
                padding: '16px',
                border: `2px solid ${isSelected && showMergeConfirm ? 'var(--primary-color)' : 'var(--border-color)'}`,
                borderRadius: 'var(--radius)',
                background: isSelected && showMergeConfirm ? 'var(--primary-light)' : 'white',
                cursor: showMergeConfirm ? 'pointer' : 'default',
                transition: 'all 0.2s ease'
              }}
              whileHover={showMergeConfirm ? { scale: 1.02 } : {}}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    {showMergeConfirm && (
                      <input
                        type="radio"
                        name={`primary-${group.group_id}`}
                        checked={isSelected}
                        onChange={() => setSelectedPrimary(idx)}
                        style={{ cursor: 'pointer' }}
                      />
                    )}
                    <strong style={{ fontSize: '16px' }}>
                      {c.full_name || `${c.first_name || ''} ${c.last_name || ''}`.trim() || 'N/A'}
                    </strong>
                  </div>
                  
                  <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    {c.company && <div>🏢 {c.company}</div>}
                    {c.position && <div>💼 {c.position}</div>}
                    {c.phone && <div>📱 {c.phone}</div>}
                    {c.email && <div>✉️ {c.email}</div>}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ 
                    fontSize: '20px', 
                    fontWeight: 'bold',
                    color: item.score >= 0.8 ? 'var(--error-color)' : 
                           item.score >= 0.6 ? 'var(--warning-color)' : 'var(--text-color)'
                  }}>
                    {(item.score * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {item.reasons.map(r => translateReason(r)).join(', ')}
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Merge confirmation */}
      {showMergeConfirm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          style={{
            marginTop: '16px',
            padding: '16px',
            background: 'var(--warning-bg)',
            border: '1px solid var(--warning-color)',
            borderRadius: 'var(--radius)'
          }}
        >
          <p style={{ margin: '0 0 12px 0', fontWeight: 500 }}>
            ⚠️ {t.selectPrimary}
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => {
                onMerge(group, selectedPrimary);
                setShowMergeConfirm(false);
              }}
              disabled={merging}
              style={{ flex: 1 }}
            >
              {merging ? `⏳ ${t.merging}` : `✅ ${t.confirmMerge}`}
            </button>
            <button
              onClick={() => setShowMergeConfirm(false)}
              className="secondary"
              disabled={merging}
              style={{ flex: 1 }}
            >
              ❌ {t.cancel}
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

