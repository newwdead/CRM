/**
 * useDuplicates Hook
 * Manages duplicate contacts state and operations
 */
import { useState, useEffect, useCallback } from 'react';
import * as duplicatesApi from '../api/duplicatesApi';

export const useDuplicates = () => {
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [groupedDuplicates, setGroupedDuplicates] = useState({});

  /**
   * Load all duplicates
   */
  const loadDuplicates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await duplicatesApi.fetchDuplicates();
      setDuplicates(data);

      // Group duplicates by contact
      const grouped = {};
      data.forEach(dup => {
        const key1 = dup.contact_id_1;
        const key2 = dup.contact_id_2;

        if (!grouped[key1]) grouped[key1] = [];
        if (!grouped[key2]) grouped[key2] = [];

        grouped[key1].push(dup);
        grouped[key2].push(dup);
      });

      setGroupedDuplicates(grouped);
    } catch (err) {
      console.error('Failed to load duplicates:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Load duplicates for a specific contact
   */
  const loadContactDuplicates = useCallback(async (contactId) => {
    try {
      setLoading(true);
      setError(null);
      const data = await duplicatesApi.fetchContactDuplicates(contactId);
      return data;
    } catch (err) {
      console.error('Failed to load contact duplicates:', err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Merge duplicates
   */
  const mergeDuplicates = useCallback(async (primaryId, duplicateIds) => {
    try {
      setLoading(true);
      setError(null);
      const result = await duplicatesApi.mergeDuplicates(primaryId, duplicateIds);
      
      // Reload duplicates after merge
      await loadDuplicates();
      
      return result;
    } catch (err) {
      console.error('Failed to merge duplicates:', err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadDuplicates]);

  /**
   * Mark duplicate as reviewed
   */
  const markAsReviewed = useCallback(async (duplicateId) => {
    try {
      setError(null);
      await duplicatesApi.markAsReviewed(duplicateId);
      
      // Update local state
      setDuplicates(prev => prev.map(dup =>
        dup.id === duplicateId
          ? { ...dup, status: 'reviewed' }
          : dup
      ));
    } catch (err) {
      console.error('Failed to mark as reviewed:', err);
      setError(err.message);
      throw err;
    }
  }, []);

  /**
   * Dismiss duplicate
   */
  const dismissDuplicate = useCallback(async (duplicateId) => {
    try {
      setError(null);
      await duplicatesApi.dismissDuplicate(duplicateId);
      
      // Remove from local state
      setDuplicates(prev => prev.filter(dup => dup.id !== duplicateId));
      
      // Update grouped duplicates
      setGroupedDuplicates(prev => {
        const newGrouped = { ...prev };
        Object.keys(newGrouped).forEach(key => {
          newGrouped[key] = newGrouped[key].filter(dup => dup.id !== duplicateId);
          if (newGrouped[key].length === 0) {
            delete newGrouped[key];
          }
        });
        return newGrouped;
      });
    } catch (err) {
      console.error('Failed to dismiss duplicate:', err);
      setError(err.message);
      throw err;
    }
  }, []);

  /**
   * Get duplicate count for a contact
   */
  const getDuplicateCount = useCallback((contactId) => {
    return groupedDuplicates[contactId]?.length || 0;
  }, [groupedDuplicates]);

  /**
   * Check if contact has duplicates
   */
  const hasDuplicates = useCallback((contactId) => {
    return (groupedDuplicates[contactId]?.length || 0) > 0;
  }, [groupedDuplicates]);

  // Load on mount
  useEffect(() => {
    loadDuplicates();
  }, [loadDuplicates]);

  return {
    duplicates,
    groupedDuplicates,
    loading,
    error,
    loadDuplicates,
    loadContactDuplicates,
    mergeDuplicates,
    markAsReviewed,
    dismissDuplicate,
    getDuplicateCount,
    hasDuplicates
  };
};

export default useDuplicates;

