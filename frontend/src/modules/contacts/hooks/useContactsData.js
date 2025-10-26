import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';

/**
 * Custom hook for managing contacts data
 * 
 * Handles:
 * - Loading contacts with pagination
 * - Search, filter, sort
 * - Statistics calculation
 * - Data refresh
 * 
 * @param {object} options - Hook options
 * @param {string} options.lang - Language (ru/en)
 * @param {number} options.limit - Items per page
 * @returns {object} Contacts data and methods
 */
export const useContactsData = ({ lang = 'ru', limit = 20 } = {}) => {
  // Data state
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, withEmail: 0, withPhone: 0 });
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  
  // Filter & sort state
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState('desc');

  /**
   * Load contacts from API
   */
  const loadContacts = useCallback(async () => {
    setLoading(true);
    
    try {
      // Build query params
      const params = new URLSearchParams();
      
      if (search) params.append('search', search);
      if (companyFilter) params.append('company', companyFilter);
      if (positionFilter) params.append('position', positionFilter);
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      params.append('page', page.toString());
      params.append('limit', limit.toString());

      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        console.error('Failed to load contacts:', response.status);
        toast.error(lang === 'ru' ? 'Ошибка загрузки контактов' : 'Failed to load contacts');
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      
      // Update state with paginated data
      setContacts(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
      
      // Calculate statistics
      setStats({
        total: data.total || 0,
        withEmail: (data.items || []).filter(c => c.email).length,
        withPhone: (data.items || []).filter(c => c.phone).length
      });
    } catch (error) {
      console.error('Error loading contacts:', error);
      toast.error(lang === 'ru' ? 'Ошибка загрузки' : 'Loading error');
    } finally {
      setLoading(false);
    }
  }, [search, companyFilter, positionFilter, sortBy, sortOrder, page, limit, lang]);

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setSearch('');
    setCompanyFilter('');
    setPositionFilter('');
    setSortBy('id');
    setSortOrder('desc');
  }, []);

  /**
   * Refresh data (keep current filters)
   */
  const refreshContacts = useCallback(() => {
    loadContacts();
  }, [loadContacts]);

  // Load contacts when dependencies change
  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  // Reset to page 1 when filters change
  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
  }, [search, companyFilter, positionFilter, sortBy, sortOrder]);

  // Listen for global refresh events
  useEffect(() => {
    const handleRefresh = () => loadContacts();
    window.addEventListener('refresh-contacts', handleRefresh);
    return () => window.removeEventListener('refresh-contacts', handleRefresh);
  }, [loadContacts]);

  return {
    // Data
    contacts,
    loading,
    stats,
    
    // Pagination
    page,
    setPage,
    total,
    pages,
    limit,
    
    // Filters & Sort
    search,
    setSearch,
    companyFilter,
    setCompanyFilter,
    positionFilter,
    setPositionFilter,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    
    // Methods
    loadContacts,
    clearFilters,
    refreshContacts
  };
};

export default useContactsData;

