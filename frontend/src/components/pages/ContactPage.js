import React from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import ContactEdit from '../ContactEdit';
import OCREditorWithBlocks from '../OCREditorWithBlocks';
import PageTitle from '../routing/PageTitle';
import toast from 'react-hot-toast';

/**
 * Contact Page
 * Shows contact details with edit and OCR modes via URL
 */
const ContactPage = ({ lang = 'ru' }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const mode = searchParams.get('mode'); // 'edit' or 'ocr'
  const [contact, setContact] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (id && mode === 'ocr') {
      // Fetch contact for OCR mode
      const token = localStorage.getItem('token');
      fetch(`/api/contacts/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(data => {
          setContact(data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to fetch contact:', err);
          toast.error(lang === 'ru' ? 'Не удалось загрузить контакт' : 'Failed to load contact');
          navigate('/contacts');
        });
    } else {
      setLoading(false);
    }
  }, [id, mode, lang, navigate]);

  const handleBack = () => {
    navigate('/contacts');
  };

  const handleOCRSave = async (updatedData) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/contacts/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(updatedData)
    });
    
    if (!response.ok) throw new Error('Failed to update contact');
    
    toast.success(lang === 'ru' ? 'Контакт обновлен' : 'Contact updated');
    navigate('/contacts');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div className="spinner"></div>
        <p>{lang === 'ru' ? 'Загрузка...' : 'Loading...'}</p>
      </div>
    );
  }

  // OCR Editor mode
  if (mode === 'ocr' && contact) {
    return (
      <>
        <PageTitle 
          title={`${lang === 'ru' ? 'Редактор OCR' : 'OCR Editor'} - ${contact.first_name || contact.uid}`}
          lang={lang}
        />
        <OCREditorWithBlocks
          contact={contact}
          onSave={handleOCRSave}
          onClose={handleBack}
        />
      </>
    );
  }

  // Edit mode (default)
  return (
    <>
      <PageTitle 
        title={lang === 'ru' ? 'Редактирование контакта' : 'Edit Contact'}
        lang={lang}
      />
      <ContactEdit 
        id={id} 
        onBack={handleBack} 
        t={{}} 
        lang={lang} 
      />
    </>
  );
};

export default ContactPage;

