import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

/**
 * Pull to Refresh Component
 * Implements pull-down gesture to refresh content
 * 
 * Usage:
 * <PullToRefresh onRefresh={async () => { await loadData(); }}>
 *   <YourContent />
 * </PullToRefresh>
 */
function PullToRefresh({ children, onRefresh, threshold = 80, lang = 'ru' }) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [canPull, setCanPull] = useState(false);
  const startY = useRef(0);
  const containerRef = useRef(null);

  const t = {
    en: {
      pullToRefresh: 'Pull to refresh',
      releaseToRefresh: 'Release to refresh',
      refreshing: 'Refreshing...'
    },
    ru: {
      pullToRefresh: 'Потяните для обновления',
      releaseToRefresh: 'Отпустите для обновления',
      refreshing: 'Обновление...'
    }
  }[lang];

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check if at top of scrollable content
    const checkScrollPosition = () => {
      setCanPull(container.scrollTop === 0);
    };

    container.addEventListener('scroll', checkScrollPosition);
    checkScrollPosition();

    return () => {
      container.removeEventListener('scroll', checkScrollPosition);
    };
  }, []);

  const handleTouchStart = (e) => {
    if (canPull && !isRefreshing) {
      startY.current = e.touches[0].clientY;
    }
  };

  const handleTouchMove = (e) => {
    if (!canPull || isRefreshing || startY.current === 0) return;

    const currentY = e.touches[0].clientY;
    const distance = currentY - startY.current;

    if (distance > 0) {
      // Prevent default scroll while pulling
      e.preventDefault();
      // Apply damping effect
      const damping = 0.5;
      setPullDistance(Math.min(distance * damping, threshold * 1.5));
    }
  };

  const handleTouchEnd = async () => {
    if (pullDistance > threshold && !isRefreshing) {
      setIsRefreshing(true);
      setPullDistance(threshold);

      try {
        if (onRefresh) {
          await onRefresh();
        }
      } catch (error) {
        console.error('Refresh error:', error);
      } finally {
        setTimeout(() => {
          setIsRefreshing(false);
          setPullDistance(0);
          startY.current = 0;
        }, 500);
      }
    } else {
      setPullDistance(0);
      startY.current = 0;
    }
  };

  const getStatusText = () => {
    if (isRefreshing) return t.refreshing;
    if (pullDistance > threshold) return t.releaseToRefresh;
    return t.pullToRefresh;
  };

  const rotation = isRefreshing ? 360 : (pullDistance / threshold) * 180;

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{
        position: 'relative',
        height: '100%',
        overflow: 'auto',
        WebkitOverflowScrolling: 'touch'
      }}
    >
      {/* Pull Indicator */}
      <motion.div
        animate={{ height: pullDistance }}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(180deg, #f0f0f0 0%, white 100%)',
          overflow: 'hidden',
          zIndex: 10
        }}
      >
        <motion.div
          animate={{ rotate: rotation }}
          transition={{ duration: isRefreshing ? 1 : 0, repeat: isRefreshing ? Infinity : 0, ease: 'linear' }}
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            border: '3px solid #e0e0e0',
            borderTopColor: '#2563eb',
            marginBottom: '8px'
          }}
        />
        <div style={{
          fontSize: '12px',
          color: '#666',
          fontWeight: '500'
        }}>
          {getStatusText()}
        </div>
      </motion.div>

      {/* Content */}
      <motion.div
        animate={{ marginTop: pullDistance }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {children}
      </motion.div>
    </div>
  );
}

export default PullToRefresh;

