/**
 * Hook для фильтрации и сортировки контактов
 * Изолированная логика фильтров
 */

import { useState, useCallback } from 'react';

export const useContactFilters = (initialFilters = {}) => {
  const [search, setSearch] = useState(initialFilters.search || '');
  const [companyFilter, setCompanyFilter] = useState(initialFilters.company || '');
  const [positionFilter, setPositionFilter] = useState(initialFilters.position || '');
  const [sortBy, setSortBy] = useState(initialFilters.sort_by || 'id');
  const [sortOrder, setSortOrder] = useState(initialFilters.order || 'desc');
  const [page, setPage] = useState(initialFilters.page || 1);
  const [limit] = useState(initialFilters.limit || 20);

  // Получить параметры для API
  const getFilterParams = useCallback(() => {
    const params = {
      page,
      limit,
      sort_by: sortBy,
      order: sortOrder
    };

    if (search) params.search = search;
    if (companyFilter) params.company = companyFilter;
    if (positionFilter) params.position = positionFilter;

    return params;
  }, [search, companyFilter, positionFilter, sortBy, sortOrder, page, limit]);

  // Сбросить фильтры
  const resetFilters = useCallback(() => {
    setSearch('');
    setCompanyFilter('');
    setPositionFilter('');
    setSortBy('id');
    setSortOrder('desc');
    setPage(1);
  }, []);

  // Установить сортировку
  const handleSort = useCallback((field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setPage(1);
  }, [sortBy, sortOrder]);

  return {
    // Состояние
    search,
    companyFilter,
    positionFilter,
    sortBy,
    sortOrder,
    page,
    limit,
    
    // Методы установки
    setSearch,
    setCompanyFilter,
    setPositionFilter,
    setSortBy,
    setSortOrder,
    setPage,
    
    // Утилиты
    getFilterParams,
    resetFilters,
    handleSort
  };
};

