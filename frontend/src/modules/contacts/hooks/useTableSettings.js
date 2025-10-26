import { useState, useCallback, useEffect } from 'react';

/**
 * Default table columns configuration
 * @param {string} lang - Language (ru/en)
 * @returns {array} Default columns
 */
const getDefaultColumns = (lang) => [
  { key: 'select', label: '☑️', visible: true, order: 0, width: '40' },
  { key: 'number', label: '№', visible: true, order: 1, width: '50' },
  { key: 'date', label: lang === 'ru' ? 'Дата' : 'Date', visible: true, order: 2, width: '100' },
  { key: 'uid', label: 'UID', visible: false, order: 3, width: '80' },
  { key: 'name', label: lang === 'ru' ? 'Имя' : 'Name', visible: true, order: 4, width: '150' },
  { key: 'company', label: lang === 'ru' ? 'Компания' : 'Company', visible: true, order: 5, width: '140' },
  { key: 'position', label: lang === 'ru' ? 'Должность' : 'Position', visible: true, order: 6, width: '120' },
  { key: 'email', label: 'Email', visible: true, order: 7, width: '180' },
  { key: 'phone', label: lang === 'ru' ? 'Телефон' : 'Phone', visible: true, order: 8, width: '130' },
  { key: 'address', label: lang === 'ru' ? 'Адрес' : 'Address', visible: false, order: 9, width: '150' },
  { key: 'website', label: lang === 'ru' ? 'Сайт' : 'Website', visible: false, order: 10, width: '60' },
  { key: 'comment', label: lang === 'ru' ? 'Комментарий' : 'Comment', visible: false, order: 11, width: '120' },
  { key: 'photo', label: lang === 'ru' ? 'Фото' : 'Photo', visible: true, order: 12, width: '60' },
  { key: 'actions', label: lang === 'ru' ? 'Действия' : 'Actions', visible: true, order: 13, width: '100' },
];

/**
 * Custom hook for managing table settings
 * 
 * Handles:
 * - Column configuration (visibility, order, width)
 * - Table zoom (0.5x - 2.0x)
 * - Save/load from localStorage
 * 
 * @param {object} options - Hook options
 * @param {string} options.lang - Language (ru/en)
 * @returns {object} Table settings and methods
 */
export const useTableSettings = ({ lang = 'ru' } = {}) => {
  // Load columns from localStorage or use defaults
  const [tableColumns, setTableColumns] = useState(() => {
    const saved = localStorage.getItem('table_columns');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse table columns:', e);
      }
    }
    return getDefaultColumns(lang);
  });

  // Load zoom from localStorage or use default
  const [tableZoom, setTableZoom] = useState(() => {
    const saved = localStorage.getItem('table_zoom');
    return saved ? parseFloat(saved) : 1.0;
  });

  /**
   * Update table columns
   * @param {array} columns - New columns configuration
   */
  const updateColumns = useCallback((columns) => {
    setTableColumns(columns);
    localStorage.setItem('table_columns', JSON.stringify(columns));
  }, []);

  /**
   * Reset columns to default
   */
  const resetColumns = useCallback(() => {
    const defaults = getDefaultColumns(lang);
    setTableColumns(defaults);
    localStorage.setItem('table_columns', JSON.stringify(defaults));
  }, [lang]);

  /**
   * Toggle column visibility
   * @param {string} columnKey - Column key to toggle
   */
  const toggleColumnVisibility = useCallback((columnKey) => {
    setTableColumns(prevColumns => {
      const newColumns = prevColumns.map(col =>
        col.key === columnKey ? { ...col, visible: !col.visible } : col
      );
      localStorage.setItem('table_columns', JSON.stringify(newColumns));
      return newColumns;
    });
  }, []);

  /**
   * Update column width
   * @param {string} columnKey - Column key
   * @param {string} width - New width
   */
  const updateColumnWidth = useCallback((columnKey, width) => {
    setTableColumns(prevColumns => {
      const newColumns = prevColumns.map(col =>
        col.key === columnKey ? { ...col, width } : col
      );
      localStorage.setItem('table_columns', JSON.stringify(newColumns));
      return newColumns;
    });
  }, []);

  /**
   * Reorder columns
   * @param {array} newOrder - New column order (array of column keys)
   */
  const reorderColumns = useCallback((newOrder) => {
    setTableColumns(prevColumns => {
      const newColumns = newOrder.map((key, index) => {
        const col = prevColumns.find(c => c.key === key);
        return { ...col, order: index };
      });
      localStorage.setItem('table_columns', JSON.stringify(newColumns));
      return newColumns;
    });
  }, []);

  /**
   * Zoom in
   */
  const zoomIn = useCallback(() => {
    const newZoom = Math.min(tableZoom + 0.1, 2.0);
    setTableZoom(newZoom);
    localStorage.setItem('table_zoom', newZoom.toString());
  }, [tableZoom]);

  /**
   * Zoom out
   */
  const zoomOut = useCallback(() => {
    const newZoom = Math.max(tableZoom - 0.1, 0.5);
    setTableZoom(newZoom);
    localStorage.setItem('table_zoom', newZoom.toString());
  }, [tableZoom]);

  /**
   * Reset zoom to 100%
   */
  const zoomReset = useCallback(() => {
    setTableZoom(1.0);
    localStorage.setItem('table_zoom', '1.0');
  }, []);

  /**
   * Set specific zoom level
   * @param {number} zoom - Zoom level (0.5 - 2.0)
   */
  const setZoom = useCallback((zoom) => {
    const clampedZoom = Math.max(0.5, Math.min(2.0, zoom));
    setTableZoom(clampedZoom);
    localStorage.setItem('table_zoom', clampedZoom.toString());
  }, []);

  /**
   * Get visible columns in order
   * @returns {array} Visible columns sorted by order
   */
  const visibleColumns = tableColumns
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order);

  return {
    // State
    tableColumns,
    tableZoom,
    visibleColumns,
    
    // Column methods
    updateColumns,
    resetColumns,
    toggleColumnVisibility,
    updateColumnWidth,
    reorderColumns,
    
    // Zoom methods
    zoomIn,
    zoomOut,
    zoomReset,
    setZoom
  };
};

export default useTableSettings;

