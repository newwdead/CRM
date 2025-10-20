import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * 404 Not Found Page
 */
const NotFound = ({ lang = 'ru' }) => {
  const t = {
    en: {
      title: '404 - Page Not Found',
      subtitle: 'The page you are looking for does not exist',
      backHome: 'Go to Home',
      backContacts: 'View Contacts',
      description: 'It seems you\'ve followed a broken link or entered a URL that doesn\'t exist.'
    },
    ru: {
      title: '404 - Страница не найдена',
      subtitle: 'Запрашиваемая страница не существует',
      backHome: 'На главную',
      backContacts: 'К контактам',
      description: 'Похоже, вы перешли по неработающей ссылке или ввели несуществующий URL.'
    }
  };

  const text = t[lang];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '70vh',
        textAlign: 'center',
        padding: '40px 20px'
      }}
    >
      <motion.div
        animate={{ rotate: [0, 10, -10, 0] }}
        transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
        style={{ fontSize: '120px', marginBottom: '20px' }}
      >
        🔍
      </motion.div>

      <h1 style={{ 
        fontSize: '48px', 
        fontWeight: '700', 
        marginBottom: '16px',
        color: '#1f2937'
      }}>
        {text.title}
      </h1>

      <p style={{ 
        fontSize: '18px', 
        color: '#6b7280', 
        marginBottom: '32px',
        maxWidth: '500px'
      }}>
        {text.description}
      </p>

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <button className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '16px' }}>
            🏠 {text.backHome}
          </button>
        </Link>

        <Link to="/contacts" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary" style={{ padding: '12px 24px', fontSize: '16px' }}>
            📇 {text.backContacts}
          </button>
        </Link>
      </div>
    </motion.div>
  );
};

export default NotFound;

