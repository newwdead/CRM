import React, { useEffect, useState } from 'react';
import ImportExport from './components/ImportExport';
import UploadCard from './components/UploadCard';
import ContactList from './components/ContactList';
import ContactEdit from './components/ContactEdit';
import Settings from './components/Settings';
import TelegramSettings from './components/TelegramSettings';

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
  const [defaultProvider, setDefaultProvider] = useState('tesseract');
  const [route, setRoute] = useState('home'); // 'home' | 'settings' | 'edit' | 'telegram'
  const [editId, setEditId] = useState(null);
  const t = translations[lang];

  useEffect(()=>{
    try {
      const lsLang = localStorage.getItem('app.lang');
      const lsProv = localStorage.getItem('app.defaultProvider');
      if(lsLang) setLang(lsLang);
      if(lsProv) setDefaultProvider(lsProv);
    } catch {}
  },[]);

  return (
    <div className="container">
      <header style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h1>{t.title}</h1>
        <nav style={{display:'flex', gap:8}}>
          <button onClick={()=>setRoute('home')} disabled={route==='home'}>{lang==='ru' ? 'Главная' : 'Home'}</button>
          <button onClick={()=>setRoute('settings')} disabled={route==='settings'}>{lang==='ru' ? 'Настройки' : 'Settings'}</button>
          <button onClick={()=>setRoute('telegram')} disabled={route==='telegram'}>{lang==='ru' ? 'Telegram' : 'Telegram'}</button>
        </nav>
      </header>

      {route==='home' && (
        <>
          <ImportExport />
          <UploadCard lang={lang} defaultProvider={defaultProvider} />
          <ContactList lang={lang} onEdit={(id)=>{ setEditId(id); setRoute('edit'); }} />
        </>
      )}
      {route==='settings' && (
        <Settings
          lang={lang}
          defaultProvider={defaultProvider}
          onChangeLang={setLang}
          onChangeProvider={setDefaultProvider}
        />
      )}
      {route==='edit' && (
        <ContactEdit id={editId} lang={lang} onBack={()=> setRoute('home')} />
      )}
      {route==='telegram' && (
        <TelegramSettings lang={lang} />
      )}
    </div>
  );
}

export default App;
