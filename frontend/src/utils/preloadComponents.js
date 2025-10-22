/**
 * Component Preloading Utilities
 * Preload critical components for better UX
 */

/**
 * Preload a lazy-loaded component
 * @param {Function} lazyComponent - React.lazy() component
 * @returns {Promise}
 */
export const preloadComponent = (lazyComponent) => {
  return lazyComponent._payload._result || lazyComponent._init(lazyComponent._payload);
};

/**
 * Preload multiple components
 * @param {Array<Function>} components - Array of React.lazy() components
 * @returns {Promise<Array>}
 */
export const preloadComponents = (components) => {
  return Promise.all(components.map(preloadComponent));
};

/**
 * Preload component on mouse hover
 * Usage: <Link onMouseEnter={() => preloadOnHover(Component)}>
 */
export const preloadOnHover = (lazyComponent) => {
  return () => preloadComponent(lazyComponent);
};

/**
 * Preload component on idle
 * Uses requestIdleCallback to preload when browser is idle
 */
export const preloadOnIdle = (lazyComponent) => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => preloadComponent(lazyComponent));
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => preloadComponent(lazyComponent), 1);
  }
};

/**
 * Preload component after a delay
 * @param {Function} lazyComponent - React.lazy() component
 * @param {number} delay - Delay in milliseconds (default: 1000)
 */
export const preloadAfterDelay = (lazyComponent, delay = 1000) => {
  setTimeout(() => preloadComponent(lazyComponent), delay);
};

export default {
  preloadComponent,
  preloadComponents,
  preloadOnHover,
  preloadOnIdle,
  preloadAfterDelay,
};

