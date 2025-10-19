import React, { useEffect, useState } from 'react';

export default function Settings({ lang='ru', defaultProvider='tesseract', onChangeLang, onChangeProvider }){
  const [locLang, setLocLang] = useState(lang);
  const [provider, setProvider] = useState(defaultProvider);

  useEffect(()=>{ setLocLang(lang) }, [lang]);
  useEffect(()=>{ setProvider(defaultProvider) }, [defaultProvider]);

  const save = ()=>{
    onChangeLang?.(locLang);
    onChangeProvider?.(provider);
    try {
      localStorage.setItem('app.lang', locLang);
      localStorage.setItem('app.defaultProvider', provider);
    } catch {}
    alert(locLang==='ru' ? 'Настройки сохранены' : 'Settings saved');
  };

  return (
    <div style={{paddingTop:10}}>
      <h2>{locLang==='ru' ? '⚙️ Настройки' : '⚙️ Settings'}</h2>

      <div style={{marginBottom:12}}>
        <label style={{marginRight:8}}>{locLang==='ru' ? 'Язык интерфейса' : 'Interface language'}</label>
        <select value={locLang} onChange={(e)=> setLocLang(e.target.value)}>
          <option value="ru">Рус</option>
          <option value="en">EN</option>
        </select>
      </div>

      <div style={{marginBottom:12}}>
        <label style={{marginRight:8}}>{locLang==='ru' ? 'Провайдер OCR по умолчанию' : 'Default OCR provider'}</label>
        <select value={provider} onChange={(e)=> setProvider(e.target.value)}>
          <option value="tesseract">Tesseract</option>
          <option value="parsio">Parsio</option>
        </select>
      </div>

      <button onClick={save}>{locLang==='ru' ? 'Сохранить' : 'Save'}</button>

      <div style={{marginTop:16, color:'#555', fontSize:14}}>
        <div>{locLang==='ru' ? 'Подсказка: настройки сохраняются в браузере (localStorage).' : 'Note: settings are saved in browser localStorage.'}</div>
      </div>
    </div>
  );
}
