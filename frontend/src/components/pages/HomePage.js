import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import PageTitle from '../routing/PageTitle';
import translations from '../../translations';
import logger from '../../utils/logger';

/**
 * Home Page / Dashboard
 * Modernized in v4.7.0 with modern-ui classes
 */
const HomePage = ({ lang = 'ru' }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [ver, setVer] = useState({ message: '' });

  const t = translations[lang];

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (error) {
        logger.error('Failed to parse user:', error);
      }
    }

    // Fetch version info
    fetch('/api/version')
      .then(r => r.json())
      .then(data => setVer(data))
      .catch(err => logger.error('Failed to fetch version:', err));
  }, []);

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.3
      }
    }),
    hover: {
      scale: 1.03,
      boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
      transition: { duration: 0.2 }
    }
  };

  const dashboardCards = [
    {
      icon: '📤',
      title: t.uploadCard,
      description: t.uploadCardDesc,
      path: '/upload',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
      icon: '📇',
      title: t.viewContacts,
      description: t.viewContactsDesc,
      path: '/contacts',
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    },
    {
      icon: '📊',
      title: t.importExport,
      description: t.importExportDesc,
      path: '/import-export',
      gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
    },
    {
      icon: '⚙️',
      title: t.settings,
      description: t.settingsDesc,
      path: '/settings',
      gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
    }
  ];

  if (user?.is_admin) {
    dashboardCards.push({
      icon: '🛡️',
      title: t.adminPanel,
      description: t.adminPanelDesc,
      path: '/admin',
      gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
    });
  }

  return (
    <>
      <PageTitle title={t.dashboardTitle} lang={lang} />
      
      <div className="modern-page">
        {/* Header */}
        <motion.div
          className="modern-page-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="modern-page-title">
            📊 {t.dashboardTitle}
          </h1>
          <p className="modern-page-subtitle">
            {t.dashboardSubtitle}
          </p>
        </motion.div>

        {/* Dashboard Cards Grid */}
        <div className="modern-grid">
          {dashboardCards.map((card, index) => (
            <motion.div
              key={card.path}
              className="modern-card"
              onClick={() => navigate(card.path)}
              custom={index}
              initial="hidden"
              animate="visible"
              whileHover="hover"
              variants={cardVariants}
              style={{
                cursor: 'pointer',
                background: card.gradient,
                color: 'white',
                border: 'none',
                minHeight: '180px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                textAlign: 'center'
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>
                {card.icon}
              </div>
              <h3 style={{
                margin: '0 0 8px 0',
                fontSize: '20px',
                fontWeight: '600',
                color: 'white'
              }}>
                {card.title}
              </h3>
              <p style={{
                margin: 0,
                fontSize: '14px',
                opacity: 0.9,
                color: 'white'
              }}>
                {card.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Version Info */}
        {ver.message && (
          <motion.div
            className="modern-alert modern-alert-info modern-mt-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <strong>ℹ️ {t.latestUpdate}:</strong> {ver.message}
          </motion.div>
        )}
      </div>
    </>
  );
};

export default HomePage;
