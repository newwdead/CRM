import React, { useState, useEffect, useRef } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

export default function SearchOverlay({ lang = 'ru', onContactSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const debounceTimer = useRef(null);

  const t = lang === 'ru' ? {
    placeholder: 'Поиск контактов, компаний, email, телефонов...',
    searching: 'Поиск...',
    noResults: 'Ничего не найдено',
    recentSearches: 'Недавние поиски',
    contacts: 'Контакты',
    companies: 'Компании',
    hint: 'Нажмите Ctrl+K для поиска',
    pressEnter: 'Enter - открыть',
    pressEsc: 'Esc - закрыть',
    useArrows: '↑↓ - навигация',
  } : {
    placeholder: 'Search contacts, companies, emails, phones...',
    searching: 'Searching...',
    noResults: 'No results found',
    recentSearches: 'Recent searches',
    contacts: 'Contacts',
    companies: 'Companies',
    hint: 'Press Ctrl+K to search',
    pressEnter: 'Enter - open',
    pressEsc: 'Esc - close',
    useArrows: '↑↓ - navigate',
  };

  // Hotkey: Ctrl+K или Cmd+K
  useHotkeys('ctrl+k, cmd+k', (e) => {
    e.preventDefault();
    setIsOpen(true);
  }, { enableOnFormTags: true });

  // Hotkey: ESC
  useHotkeys('esc', () => {
    if (isOpen) {
      setIsOpen(false);
      setQuery('');
      setResults([]);
    }
  }, { enableOnFormTags: true, enabled: isOpen });

  // Arrow navigation
  useHotkeys('up', (e) => {
    if (isOpen && results.length > 0) {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    }
  }, { enableOnFormTags: true, enabled: isOpen });

  useHotkeys('down', (e) => {
    if (isOpen && results.length > 0) {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    }
  }, { enableOnFormTags: true, enabled: isOpen });

  // Enter to select
  useHotkeys('enter', (e) => {
    if (isOpen && results.length > 0 && results[selectedIndex]) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    }
  }, { enableOnFormTags: true, enabled: isOpen });

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(async () => {
      await performSearch(query);
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query]);

  const performSearch = async (searchQuery) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/contacts/search/?q=${encodeURIComponent(searchQuery)}&limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data.items || []);
        setSelectedIndex(0);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (contact) => {
    // Save to recent searches
    const recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    const updated = [
      { id: contact.id, name: contact.full_name || contact.first_name, company: contact.company },
      ...recent.filter(r => r.id !== contact.id)
    ].slice(0, 5);
    localStorage.setItem('recent_searches', JSON.stringify(updated));

    // Callback to parent
    if (onContactSelect) {
      onContactSelect(contact.id);
    }

    // Close overlay
    setIsOpen(false);
    setQuery('');
    setResults([]);
  };

  if (!isOpen) {
    return (
      <div 
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '8px 16px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius)',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          transition: 'all 0.2s',
          zIndex: 999
        }}
        onClick={() => setIsOpen(true)}
        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--primary-light)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-secondary)'}
      >
        🔍 {t.hint}
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
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        padding: '100px 20px',
        zIndex: 10000,
        animation: 'fadeIn 0.2s'
      }}
      onClick={() => { setIsOpen(false); setQuery(''); setResults([]); }}
    >
      <div 
        style={{
          width: '100%',
          maxWidth: '600px',
          background: 'var(--bg-color)',
          borderRadius: 'var(--radius)',
          boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
          overflow: 'hidden',
          animation: 'slideDown 0.3s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)' }}>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.placeholder}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              border: 'none',
              background: 'transparent',
              color: 'var(--text-color)',
              outline: 'none'
            }}
          />
        </div>

        {/* Results */}
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <div className="spinner" style={{ margin: '0 auto 12px' }}></div>
              {t.searching}
            </div>
          ) : results.length > 0 ? (
            <div>
              {results.map((contact, index) => (
                <div
                  key={contact.id}
                  onClick={() => handleSelect(contact)}
                  style={{
                    padding: '12px 20px',
                    borderBottom: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    background: index === selectedIndex ? 'var(--bg-secondary)' : 'transparent',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                    {contact.last_name || contact.first_name ? (
                      `${contact.last_name || ''} ${contact.first_name || ''} ${contact.middle_name || ''}`.trim()
                    ) : (
                      contact.full_name || '—'
                    )}
                  </div>
                  {contact.company && (
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      🏢 {contact.company}
                      {contact.position && ` • ${contact.position}`}
                    </div>
                  )}
                  {contact.email && (
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      ✉️ {contact.email}
                    </div>
                  )}
                  {contact.phone && (
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      📞 {contact.phone}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : query.trim() ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              🔍 {t.noResults}
            </div>
          ) : null}
        </div>

        {/* Footer with hints */}
        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          gap: '16px',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          background: 'var(--bg-secondary)'
        }}>
          <span>💡 {t.useArrows}</span>
          <span>↵ {t.pressEnter}</span>
          <span>Esc {t.pressEsc}</span>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideDown {
          from { 
            opacity: 0;
            transform: translateY(-20px);
          }
          to { 
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

