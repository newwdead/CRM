/**
 * QRViewer - Сканирование и отображение QR кодов с визиток
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const QRViewer = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [contact, setContact] = useState(null);
  const [qrResult, setQrResult] = useState(null);

  useEffect(() => {
    loadContact();
  }, [id]);

  const loadContact = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to load contact');

      const data = await response.json();
      setContact(data);

      // If contact already has QR data, display it
      if (data.has_qr_code && data.qr_data) {
        parseStoredQR(data.qr_data);
      }
    } catch (error) {
      console.error('Error loading contact:', error);
      toast.error('Не удалось загрузить контакт');
    }
  };

  const parseStoredQR = (qrData) => {
    // Simple parsing for display
    const result = {
      has_qr: true,
      qr_data: qrData,
      qr_type: 'vCard' in qrData.toUpperCase() ? 'vCard' : 
                qrData.toUpperCase().startsWith('MECARD:') ? 'MeCard' : 'Other',
      message: 'QR код загружен из базы данных'
    };
    setQrResult(result);
  };

  const scanQR = async () => {
    setScanning(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${id}/scan-qr`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to scan QR');

      const data = await response.json();
      setQrResult(data);

      if (data.has_qr) {
        toast.success(data.message);
      } else {
        toast.info(data.message);
      }
    } catch (error) {
      console.error('Error scanning QR:', error);
      toast.error('Ошибка сканирования QR кода');
    } finally {
      setScanning(false);
    }
  };

  const applyQRData = async () => {
    if (!window.confirm('Применить данные из QR кода к контакту? Существующие данные будут обновлены.')) {
      return;
    }

    setApplying(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/contacts/${id}/apply-qr-data`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to apply QR data');

      const data = await response.json();
      toast.success(data.message);
      
      // Reload contact
      await loadContact();
    } catch (error) {
      console.error('Error applying QR data:', error);
      toast.error('Ошибка применения данных');
    } finally {
      setApplying(false);
    }
  };

  const renderQRContent = () => {
    if (!qrResult || !qrResult.has_qr) return null;

    const { qr_data, qr_type, contact_data } = qrResult;

    return (
      <div style={{ marginTop: '20px' }}>
        {/* QR Type Badge */}
        <div style={{ marginBottom: '15px' }}>
          <span style={{
            padding: '6px 12px',
            backgroundColor: qr_type === 'vCard' ? '#10b981' : qr_type === 'MeCard' ? '#3b82f6' : '#6b7280',
            color: 'white',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '600'
          }}>
            {qr_type === 'vCard' && '📇 vCard'}
            {qr_type === 'MeCard' && '📇 MeCard'}
            {qr_type === 'Other' && '🔗 Другой формат'}
          </span>
        </div>

        {/* Contact Data from QR (if parsed) */}
        {contact_data && Object.keys(contact_data).length > 0 && (
          <div style={{
            padding: '20px',
            backgroundColor: '#f0fdf4',
            border: '2px solid #10b981',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>
              ✅ Распознанные данные:
            </h3>

            <div style={{ display: 'grid', gap: '12px' }}>
              {contact_data.full_name && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>ФИО:</span>{' '}
                  <span>{contact_data.full_name}</span>
                </div>
              )}
              
              {(contact_data.first_name || contact_data.last_name) && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Имя:</span>{' '}
                  <span>{[contact_data.last_name, contact_data.first_name, contact_data.middle_name].filter(Boolean).join(' ')}</span>
                </div>
              )}

              {contact_data.company && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Компания:</span>{' '}
                  <span>{contact_data.company}</span>
                </div>
              )}

              {contact_data.position && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Должность:</span>{' '}
                  <span>{contact_data.position}</span>
                </div>
              )}

              {contact_data.email && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Email:</span>{' '}
                  <span>{contact_data.email}</span>
                </div>
              )}

              {contact_data.phone && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Телефон:</span>{' '}
                  <span>{contact_data.phone}</span>
                </div>
              )}

              {contact_data.phone_mobile && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Мобильный:</span>{' '}
                  <span>{contact_data.phone_mobile}</span>
                </div>
              )}

              {contact_data.address && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Адрес:</span>{' '}
                  <span>{contact_data.address}</span>
                </div>
              )}

              {contact_data.website && (
                <div>
                  <span style={{ fontWeight: '600', color: '#6b7280' }}>Веб-сайт:</span>{' '}
                  <span>{contact_data.website}</span>
                </div>
              )}
            </div>

            <button
              onClick={applyQRData}
              disabled={applying}
              style={{
                marginTop: '20px',
                padding: '10px 20px',
                backgroundColor: applying ? '#9ca3af' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: applying ? 'not-allowed' : 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              {applying ? '⏳ Применение...' : '✅ Применить данные к контакту'}
            </button>
          </div>
        )}

        {/* Raw QR Data */}
        <div style={{
          padding: '15px',
          backgroundColor: '#f9fafb',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          marginTop: '15px'
        }}>
          <h4 style={{ marginTop: 0, marginBottom: '10px', fontSize: '14px', fontWeight: '600', color: '#6b7280' }}>
            📄 Сырые данные QR кода:
          </h4>
          <pre style={{
            padding: '10px',
            backgroundColor: '#1f2937',
            color: '#f3f4f6',
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '12px',
            maxHeight: '300px',
            margin: 0
          }}>
            {qr_data}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            🔍 Сканирование QR кода
          </h1>
          {contact && (
            <p style={{ margin: '8px 0 0', color: '#666', fontSize: '14px' }}>
              Контакт: {contact.full_name || contact.first_name || `ID: ${contact.id}`}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={scanQR}
            disabled={scanning}
            style={{
              padding: '10px 20px',
              backgroundColor: scanning ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: scanning ? 'not-allowed' : 'pointer',
              fontWeight: '600'
            }}
          >
            {scanning ? '🔄 Сканирование...' : '🔍 Сканировать QR'}
          </button>

          <button
            onClick={() => navigate(`/contacts/${id}`)}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            ← К контакту
          </button>
        </div>
      </div>

      {/* Contact Image */}
      {contact && contact.photo_path && (
        <div style={{
          marginBottom: '20px',
          textAlign: 'center',
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <img
            src={`/files/${contact.photo_path}`}
            alt="Business card"
            style={{
              maxWidth: '100%',
              maxHeight: '500px',
              borderRadius: '4px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}
          />
        </div>
      )}

      {/* QR Result */}
      {qrResult && !qrResult.has_qr && (
        <div style={{
          padding: '20px',
          backgroundColor: '#fef3c7',
          border: '2px solid #f59e0b',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>❌</div>
          <div style={{ fontSize: '16px', fontWeight: '600' }}>
            {qrResult.message}
          </div>
        </div>
      )}

      {/* QR Content */}
      {renderQRContent()}

      {/* Info Box */}
      <div style={{
        marginTop: '30px',
        padding: '15px',
        backgroundColor: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#1e40af'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '8px' }}>ℹ️ Поддерживаемые форматы:</div>
        <ul style={{ margin: '0', paddingLeft: '20px' }}>
          <li><strong>vCard</strong> - стандартный формат для визиток (BEGIN:VCARD...END:VCARD)</li>
          <li><strong>MeCard</strong> - упрощённый формат (MECARD:N:...)</li>
          <li><strong>URL</strong> - ссылки и другой текст</li>
        </ul>
      </div>
    </div>
  );
};

export default QRViewer;

