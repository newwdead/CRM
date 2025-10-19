import React, { useState } from 'react';
import ImportExport from './components/ImportExport';
import UploadCard from './components/UploadCard';
import ContactList from './components/ContactList';

const translations = {
  en: {
    title: 'Business Card CRM',
    upload: 'Upload card',
  },
  ru: {
    title: 'CRM визиток',
    upload: 'Загрузить визитку',
  }
};

function App(){
  const [lang, setLang] = useState('ru');
  const t = translations[lang];

  return (
    <div className="container">
      <header style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h1>{t.title}</h1>
        <div>
          <label>Lang: </label>
          <select value={lang} onChange={(e)=>setLang(e.target.value)}>
            <option value="ru">Рус</option>
            <option value="en">EN</option>
          </select>
        </div>
      </header>

      <ImportExport />
      <UploadCard lang={lang} />
      <ContactList lang={lang} />
    </div>
  );
}

export default App;
