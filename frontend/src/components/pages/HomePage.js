import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import PageTitle from '../routing/PageTitle';
import translations from '../../translations';

/**
 * Home Page / Dashboard
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
        console.error('Failed to parse user:', error);
      }
    }

    // Fetch version info
    fetch('/api/version')
      .then(r => r.json())
      .then(data => setVer(data))
      .catch(err => console.error('Failed to fetch version:', err));
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
      scale: 1.05,
      boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
      transition: { duration: 0.2 }
    }
  };

  return (
    <>
      <PageTitle title={t.dashboardTitle} lang={lang} />
      
      <motion.div 
        className="home-dashboard"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="dashboard-header">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            📊 {t.dashboardTitle}
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {t.dashboardSubtitle}
          </motion.p>
        </div>
        
        <div className="dashboard-grid">
          <motion.div 
            className="dashboard-card" 
            onClick={() => navigate('/upload')}
            custom={0}
            initial="hidden"
            animate="visible"
            whileHover="hover"
            variants={cardVariants}
          >
            <div className="dashboard-icon">📤</div>
            <h3>{t.uploadCard}</h3>
            <p>{t.uploadCardDesc}</p>
          </motion.div>

          <motion.div 
            className="dashboard-card" 
            onClick={() => navigate('/contacts')}
            custom={1}
            initial="hidden"
            animate="visible"
            whileHover="hover"
            variants={cardVariants}
          >
            <div className="dashboard-icon">📇</div>
            <h3>{t.viewContacts}</h3>
            <p>{t.viewContactsDesc}</p>
          </motion.div>

          <motion.div 
            className="dashboard-card" 
            onClick={() => navigate('/import-export')}
            custom={2}
            initial="hidden"
            animate="visible"
            whileHover="hover"
            variants={cardVariants}
          >
            <div className="dashboard-icon">📊</div>
            <h3>{t.importExport}</h3>
            <p>{t.importExportDesc}</p>
          </motion.div>

          <motion.div 
            className="dashboard-card" 
            onClick={() => navigate('/settings')}
            custom={3}
            initial="hidden"
            animate="visible"
            whileHover="hover"
            variants={cardVariants}
          >
            <div className="dashboard-icon">⚙️</div>
            <h3>{t.settings}</h3>
            <p>{t.settingsDesc}</p>
          </motion.div>

          {user?.is_admin && (
            <motion.div 
              className="dashboard-card" 
              onClick={() => navigate('/admin')}
              custom={4}
              initial="hidden"
              animate="visible"
              whileHover="hover"
              variants={cardVariants}
            >
              <div className="dashboard-icon">🛡️</div>
              <h3>{t.adminPanel}</h3>
              <p>{t.adminPanelDesc}</p>
            </motion.div>
          )}
        </div>

        {ver.message && (
          <motion.div 
            className="dashboard-info"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h3>ℹ️ {t.latestUpdate}</h3>
            <p>{ver.message}</p>
          </motion.div>
        )}
      </motion.div>
    </>
  );
};

export default HomePage;

