/**
 * Contacts Module - Export
 * Main entry point for contacts module
 * 
 * Refactored: October 26, 2025
 * Modular architecture with hooks, constants, and components
 */

// Custom Hooks
export { useContactsData } from './hooks/useContactsData';
export { useContactSelection } from './hooks/useContactSelection';
export { useTableSettings } from './hooks/useTableSettings';
export { useBulkOperations } from './hooks/useBulkOperations';
export { useContactModals } from './hooks/useContactModals';

// Constants
export { 
  contactListTranslations, 
  getContactListTranslations 
} from './constants/translations';

export { 
  sortFields,
  sortOrders,
  editableFields,
  getDefaultColumns,
  centeredColumns,
  dateColumns,
  getColumnByKey,
  isColumnVisible,
  getVisibleColumns,
  getSortableColumns
} from './constants/tableConfig';

// Components (will be added in Phase 3)
// export { ContactListContainer } from './components/ContactListContainer';
// export { ContactsToolbar } from './components/ContactsToolbar';
// export { ContactsFilters } from './components/ContactsFilters';
// export { ContactsTable } from './components/ContactsTable';
// export { ContactsPagination } from './components/ContactsPagination';
// export { BulkEditPanel } from './components/BulkEditPanel';
// export { TableSettingsModal } from './components/TableSettingsModal';
