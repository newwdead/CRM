/**
 * OCR Module - Export
 * Главная точка входа для модуля OCR
 * 
 * Refactored: October 26, 2025
 * Modular architecture with hooks, utils, and components
 */

// Main Container Component
export { default as OCREditorContainer } from './components/OCREditorContainer';

// Custom Hooks
export { useOCRBlocks } from './hooks/useOCRBlocks';
export { useBlockSelection } from './hooks/useBlockSelection';
export { useImageControls } from './hooks/useImageControls';
export { useFieldAssignment } from './hooks/useFieldAssignment';
export { useBlockManipulation } from './hooks/useBlockManipulation';

// UI Components (for advanced usage)
export { default as OCRToolbar } from './components/OCRToolbar';
export { default as ImageCanvas } from './components/ImageCanvas';
export { default as FieldsSidebar } from './components/FieldsSidebar';
export { default as BlockTextEditor } from './components/BlockTextEditor';
export { default as AssignmentPanel } from './components/AssignmentPanel';
export { default as BlockOverlay } from './components/BlockOverlay';

// Constants & Utils
export { getOCRTranslations } from './constants/translations';
export { editableFields, fieldColors } from './constants/fieldConfig';
export * from './utils/blockUtils';
export * from './utils/imageUtils';

