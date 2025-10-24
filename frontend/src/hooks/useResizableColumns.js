import { useCallback, useRef, useState } from 'react';

/**
 * Custom Hook for Resizable Table Columns
 * v5.0.2: Enables drag-to-resize functionality
 * 
 * Usage:
 * const { handleMouseDown, isResizing } = useResizableColumns(columns, setColumns);
 * 
 * @param {Array} columns - Array of column configurations with width
 * @param {Function} setColumns - State setter for columns
 * @returns {Object} - { handleMouseDown, isResizing }
 */
export function useResizableColumns(columns, setColumns) {
  const [isResizing, setIsResizing] = useState(false);
  const resizingColumn = useRef(null);
  const startX = useRef(0);
  const startWidth = useRef(0);

  // Start resizing
  const handleMouseDown = useCallback((e, columnKey) => {
    e.preventDefault();
    e.stopPropagation();
    
    const th = e.target.closest('th');
    if (!th) return;
    
    resizingColumn.current = columnKey;
    startX.current = e.clientX;
    startWidth.current = parseInt(th.style.width || th.offsetWidth);
    setIsResizing(true);
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  // Handle mouse move while resizing
  const handleMouseMove = useCallback((e) => {
    if (!resizingColumn.current) return;
    
    const diff = e.clientX - startX.current;
    const newWidth = Math.max(40, Math.min(800, startWidth.current + diff));
    
    // Update column width immediately for smooth resizing
    const th = document.querySelector(`th[data-column-key="${resizingColumn.current}"]`);
    if (th) {
      th.style.width = `${newWidth}px`;
    }
  }, []);

  // End resizing
  const handleMouseUp = useCallback(() => {
    if (!resizingColumn.current) return;
    
    // Get final width
    const th = document.querySelector(`th[data-column-key="${resizingColumn.current}"]`);
    if (th) {
      const finalWidth = parseInt(th.style.width);
      
      // Update columns state
      setColumns(prev => 
        prev.map(col => 
          col.key === resizingColumn.current 
            ? { ...col, width: finalWidth.toString() }
            : col
        )
      );
      
      // Save to localStorage
      const updatedColumns = columns.map(col => 
        col.key === resizingColumn.current 
          ? { ...col, width: finalWidth.toString() }
          : col
      );
      localStorage.setItem('table_columns', JSON.stringify(updatedColumns));
    }
    
    resizingColumn.current = null;
    setIsResizing(false);
    
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  }, [columns, setColumns]);

  return {
    handleMouseDown,
    isResizing
  };
}

export default useResizableColumns;
