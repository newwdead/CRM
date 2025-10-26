/**
 * Contact List Table Configuration
 * Column definitions and sort options
 */

/**
 * Available sort fields
 */
export const sortFields = [
  { value: 'id', labelRu: 'ID', labelEn: 'ID' },
  { value: 'full_name', labelRu: 'Имя', labelEn: 'Name' },
  { value: 'company', labelRu: 'Компания', labelEn: 'Company' },
  { value: 'position', labelRu: 'Должность', labelEn: 'Position' },
  { value: 'email', labelRu: 'Email', labelEn: 'Email' },
  { value: 'phone', labelRu: 'Телефон', labelEn: 'Phone' },
  { value: 'created_at', labelRu: 'Дата создания', labelEn: 'Created date' },
];

/**
 * Sort order options
 */
export const sortOrders = [
  { value: 'asc', labelRu: 'По возрастанию', labelEn: 'Ascending' },
  { value: 'desc', labelRu: 'По убыванию', labelEn: 'Descending' },
];

/**
 * Editable contact fields
 */
export const editableFields = [
  'full_name',
  'company',
  'position',
  'email',
  'phone',
  'address',
  'website',
  'comment'
];

/**
 * Get default columns configuration
 * @param {string} lang - Language ('ru' or 'en')
 * @returns {array} Default columns
 */
export const getDefaultColumns = (lang = 'ru') => [
  { key: 'select', label: '☑️', visible: true, order: 0, width: '40', sortable: false },
  { key: 'number', label: '№', visible: true, order: 1, width: '50', sortable: false },
  { key: 'date', label: lang === 'ru' ? 'Дата' : 'Date', visible: true, order: 2, width: '100', sortable: true, sortKey: 'created_at' },
  { key: 'uid', label: 'UID', visible: false, order: 3, width: '80', sortable: false },
  { key: 'name', label: lang === 'ru' ? 'Имя' : 'Name', visible: true, order: 4, width: '150', sortable: true, sortKey: 'full_name' },
  { key: 'company', label: lang === 'ru' ? 'Компания' : 'Company', visible: true, order: 5, width: '140', sortable: true, sortKey: 'company' },
  { key: 'position', label: lang === 'ru' ? 'Должность' : 'Position', visible: true, order: 6, width: '120', sortable: true, sortKey: 'position' },
  { key: 'email', label: 'Email', visible: true, order: 7, width: '180', sortable: true, sortKey: 'email' },
  { key: 'phone', label: lang === 'ru' ? 'Телефон' : 'Phone', visible: true, order: 8, width: '130', sortable: true, sortKey: 'phone' },
  { key: 'address', label: lang === 'ru' ? 'Адрес' : 'Address', visible: false, order: 9, width: '150', sortable: false },
  { key: 'website', label: lang === 'ru' ? 'Сайт' : 'Website', visible: false, order: 10, width: '60', sortable: false },
  { key: 'comment', label: lang === 'ru' ? 'Комментарий' : 'Comment', visible: false, order: 11, width: '120', sortable: false },
  { key: 'photo', label: lang === 'ru' ? 'Фото' : 'Photo', visible: true, order: 12, width: '60', sortable: false },
  { key: 'actions', label: lang === 'ru' ? 'Действия' : 'Actions', visible: true, order: 13, width: '100', sortable: false },
];

/**
 * Column keys that should be centered
 */
export const centeredColumns = ['select', 'number', 'photo', 'actions'];

/**
 * Column keys that display dates
 */
export const dateColumns = ['date', 'created_at', 'updated_at'];

/**
 * Get column by key
 * @param {array} columns - Columns array
 * @param {string} key - Column key
 * @returns {object|null} Column object or null
 */
export const getColumnByKey = (columns, key) => {
  return columns.find(col => col.key === key) || null;
};

/**
 * Check if column is visible
 * @param {array} columns - Columns array
 * @param {string} key - Column key
 * @returns {boolean} Whether column is visible
 */
export const isColumnVisible = (columns, key) => {
  const column = getColumnByKey(columns, key);
  return column ? column.visible : false;
};

/**
 * Get visible columns sorted by order
 * @param {array} columns - Columns array
 * @returns {array} Visible columns
 */
export const getVisibleColumns = (columns) => {
  return columns
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order);
};

/**
 * Get sortable columns
 * @param {array} columns - Columns array
 * @returns {array} Sortable columns
 */
export const getSortableColumns = (columns) => {
  return columns.filter(col => col.sortable);
};

export default {
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
};

