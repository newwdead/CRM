/**
 * Field configuration for OCR Editor
 * Defines editable fields and their visual properties
 */

/**
 * List of editable contact fields
 */
export const editableFields = [
  'first_name',
  'last_name',
  'middle_name',
  'company',
  'position',
  'email',
  'phone',
  'phone_mobile',
  'phone_work',
  'phone_additional',
  'address',
  'address_additional',
  'website',
  'comment'
];

/**
 * Field colors for visual distinction in block overlay
 * Each field gets a unique color for better UX
 */
export const fieldColors = {
  first_name: '#3b82f6',        // Blue
  last_name: '#8b5cf6',         // Purple
  middle_name: '#a855f7',       // Light Purple
  company: '#10b981',           // Green
  position: '#14b8a6',          // Teal
  email: '#f59e0b',             // Orange
  phone: '#ef4444',             // Red
  phone_mobile: '#ec4899',      // Pink
  phone_work: '#f97316',        // Dark Orange
  phone_additional: '#84cc16',  // Lime
  address: '#06b6d4',           // Cyan
  address_additional: '#0ea5e9', // Sky Blue
  website: '#6366f1',           // Indigo
  comment: '#64748b'            // Slate
};

/**
 * Field groups for better organization
 */
export const fieldGroups = {
  name: ['first_name', 'last_name', 'middle_name'],
  company: ['company', 'position'],
  contact: ['email', 'phone', 'phone_mobile', 'phone_work', 'phone_additional'],
  address: ['address', 'address_additional'],
  other: ['website', 'comment']
};

/**
 * Get field color by field name
 * @param {string} fieldName - Field name
 * @returns {string} Hex color code
 */
export const getFieldColor = (fieldName) => {
  return fieldColors[fieldName] || '#64748b'; // Default: slate
};

/**
 * Get all fields in a specific group
 * @param {string} groupName - Group name
 * @returns {array} Array of field names
 */
export const getFieldGroup = (groupName) => {
  return fieldGroups[groupName] || [];
};

/**
 * Check if field is editable
 * @param {string} fieldName - Field name
 * @returns {boolean} True if field is editable
 */
export const isFieldEditable = (fieldName) => {
  return editableFields.includes(fieldName);
};

