/**
 * Device Detection Utilities
 * Helper functions to detect mobile devices and capabilities
 */

/**
 * Check if current device is mobile
 */
export const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
};

/**
 * Check if device has touch support
 */
export const isTouchDevice = () => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    navigator.msMaxTouchPoints > 0
  );
};

/**
 * Check if device has camera
 */
export const hasCamera = () => {
  return !!(
    navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia
  );
};

/**
 * Get device type
 */
export const getDeviceType = () => {
  const ua = navigator.userAgent;
  
  if (/tablet|ipad|playbook|silk/i.test(ua)) {
    return 'tablet';
  }
  
  if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/i.test(ua)) {
    return 'mobile';
  }
  
  return 'desktop';
};

/**
 * Check if device is iOS
 */
export const isIOS = () => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

/**
 * Check if device is Android
 */
export const isAndroid = () => {
  return /Android/.test(navigator.userAgent);
};

/**
 * Get screen size category
 */
export const getScreenSize = () => {
  const width = window.innerWidth;
  
  if (width < 640) return 'small'; // Mobile portrait
  if (width < 768) return 'medium'; // Mobile landscape / Small tablet
  if (width < 1024) return 'large'; // Tablet
  return 'xlarge'; // Desktop
};

/**
 * Check if running as PWA (installed app)
 */
export const isPWA = () => {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
};

/**
 * Check if device supports vibration
 */
export const hasVibration = () => {
  return 'vibrate' in navigator;
};

/**
 * Vibrate device (if supported)
 */
export const vibrate = (pattern = 10) => {
  if (hasVibration()) {
    navigator.vibrate(pattern);
  }
};

/**
 * Get device orientation
 */
export const getOrientation = () => {
  if (window.innerHeight > window.innerWidth) {
    return 'portrait';
  }
  return 'landscape';
};

export default {
  isMobileDevice,
  isTouchDevice,
  hasCamera,
  getDeviceType,
  isIOS,
  isAndroid,
  getScreenSize,
  isPWA,
  hasVibration,
  vibrate,
  getOrientation
};
