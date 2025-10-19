import React, { useEffect, useState } from 'react';

export default function UploadCard({lang='ru', defaultProvider='tesseract'}){
  const [file, setFile] = useState(null);
  const [provider, setProvider] = useState(defaultProvider || 'tesseract');
  const [error, setError] = useState(null);
  const [showError, setShowError] = useState(false);

  const upload = async () => {
    if(!file) {
      setError(lang==='ru' ? 'Выберите файл визитки!' : 'Choose a file!');
      setShowError(true);
      return;
    }
    const fd = new FormData();
    fd.append('file', file);
    const url = `/api/upload/?provider=${encodeURIComponent(provider)}`;
    const res = await fetch(url, { method: 'POST', body: fd });
    if(res.ok){
      const data = await res.json();
      window.dispatchEvent(new Event('refresh-contacts'));
    } else {
      let message = lang==='ru' ? 'Ошибка загрузки' : 'Upload error';
      try {
        const err = await res.json();
        if(err && err.detail){ message = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail); }
      } catch(_){ }
      setError(message);
      setShowError(true);
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

      {showError && (
        <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.35)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:9999}} onClick={()=>setShowError(false)}>
          <div style={{background:'#fff', padding:16, borderRadius:8, width:'min(600px, 90vw)'}} onClick={e=>e.stopPropagation()}>
            <h3 style={{marginTop:0}}>{lang==='ru' ? 'Ошибка' : 'Error'}</h3>
            <pre style={{whiteSpace:'pre-wrap', wordBreak:'break-word', background:'#f7f7f7', padding:8, borderRadius:6, maxHeight:300, overflow:'auto'}}>{error}</pre>
            <div style={{display:'flex', gap:8, justifyContent:'flex-end'}}>
              <button onClick={() => { navigator.clipboard?.writeText(String(error||'')); }}>
                {lang==='ru' ? 'Скопировать' : 'Copy'}
              </button>
              <button onClick={()=>setShowError(false)}>
                {lang==='ru' ? 'Закрыть' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
