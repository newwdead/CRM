import React, { useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Mobile-optimized Contact Card View
 * Alternative to table view for mobile devices
 * 
 * Features:
 * - Card-based layout for easy viewing
 * - Swipe-enabled actions (call, email, edit, delete)
 * - Touch-friendly UI
 * - Optimized for small screens
 */
function ContactCardView({ contacts, onCall, onEmail, onEdit, onDelete, lang = 'ru' }) {
  const [swipedCard, setSwipedCard] = useState(null);

  const t = {
    en: {
      call: 'Call',
      email: 'Email',
      edit: 'Edit',
      delete: 'Delete',
      company: 'Company',
      position: 'Position',
      noPhone: 'No phone',
      noEmail: 'No email',
      noContacts: 'No contacts found',
      swipeLeft: 'Swipe left for actions'
    },
    ru: {
      call: 'Позвонить',
      email: 'Email',
      edit: 'Редактировать',
      delete: 'Удалить',
      company: 'Компания',
      position: 'Должность',
      noPhone: 'Нет телефона',
      noEmail: 'Нет email',
      noContacts: 'Контакты не найдены',
      swipeLeft: 'Свайп влево для действий'
    }
  }[lang];

  const handleSwipeStart = (e, contactId) => {
    const touch = e.touches[0];
    setSwipedCard({ id: contactId, startX: touch.clientX });
  };

  const handleSwipeEnd = (e, contactId) => {
    const touch = e.changedTouches[0];
    const diff = swipedCard.startX - touch.clientX;

    if (diff > 50) {
      // Swiped left - show actions
      setSwipedCard({ ...swipedCard, swiped: true });
    } else if (diff < -50) {
      // Swiped right - hide actions
      setSwipedCard(null);
    }
  };

  if (!contacts || contacts.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px 20px',
        color: '#999'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
        <p>{t.noContacts}</p>
      </div>
    );
  }

  return (
    <div style={{
      padding: '8px',
      maxWidth: '600px',
      margin: '0 auto'
    }}>
      {contacts.map((contact) => {
        const isExpanded = swipedCard?.id === contact.id && swipedCard?.swiped;
        const fullName = contact.last_name || contact.first_name
          ? `${contact.last_name || ''} ${contact.first_name || ''} ${contact.middle_name || ''}`.trim()
          : contact.full_name || 'Без имени';

        return (
          <motion.div
            key={contact.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              position: 'relative',
              marginBottom: '12px',
              overflow: 'hidden',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
            onTouchStart={(e) => handleSwipeStart(e, contact.id)}
            onTouchEnd={(e) => handleSwipeEnd(e, contact.id)}
          >
            {/* Contact Card */}
            <motion.div
              animate={{ x: isExpanded ? -120 : 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              style={{
                background: 'white',
                padding: '16px',
                position: 'relative',
                zIndex: 2
              }}
            >
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                {/* Avatar/Photo */}
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '8px',
                  background: contact.photo_path 
                    ? `url(/files/${contact.thumbnail_path || contact.photo_path}) center/cover` 
                    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '24px',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>
                  {!contact.photo_path && (fullName[0] || '?').toUpperCase()}
                </div>

                {/* Contact Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{
                    margin: '0 0 4px 0',
                    fontSize: '16px',
                    fontWeight: '600',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {fullName}
                  </h3>

                  {contact.company && (
                    <div style={{
                      fontSize: '14px',
                      color: '#666',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      marginBottom: '2px'
                    }}>
                      🏢 {contact.company}
                    </div>
                  )}

                  {contact.position && (
                    <div style={{
                      fontSize: '13px',
                      color: '#999',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {contact.position}
                    </div>
                  )}

                  {/* Quick Contact Buttons */}
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: '8px',
                    flexWrap: 'wrap'
                  }}>
                    {contact.phone && (
                      <a
                        href={`tel:${contact.phone}`}
                        style={{
                          padding: '6px 12px',
                          background: '#4CAF50',
                          color: 'white',
                          borderRadius: '6px',
                          fontSize: '13px',
                          textDecoration: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onCall) onCall(contact);
                        }}
                      >
                        📞 {t.call}
                      </a>
                    )}

                    {contact.email && (
                      <a
                        href={`mailto:${contact.email}`}
                        style={{
                          padding: '6px 12px',
                          background: '#2196F3',
                          color: 'white',
                          borderRadius: '6px',
                          fontSize: '13px',
                          textDecoration: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onEmail) onEmail(contact);
                        }}
                      >
                        ✉️ {t.email}
                      </a>
                    )}
                  </div>
                </div>
              </div>

              {/* Swipe Indicator */}
              {!isExpanded && (
                <div style={{
                  position: 'absolute',
                  bottom: '4px',
                  right: '8px',
                  fontSize: '10px',
                  color: '#ccc'
                }}>
                  ← {t.swipeLeft}
                </div>
              )}
            </motion.div>

            {/* Action Buttons (Revealed on Swipe) */}
            <div style={{
              position: 'absolute',
              right: 0,
              top: 0,
              height: '100%',
              display: 'flex',
              gap: '2px',
              zIndex: 1
            }}>
              <button
                onClick={() => {
                  setSwipedCard(null);
                  if (onEdit) onEdit(contact);
                }}
                style={{
                  width: '60px',
                  background: '#FF9800',
                  border: 'none',
                  color: 'white',
                  fontSize: '20px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px'
                }}
              >
                <span>✏️</span>
                <span style={{ fontSize: '10px' }}>{t.edit}</span>
              </button>
              <button
                onClick={() => {
                  setSwipedCard(null);
                  if (onDelete) onDelete(contact);
                }}
                style={{
                  width: '60px',
                  background: '#F44336',
                  border: 'none',
                  color: 'white',
                  fontSize: '20px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px'
                }}
              >
                <span>🗑️</span>
                <span style={{ fontSize: '10px' }}>{t.delete}</span>
              </button>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

export default ContactCardView;

