import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import DuplicateMergeModal from './DuplicateMergeModal';

export default function DuplicatesPanel({ lang = 'ru' }) {
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [similarityFilter, setSimilarityFilter] = useState(0.7);
  const [selectedForMerge, setSelectedForMerge] = useState(null);
  const [selectedContact, setSelectedContact] = useState(null);

  const t = lang === 'ru' ? {
    title: 'Управление дубликатами',
    status: 'Статус',
    pending: 'Ожидает',
    reviewed: 'Проверено',
    merged: 'Объединено',
    ignored: 'Игнорировано',
    all: 'Все',
    minSimilarity: 'Минимальная схожесть',
    findDuplicates: 'Найти дубликаты',
    contact1: 'Контакт 1',
    contact2: 'Контакт 2',
    similarity: 'Схожесть',
    matchFields: 'Совпадения',
    actions: 'Действия',
    merge: 'Объединить',
    ignore: 'Игнорировать',
    noResults: 'Дубликаты не найдены',
    autoDetected: 'Авто',
    manual: 'Ручной',
    detectedAt: 'Обнаружено',
    finding: 'Поиск...',
    loading: 'Загрузка...',
    ignored_success: 'Дубликат помечен как игнорируемый',
    error: 'Ошибка',
    total: 'Всего найдено'
  } : {
    title: 'Duplicate Management',
    status: 'Status',
    pending: 'Pending',
    reviewed: 'Reviewed',
    merged: 'Merged',
    ignored: 'Ignored',
    all: 'All',
    minSimilarity: 'Min Similarity',
    findDuplicates: 'Find Duplicates',
    contact1: 'Contact 1',
    contact2: 'Contact 2',
    similarity: 'Similarity',
    matchFields: 'Matches',
    actions: 'Actions',
    merge: 'Merge',
    ignore: 'Ignore',
    noResults: 'No duplicates found',
    autoDetected: 'Auto',
    manual: 'Manual',
    detectedAt: 'Detected',
    finding: 'Finding...',
    loading: 'Loading...',
    ignored_success: 'Duplicate marked as ignored',
    error: 'Error',
    total: 'Total found'
  };

  const loadDuplicates = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      params.append('limit', '1000');

      const res = await fetch(`/api/duplicates?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setDuplicates(data.duplicates || []);
      } else {
        toast.error(t.error);
      }
    } catch (error) {
      console.error('Error loading duplicates:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDuplicates();
  }, [statusFilter]);

  const handleFindDuplicates = async () => {
    try {
      setLoading(true);
      toast.loading(t.finding);
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/duplicates/find?threshold=${similarityFilter}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        toast.dismiss();
        toast.success(`${t.total}: ${data.found}`);
        loadDuplicates();
      } else {
        toast.dismiss();
        toast.error(t.error);
      }
    } catch (error) {
      toast.dismiss();
      console.error('Error finding duplicates:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const handleIgnore = async (duplicateId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/duplicates/${duplicateId}/ignore`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success(t.ignored_success);
        loadDuplicates();
      } else {
        toast.error(t.error);
      }
    } catch (error) {
      console.error('Error ignoring duplicate:', error);
      toast.error(t.error);
    }
  };

  const handleMerge = (dup) => {
    setSelectedForMerge(dup);
    setSelectedContact(dup.contact_1);
  };

  const filteredDuplicates = duplicates.filter(dup => 
    dup.similarity_score >= similarityFilter
  );

  return (
    <div style={{ padding: '20px' }}>
      <h2>{t.title}</h2>

      {/* Filters */}
      <div style={{ 
        display: 'flex', 
        gap: '20px', 
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        flexWrap: 'wrap'
      }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>{t.status}:</label>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
          >
            <option value="all">{t.all}</option>
            <option value="pending">{t.pending}</option>
            <option value="reviewed">{t.reviewed}</option>
            <option value="merged">{t.merged}</option>
            <option value="ignored">{t.ignored}</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
            {t.minSimilarity}: {Math.round(similarityFilter * 100)}%
          </label>
          <input 
            type="range" 
            min="0.5" 
            max="1.0" 
            step="0.05"
            value={similarityFilter}
            onChange={(e) => setSimilarityFilter(parseFloat(e.target.value))}
            style={{ width: '200px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button 
            onClick={handleFindDuplicates}
            disabled={loading}
            style={{
              padding: '8px 20px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: '500'
            }}
          >
            {loading ? t.finding : t.findDuplicates}
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div style={{ marginBottom: '20px', fontSize: '14px', color: '#666' }}>
        {t.total}: <strong>{filteredDuplicates.length}</strong>
      </div>

      {/* Table */}
      {loading && !duplicates.length ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          {t.loading}
        </div>
      ) : filteredDuplicates.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          {t.noResults}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.contact1}</th>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.contact2}</th>
                <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>{t.similarity}</th>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>{t.matchFields}</th>
                <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>{t.detectedAt}</th>
                <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>{t.actions}</th>
              </tr>
            </thead>
            <tbody>
              {filteredDuplicates.map(dup => (
                <tr key={dup.id} style={{ borderBottom: '1px solid #ddd' }}>
                  <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                    <div style={{ fontWeight: '500' }}>
                      {dup.contact_1.full_name || '—'}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      {dup.contact_1.email && <div>📧 {dup.contact_1.email}</div>}
                      {dup.contact_1.phone && <div>📞 {dup.contact_1.phone}</div>}
                      {dup.contact_1.company && <div>🏢 {dup.contact_1.company}</div>}
                    </div>
                  </td>
                  <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                    <div style={{ fontWeight: '500' }}>
                      {dup.contact_2.full_name || '—'}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      {dup.contact_2.email && <div>📧 {dup.contact_2.email}</div>}
                      {dup.contact_2.phone && <div>📞 {dup.contact_2.phone}</div>}
                      {dup.contact_2.company && <div>🏢 {dup.contact_2.company}</div>}
                    </div>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>
                    <div style={{
                      display: 'inline-block',
                      padding: '4px 12px',
                      backgroundColor: dup.similarity_score >= 0.9 ? '#4CAF50' : dup.similarity_score >= 0.8 ? '#FF9800' : '#2196F3',
                      color: 'white',
                      borderRadius: '12px',
                      fontWeight: 'bold',
                      fontSize: '13px'
                    }}>
                      {Math.round(dup.similarity_score * 100)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
                      {dup.auto_detected ? t.autoDetected : t.manual}
                    </div>
                  </td>
                  <td style={{ padding: '12px', border: '1px solid #ddd', fontSize: '12px' }}>
                    {dup.match_fields && Object.keys(dup.match_fields).length > 0 ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {Object.entries(dup.match_fields).map(([field, score]) => (
                          <span
                            key={field}
                            style={{
                              padding: '2px 8px',
                              backgroundColor: score >= 0.9 ? '#e8f5e9' : '#fff3e0',
                              border: `1px solid ${score >= 0.9 ? '#4CAF50' : '#FF9800'}`,
                              borderRadius: '4px',
                              fontSize: '11px'
                            }}
                          >
                            {field}: {Math.round(score * 100)}%
                          </span>
                        ))}
                      </div>
                    ) : '—'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd', fontSize: '12px', color: '#666' }}>
                    {dup.detected_at ? new Date(dup.detected_at).toLocaleDateString() : '—'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>
                    {dup.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <button
                          onClick={() => handleMerge(dup)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          {t.merge}
                        </button>
                        <button
                          onClick={() => handleIgnore(dup.id)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#f44336',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          {t.ignore}
                        </button>
                      </div>
                    )}
                    {dup.status === 'merged' && (
                      <span style={{ color: '#4CAF50', fontWeight: '500' }}>✓ {t.merged}</span>
                    )}
                    {dup.status === 'ignored' && (
                      <span style={{ color: '#999' }}>⊘ {t.ignored}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Merge Modal */}
      {selectedForMerge && selectedContact && (
        <DuplicateMergeModal
          lang={lang}
          contact={selectedContact}
          duplicates={[selectedForMerge]}
          onClose={() => {
            setSelectedForMerge(null);
            setSelectedContact(null);
          }}
          onMerged={() => {
            setSelectedForMerge(null);
            setSelectedContact(null);
            loadDuplicates();
          }}
        />
      )}
    </div>
  );
}

