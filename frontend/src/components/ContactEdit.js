import React, { useEffect, useState } from 'react';

export default function ContactEdit({ id, lang='ru', onBack }){
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const t = {
    ru: {
      title: 'Редактирование контакта',
      back: 'Назад',
      save: 'Сохранить',
      uid: 'UID',
      name: 'Имя',
      company: 'Компания',
      position: 'Должность',
      email: 'Email',
      phone: 'Телефон',
      address: 'Адрес',
      website: 'Сайт',
      comment: 'Комментарий',
      photo: 'Фото',
      openOriginal: 'Открыть оригинал',
      saved: 'Сохранено',
      notFound: 'Контакт не найден',
    },
    en: {
      title: 'Edit contact',
      back: 'Back',
      save: 'Save',
      uid: 'UID',
      name: 'Name',
      company: 'Company',
      position: 'Position',
      email: 'Email',
      phone: 'Phone',
      address: 'Address',
      website: 'Website',
      comment: 'Comment',
      photo: 'Photo',
      openOriginal: 'Open original',
      saved: 'Saved',
      notFound: 'Contact not found',
    }
  }[lang] || {};

  useEffect(()=>{
    let cancel = false;
    const load = async ()=>{
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Прямой запрос конкретного контакта по ID
        const res = await fetch(`/api/contacts/${id}`, { headers });
        
        if (res.ok) {
          const contact = await res.json();
          if(!cancel){
            setData(contact);
          }
        } else {
          if(!cancel) setData(null);
        }
      } catch (e) {
        console.error('Error loading contact:', e);
        if(!cancel) setData(null);
      } finally {
        if(!cancel) setLoading(false);
      }
    };
    load();
    return ()=>{ cancel = true };
  }, [id]);

  const save = async ()=>{
    if(!data) return;
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const patch = {
        full_name: data.full_name || null,
        company: data.company || null,
        position: data.position || null,
        email: data.email || null,
        phone: data.phone || null,
        address: data.address || null,
        website: data.website || null,
        comment: data.comment || null,
      };
      await fetch(`/api/contacts/${id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(patch)
      });
      alert(t.saved);
      // обновить список
      window.dispatchEvent(new Event('refresh-contacts'));
      onBack?.();
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>{lang==='ru' ? 'Загрузка...' : 'Loading...'}</div>;
  if (!data) return <div>{t.notFound} <button onClick={onBack}>{t.back}</button></div>;

  return (
    <div style={{marginTop:20}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h2 style={{margin:0}}>{t.title}</h2>
        <button onClick={onBack}>{t.back}</button>
      </div>

      {data.uid && (
        <div style={{marginTop:12}}>
          <label style={{display:'block', fontWeight:'bold'}}>{t.uid}</label>
          <div style={{display:'flex', alignItems:'center', gap:8}}>
            <code>{data.uid}</code>
            <button onClick={()=>navigator.clipboard?.writeText(String(data.uid))}>{lang==='ru'?'Коп.':'Copy'}</button>
          </div>
        </div>
      )}

      {data.photo_path && (
        <div style={{marginTop:12}}>
          <label style={{display:'block', fontWeight:'bold'}}>{t.photo}</label>
          <div style={{display:'flex', alignItems:'center', gap:12, marginBottom:8}}>
            <a href={`/files/${data.photo_path}`} target="_blank" rel="noreferrer">{t.openOriginal}</a>
          </div>
          <div style={{border:'1px solid #ddd', padding:8, maxWidth: '100%', overflow:'auto'}}>
            <img
              src={`/files/${data.photo_path}`}
              alt="card"
              style={{maxWidth: '600px', width: '100%', height: 'auto'}}
              onError={(e)=>{ e.currentTarget.style.display='none'; }}
            />
          </div>
        </div>
      )}

      <div style={{marginTop:12, display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
        <div>
          <label style={{display:'block'}}>{t.name}</label>
          <input value={data.full_name||''} onChange={e=>setData({...data, full_name:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.company}</label>
          <input value={data.company||''} onChange={e=>setData({...data, company:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.position}</label>
          <input value={data.position||''} onChange={e=>setData({...data, position:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.email}</label>
          <input value={data.email||''} onChange={e=>setData({...data, email:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.phone}</label>
          <input value={data.phone||''} onChange={e=>setData({...data, phone:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.address}</label>
          <input value={data.address||''} onChange={e=>setData({...data, address:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.website}</label>
          <input value={data.website||''} onChange={e=>setData({...data, website:e.target.value})} />
        </div>
        <div>
          <label style={{display:'block'}}>{t.comment}</label>
          <input value={data.comment||''} onChange={e=>setData({...data, comment:e.target.value})} />
        </div>
      </div>

      <div style={{marginTop:16}}>
        <button onClick={save} disabled={saving}>{t.save}</button>
      </div>
    </div>
  );
}
