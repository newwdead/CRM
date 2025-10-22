import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * Bottom Navigation for Mobile
 * Fixed bottom navigation bar with main app actions
 * 
 * Features:
 * - Always visible on mobile
 * - Thumb-friendly zones
 * - Active state indication
 * - Smooth animations
 */
function BottomNavigation({ lang = 'ru' }) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const navItems = [
    { path: '/', icon: '🏠', label: lang === 'ru' ? 'Главная' : 'Home' },
    { path: '/contacts', icon: '📇', label: lang === 'ru' ? 'Контакты' : 'Contacts' },
    { path: '/upload', icon: '📤', label: lang === 'ru' ? 'Загрузить' : 'Upload' },
    { path: '/settings', icon: '⚙️', label: lang === 'ru' ? 'Настройки' : 'Settings' }
  ];

  // Don't show on desktop
  const isMobile = window.innerWidth <= 768;
  if (!isMobile) return null;

  return (
    <motion.nav
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '64px',
        background: 'white',
        borderTop: '1px solid #e0e0e0',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 1000,
        boxShadow: '0 -2px 10px rgba(0,0,0,0.1)',
        paddingBottom: 'env(safe-area-inset-bottom)' // Safe area for notched phones
      }}
    >
      {navItems.map((item) => {
        const active = isActive(item.path);
        return (
          <motion.button
            key={item.path}
            onClick={() => navigate(item.path)}
            whileTap={{ scale: 0.9 }}
            style={{
              flex: 1,
              height: '100%',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              color: active ? '#2563eb' : '#666',
              fontSize: '24px',
              transition: 'color 0.2s',
              padding: '8px',
              position: 'relative'
            }}
          >
            <motion.span
              animate={{ scale: active ? 1.2 : 1 }}
              transition={{ type: 'spring', stiffness: 300 }}
            >
              {item.icon}
            </motion.span>
            <span style={{
              fontSize: '11px',
              fontWeight: active ? '600' : 'normal'
            }}>
              {item.label}
            </span>

            {/* Active Indicator */}
            {active && (
              <motion.div
                layoutId="activeIndicator"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '40px',
                  height: '3px',
                  background: '#2563eb',
                  borderRadius: '0 0 3px 3px'
                }}
              />
            )}
          </motion.button>
        );
      })}
    </motion.nav>
  );
}

export default BottomNavigation;

