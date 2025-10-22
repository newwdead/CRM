/**
 * Tests for Preload Components Utilities
 */

import {
  preloadComponent,
  preloadComponents,
  preloadOnHover,
  preloadOnIdle,
  preloadAfterDelay,
} from '../../utils/preloadComponents';

// Mock lazy component
const createMockLazyComponent = (resolved = true) => {
  const mockComponent = () => <div>Mock Component</div>;
  
  if (resolved) {
    return {
      _payload: {
        _result: mockComponent,
      },
      _init: jest.fn(() => mockComponent),
    };
  }
  
  return {
    _payload: {},
    _init: jest.fn(() => Promise.resolve(mockComponent)),
  };
};

describe('preloadComponent', () => {
  test('returns cached component if already loaded', () => {
    const mockLazy = createMockLazyComponent(true);
    
    const result = preloadComponent(mockLazy);
    
    expect(result).toBeDefined();
    expect(mockLazy._init).not.toHaveBeenCalled();
  });

  test('calls _init if component not yet loaded', () => {
    const mockLazy = createMockLazyComponent(false);
    
    preloadComponent(mockLazy);
    
    expect(mockLazy._init).toHaveBeenCalledWith(mockLazy._payload);
  });
});

describe('preloadComponents', () => {
  test('preloads multiple components', async () => {
    const lazy1 = createMockLazyComponent(true);
    const lazy2 = createMockLazyComponent(true);
    const lazy3 = createMockLazyComponent(true);
    
    const result = await preloadComponents([lazy1, lazy2, lazy3]);
    
    expect(result).toHaveLength(3);
  });

  test('returns empty array for empty input', async () => {
    const result = await preloadComponents([]);
    
    expect(result).toEqual([]);
  });
});

describe('preloadOnHover', () => {
  test('returns a function', () => {
    const mockLazy = createMockLazyComponent(true);
    
    const hoverHandler = preloadOnHover(mockLazy);
    
    expect(typeof hoverHandler).toBe('function');
  });

  test('preloads component when returned function is called', () => {
    const mockLazy = createMockLazyComponent(false);
    
    const hoverHandler = preloadOnHover(mockLazy);
    hoverHandler();
    
    expect(mockLazy._init).toHaveBeenCalled();
  });
});

describe('preloadOnIdle', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('uses requestIdleCallback if available', () => {
    const mockIdleCallback = jest.fn((cb) => cb());
    global.requestIdleCallback = mockIdleCallback;
    
    const mockLazy = createMockLazyComponent(false);
    
    preloadOnIdle(mockLazy);
    
    expect(mockIdleCallback).toHaveBeenCalled();
    
    delete global.requestIdleCallback;
  });

  test('falls back to setTimeout if requestIdleCallback unavailable', () => {
    const originalRIC = global.requestIdleCallback;
    delete global.requestIdleCallback;
    
    const mockLazy = createMockLazyComponent(false);
    
    preloadOnIdle(mockLazy);
    
    jest.runAllTimers();
    
    expect(mockLazy._init).toHaveBeenCalled();
    
    if (originalRIC) {
      global.requestIdleCallback = originalRIC;
    }
  });
});

describe('preloadAfterDelay', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('preloads component after default delay (1000ms)', () => {
    const mockLazy = createMockLazyComponent(false);
    
    preloadAfterDelay(mockLazy);
    
    expect(mockLazy._init).not.toHaveBeenCalled();
    
    jest.advanceTimersByTime(1000);
    
    expect(mockLazy._init).toHaveBeenCalled();
  });

  test('preloads component after custom delay', () => {
    const mockLazy = createMockLazyComponent(false);
    
    preloadAfterDelay(mockLazy, 2000);
    
    expect(mockLazy._init).not.toHaveBeenCalled();
    
    jest.advanceTimersByTime(1999);
    expect(mockLazy._init).not.toHaveBeenCalled();
    
    jest.advanceTimersByTime(1);
    expect(mockLazy._init).toHaveBeenCalled();
  });

  test('does not preload before delay expires', () => {
    const mockLazy = createMockLazyComponent(false);
    
    preloadAfterDelay(mockLazy, 5000);
    
    jest.advanceTimersByTime(4999);
    
    expect(mockLazy._init).not.toHaveBeenCalled();
  });
});

