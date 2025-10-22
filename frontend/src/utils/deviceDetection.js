/**
 * Device Detection Utilities
 * Detect mobile devices, screen sizes, and capabilities
 */

/**
 * Check if current device is mobile
 * @returns {boolean} True if mobile device
 */
export const isMobile = () => {
  // Check by user agent
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i;
  
  // Check by screen width
  const isSmallScreen = window.innerWidth <= 768;
  
  // Check by touch support
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  return mobileRegex.test(userAgent.toLowerCase()) || (isSmallScreen && isTouchDevice);
};

/**
 * Check if device is tablet
 * @returns {boolean} True if tablet
 */
export const isTablet = () => {
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  const tabletRegex = /ipad|tablet|playbook|silk/i;
  const width = window.innerWidth;
  
  return tabletRegex.test(userAgent.toLowerCase()) || (width > 768 && width <= 1024);
};

/**
 * Get device type
 * @returns {string} 'mobile' | 'tablet' | 'desktop'
 */
export const getDeviceType = () => {
  if (isMobile()) return 'mobile';
  if (isTablet()) return 'tablet';
  return 'desktop';
};

/**
 * Check if device has touch support
 * @returns {boolean} True if device supports touch
 */
export const isTouchDevice = () => {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

/**
 * Get screen orientation
 * @returns {string} 'portrait' | 'landscape'
 */
export const getOrientation = () => {
  return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
};

/**
 * Check if running as PWA (installed app)
 * @returns {boolean} True if PWA
 */
export const isPWA = () => {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
};

/**
 * Get safe area insets (for notched devices)
 * @returns {object} Top, bottom, left, right insets
 */
export const getSafeAreaInsets = () => {
  const computedStyle = getComputedStyle(document.documentElement);
  return {
    top: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-top)') || '0'),
    bottom: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-bottom)') || '0'),
    left: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-left)') || '0'),
    right: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-right)') || '0')
  };
};

/**
 * Check if device supports camera
 * @returns {Promise<boolean>} True if camera available
 */
export const hasCameraAccess = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.some(device => device.kind === 'videoinput');
  } catch (error) {
    return false;
  }
};

/**
 * Request camera permission
 * @returns {Promise<boolean>} True if permission granted
 */
export const requestCameraPermission = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    // Stop stream immediately, we just wanted to check permission
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Check if online
 * @returns {boolean} True if online
 */
export const isOnline = () => {
  return navigator.onLine;
};

/**
 * Get network type (if available)
 * @returns {string|null} Network type or null
 */
export const getNetworkType = () => {
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  return connection ? connection.effectiveType : null;
};

/**
 * Check if slow network
 * @returns {boolean} True if slow network (2G or slow 3G)
 */
export const isSlowNetwork = () => {
  const networkType = getNetworkType();
  return networkType === 'slow-2g' || networkType === '2g';
};

/**
 * Add responsive class to body based on device
 */
export const addResponsiveClass = () => {
  const deviceType = getDeviceType();
  const orientation = getOrientation();
  
  document.body.classList.remove('mobile', 'tablet', 'desktop', 'portrait', 'landscape');
  document.body.classList.add(deviceType, orientation);
  
  if (isPWA()) {
    document.body.classList.add('pwa');
  }
};

/**
 * Listen for orientation changes
 * @param {Function} callback Callback function
 * @returns {Function} Cleanup function
 */
export const onOrientationChange = (callback) => {
  const handleChange = () => {
    callback(getOrientation());
  };
  
  window.addEventListener('orientationchange', handleChange);
  window.addEventListener('resize', handleChange);
  
  return () => {
    window.removeEventListener('orientationchange', handleChange);
    window.removeEventListener('resize', handleChange);
  };
};

/**
 * Detect and initialize responsive behavior
 */
export const initResponsive = () => {
  // Add initial classes
  addResponsiveClass();
  
  // Update on resize
  window.addEventListener('resize', addResponsiveClass);
  
  // Update on orientation change
  window.addEventListener('orientationchange', addResponsiveClass);
  
  // Cleanup function
  return () => {
    window.removeEventListener('resize', addResponsiveClass);
    window.removeEventListener('orientationchange', addResponsiveClass);
  };
};

