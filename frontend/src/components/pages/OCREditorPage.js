import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { OCREditorContainer } from '../../modules/ocr';
import toast from 'react-hot-toast';

/**
 * OCR Editor Page - Отдельная страница для редактирования OCR блоков
 * 
 * URL: /contact/:id/ocr-editor
 */
const OCREditorPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contact, setContact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Загрузка контакта при монтировании
  useEffect(() => {
    loadContact();
  }, [id]);

  const loadContact = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(
        `/api/contacts/${id}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load contact');
      }

      const data = await response.json();
      setContact(data);
    } catch (err) {
      console.error('Error loading contact:', err);
      setError(err.message || 'Failed to load contact');
      toast.error('Ошибка загрузки контакта');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updatedData) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `/api/contacts/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(updatedData)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save contact');
      }

      toast.success('OCR данные сохранены!');
      
      // Перезагрузить контакт после сохранения
      await loadContact();
    } catch (err) {
      console.error('Error saving OCR data:', err);
      toast.error('Ошибка сохранения: ' + err.message);
    }
  };

  const handleClose = () => {
    // Вернуться на страницу списка контактов или карточку контакта
    navigate('/contacts');
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка редактора OCR...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="text-red-600 text-center mb-4">
            <svg className="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-semibold mb-2">Ошибка загрузки</h2>
            <p className="text-gray-600 mb-4">{error}</p>
          </div>
          <button
            onClick={() => navigate('/contacts')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Вернуться к контактам
          </button>
        </div>
      </div>
    );
  }

  // No contact found
  if (!contact) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <p className="text-gray-600 mb-4">Контакт не найден</p>
          <button
            onClick={() => navigate('/contacts')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Вернуться к контактам
          </button>
        </div>
      </div>
    );
  }

  // Main OCR Editor
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={handleClose}
              className="text-gray-600 hover:text-gray-900 transition-colors"
              title="Вернуться назад"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                Редактор OCR блоков
              </h1>
              <p className="text-sm text-gray-500">
                {contact.full_name || 'Без имени'} 
                {contact.company && ` - ${contact.company}`}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              ID: {contact.id}
            </span>
          </div>
        </div>
      </div>

      {/* OCR Editor Container */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <OCREditorContainer
          contact={contact}
          onSave={handleSave}
          onClose={handleClose}
        />
      </div>
    </div>
  );
};

export default OCREditorPage;

