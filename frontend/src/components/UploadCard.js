import React, { useState } from 'react';

export default function UploadCard({lang='ru'}){
  const [file, setFile] = useState(null);
  const [provider, setProvider] = useState('tesseract');

  const upload = async () => {
    if(!file) return alert(lang==='ru' ? 'Выберите файл визитки!' : 'Choose a file!');
    const fd = new FormData();
    fd.append('file', file);
    const url = `http://localhost:8000/upload/?provider=${encodeURIComponent(provider)}`;
    const res = await fetch(url, { method: 'POST', body: fd });
    if(res.ok){
      const data = await res.json();
      alert(lang==='ru' ? 'Визитка распознана и добавлена.' : 'Card recognized and added.');
      window.dispatchEvent(new Event('refresh-contacts'));
    } else {
      let message = lang==='ru' ? 'Ошибка загрузки' : 'Upload error';
      try {
        const err = await res.json();
        if(err && err.detail){ message = err.detail; }
      } catch(_){}
      alert(message);
    }
  };

  return (
    <div style={{marginTop:20}}>
      <h3>{lang==='ru' ? '📤 Загрузить визитку' : '📤 Upload card'}</h3>
      <div style={{marginBottom:8}}>
        <label style={{marginRight:6}}>{lang==='ru' ? 'Провайдер OCR:' : 'OCR Provider:'}</label>
        <select value={provider} onChange={(e)=>setProvider(e.target.value)}>
          <option value="tesseract">Tesseract</option>
          <option value="parsio">Parsio</option>
        </select>
      </div>
      <input type="file" onChange={(e)=>setFile(e.target.files[0])} />
      <button onClick={upload} style={{marginLeft:10}}>{lang==='ru' ? 'Загрузить' : 'Upload'}</button>
    </div>
  );
}
