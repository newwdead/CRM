import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ContactList from '../ContactList';
import PageTitle from '../routing/PageTitle';

/**
 * Contacts Page
 * Wraps ContactList with routing support
 * Supports query parameters for filters
 */
const ContactsPage = ({ lang = 'ru' }) => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const handleEdit = (id) => {
    navigate(`/contacts/${id}`);
  };

  const handleOCREdit = (id) => {
    navigate(`/contacts/${id}?mode=ocr`);
  };

  // Sync filters with URL query parameters
  const handleFilterChange = (filters) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
    setSearchParams(params);
  };

  // Get initial filters from URL
  const initialFilters = {
    search: searchParams.get('search') || '',
    tag: searchParams.get('tag') || '',
    group: searchParams.get('group') || '',
    company: searchParams.get('company') || '',
    page: parseInt(searchParams.get('page') || '1'),
    limit: parseInt(searchParams.get('limit') || '20')
  };

  return (
    <>
      <PageTitle title={lang === 'ru' ? 'Контакты' : 'Contacts'} lang={lang} />
      <ContactList 
        onEdit={handleEdit}
        onOCREdit={handleOCREdit}
        t={{}} 
        lang={lang}
        initialFilters={initialFilters}
        onFilterChange={handleFilterChange}
      />
    </>
  );
};

export default ContactsPage;

