/**
 * Production-Safe Logger Utility
 * 
 * Only logs in development environment
 * Provides structured logging with levels
 */

const isDevelopment = process.env.NODE_ENV === 'development';

const logger = {
  /**
   * Development-only console.log
   */
  log: (...args) => {
    if (isDevelopment) {
      console.log('[LOG]', ...args);
    }
  },

  /**
   * Development-only console.error
   */
  error: (...args) => {
    if (isDevelopment) {
      console.error('[ERROR]', ...args);
    } else {
      // In production, still log errors but minimal
      console.error('An error occurred. Check browser console in dev mode.');
    }
  },

  /**
   * Development-only console.warn
   */
  warn: (...args) => {
    if (isDevelopment) {
      console.warn('[WARN]', ...args);
    }
  },

  /**
   * Development-only console.info
   */
  info: (...args) => {
    if (isDevelopment) {
      console.info('[INFO]', ...args);
    }
  },

  /**
   * Development-only console.debug
   */
  debug: (...args) => {
    if (isDevelopment) {
      console.debug('[DEBUG]', ...args);
    }
  },

  /**
   * Always log (critical information)
   */
  always: (...args) => {
    console.log(...args);
  }
};

export default logger;

