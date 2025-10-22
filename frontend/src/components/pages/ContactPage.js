import React from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import ContactEdit from '../ContactEdit';
import PageTitle from '../routing/PageTitle';

/**
 * Contact Page
 * Shows contact details with edit and OCR modes via URL
 */
const ContactPage = ({ lang = 'ru' }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const mode = searchParams.get('mode'); // 'edit' or 'ocr'

  React.useEffect(() => {
    if (id && mode === 'ocr') {
      // Redirect to new OCR editor page
      navigate(`/contacts/${id}/ocr-editor`, { replace: true });
    }
  }, [id, mode, navigate]);

  const handleBack = () => {
    navigate('/contacts');
  };

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

