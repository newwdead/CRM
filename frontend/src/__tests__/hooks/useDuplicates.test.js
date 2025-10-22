/**
 * Tests for useDuplicates Hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useDuplicates } from '../../modules/duplicates';
import * as duplicatesApi from '../../modules/duplicates/api/duplicatesApi';

// Mock the API
jest.mock('../../modules/duplicates/api/duplicatesApi');

// Mock toast
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

describe('useDuplicates', () => {
  const mockDuplicates = [
    {
      id: 1,
      contact_id_1: 1,
      contact_id_2: 2,
      similarity: 0.9,
      match_type: 'name',
      resolved: false,
    },
    {
      id: 2,
      contact_id_1: 1,
      contact_id_2: 3,
      similarity: 0.85,
      match_type: 'email',
      resolved: false,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    duplicatesApi.fetchDuplicates.mockResolvedValue(mockDuplicates);
  });

  test('loads duplicates on mount', async () => {
    const { result } = renderHook(() => useDuplicates('ru'));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.duplicates).toEqual(mockDuplicates);
    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledWith('ru');
  });

  test('handles loading state correctly', async () => {
    const { result } = renderHook(() => useDuplicates('en'));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  test('handles errors when loading duplicates', async () => {
    const errorMessage = 'Failed to load';
    duplicatesApi.fetchDuplicates.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeDefined();
  });

  test('merges duplicates successfully', async () => {
    duplicatesApi.mergeDuplicates.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleMerge(1, [2]);
    });

    expect(duplicatesApi.mergeDuplicates).toHaveBeenCalledWith(1, [2], 'ru');
    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(2); // Initial + after merge
  });

  test('handles merge errors', async () => {
    duplicatesApi.mergeDuplicates.mockRejectedValue(new Error('Merge failed'));

    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleMerge(1, [2]);
    });

    expect(duplicatesApi.mergeDuplicates).toHaveBeenCalledWith(1, [2], 'ru');
    // Should not reload after error
    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(1); // Only initial
  });

  test('marks duplicate as reviewed', async () => {
    duplicatesApi.markAsReviewed.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleMarkAsReviewed(1);
    });

    expect(duplicatesApi.markAsReviewed).toHaveBeenCalledWith(1, 'ru');
    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(2);
  });

  test('dismisses duplicate', async () => {
    duplicatesApi.dismissDuplicate.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleDismiss(1);
    });

    expect(duplicatesApi.dismissDuplicate).toHaveBeenCalledWith(1, 'ru');
    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(2);
  });

  test('can reload duplicates manually', async () => {
    const { result } = renderHook(() => useDuplicates('ru'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.loadDuplicates();
    });

    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledTimes(2);
  });

  test('uses English language correctly', async () => {
    const { result } = renderHook(() => useDuplicates('en'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(duplicatesApi.fetchDuplicates).toHaveBeenCalledWith('en');
  });
});

