import React, { useEffect, useState } from 'react';

export default function ContactList({lang='ru'}){
  const [contacts, setContacts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [selected, setSelected] = useState([]);
  const [showBulkEdit, setShowBulkEdit] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({});
  const [search, setSearch] = useState('');
  const [uidFilter, setUidFilter] = useState('');
  const [newContact, setNewContact] = useState({full_name:'',company:'',position:'',email:'',phone:'',address:'',comment:'',website:''});
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [sort, setSort] = useState('-id');
  const [detail, setDetail] = useState(null);
  const [zoom, setZoom] = useState(1);

  const load = async ()=>{
    const res = await fetch('http://localhost:8000/contacts/');
    const data = await res.json();
    setContacts(data);
    setFiltered(data);
  };

  useEffect(()=>{
    load();
    const handler = ()=>load();
    window.addEventListener('refresh-contacts', handler);
    return ()=> window.removeEventListener('refresh-contacts', handler);
  },[]);

  const applyFilters = (q, uidQ)=>{
    const ql = (q||'').toLowerCase();
    const ul = (uidQ||'').toLowerCase();
    let base = contacts.filter(c =>
      (c.full_name||'').toLowerCase().includes(ql) ||
      (c.email||'').toLowerCase().includes(ql) ||
      (c.phone||'').toLowerCase().includes(ql) ||
      (c.company||'').toLowerCase().includes(ql) ||
      (c.comment||'').toLowerCase().includes(ql) ||
      (c.website||'').toLowerCase().includes(ql)
    );
    if (ul) base = base.filter(c => (c.uid||'').toLowerCase().includes(ul));
    setFiltered(base);
  };

  const handleSearch = (e)=>{
    const q = e.target.value;
    setSearch(q);
    applyFilters(q, uidFilter);
  };

  const handleUidFilter = (e)=>{
    const val = e.target.value;
    setUidFilter(val);
    applyFilters(search, val);
  };

  const toggle = (id)=> setSelected(s => s.includes(id) ? s.filter(x=>x!==id) : [...s,id]);

  const updateContactField = async (id, patch)=>{
    await fetch(`http://localhost:8000/contacts/${id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(patch)});
  };

  const setContactLocal = (id, patch)=>{
    setContacts(prev => prev.map(c => c.id===id ? {...c, ...patch} : c));
    setFiltered(prev => prev.map(c => c.id===id ? {...c, ...patch} : c));
  };

  const deleteSelected = async ()=>{
    if(!selected.length) return alert(lang==='ru' ? 'Ничего не выбрано' : 'Nothing selected');
    if(!confirm(lang==='ru' ? `Удалить ${selected.length} контактов?` : `Delete ${selected.length} contacts?`)) return;
    await fetch('http://localhost:8000/contacts/delete_bulk', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(selected)});
    setSelected([]);
    await load();
  };

  const applyBulkEdit = async ()=>{
    const fields = Object.fromEntries(Object.entries(bulkEditData).filter(([k,v]) => v && v.trim() !== ''));
    if(!Object.keys(fields).length) return alert(lang==='ru' ? 'Введите хотя бы одно поле' : 'Enter at least one field');
    await fetch('http://localhost:8000/contacts/update_bulk', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ids:selected, fields})});
    setSelected([]); setShowBulkEdit(false); setBulkEditData({}); await load();
  };

  const createNew = async ()=>{
    const empty = Object.values(newContact).every(v=>!v);
    if(empty) return alert(lang==='ru' ? 'Заполните хотя бы одно поле' : 'Fill at least one field');
    await fetch('http://localhost:8000/contacts/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(newContact)});
    setNewContact({full_name:'',company:'',position:'',email:'',phone:'',address:'',comment:'',website:''});
    await load();
  };

  return (
    <div style={{marginTop:20}}>
      <h2>{lang==='ru' ? '📇 Контакты' : '📇 Contacts'}</h2>
      <div style={{display:'flex', gap:8, marginBottom:10}}>
        <input placeholder={lang==='ru' ? '🔍 Поиск...' : '🔍 Search...'} value={search} onChange={handleSearch} style={{flex:1, padding:8}} />
        <input placeholder="UID" value={uidFilter} onChange={handleUidFilter} style={{width:200, padding:8}} />
      </div>
      <div style={{marginBottom:10}}>
        <button onClick={deleteSelected}>🗑️ {lang==='ru' ? 'Удалить выбранные' : 'Delete selected'}</button>
        <button style={{marginLeft:8}} onClick={()=>setShowBulkEdit(!showBulkEdit)}>✏️ {lang==='ru' ? 'Массовое редактирование' : 'Bulk edit'}</button>
      </div>

      {showBulkEdit && (
        <div style={{border:'1px solid #ccc', padding:10, marginBottom:10}}>
          <h4>{lang==='ru' ? `Редактировать ${selected.length} контактов` : `Edit ${selected.length} contacts`}</h4>
          {['company','position','email','phone','address','comment','website'].map(f => (
            <input key={f} name={f} placeholder={f} onChange={(e)=>setBulkEditData({...bulkEditData, [f]: e.target.value})} style={{marginRight:6}} />
          ))}
          <button onClick={applyBulkEdit}>{lang==='ru' ? 'Применить' : 'Apply'}</button>
        </div>
      )}

      <table border="1" cellPadding="6" style={{width:'100%'}}>
        <thead>
          <tr><th></th><th>UID</th><th>{lang==='ru' ? 'Имя' : 'Name'}</th><th>{lang==='ru' ? 'Компания' : 'Company'}</th><th>{lang==='ru' ? 'Должность' : 'Position'}</th><th>Email</th><th>{lang==='ru' ? 'Телефон' : 'Phone'}</th><th>{lang==='ru' ? 'Адрес' : 'Address'}</th><th>{lang==='ru' ? 'Сайт' : 'Website'}</th><th>{lang==='ru' ? 'Комментарий' : 'Comment'}</th></tr>
        </thead>
        <tbody>
          {filtered.map(c => (
            <tr key={c.id} onClick={()=> setDetail(c)} style={{cursor:'pointer'}}>
              <td><input type="checkbox" checked={selected.includes(c.id)} onChange={()=>toggle(c.id)} onClick={(e)=> e.stopPropagation()} /></td>
              <td>{c.uid ? <span title={c.uid} style={{whiteSpace:'nowrap'}}>{c.uid.slice(0,8)}<button style={{marginLeft:6}} onClick={(e)=>{e.stopPropagation(); navigator.clipboard?.writeText(String(c.uid));}}>{lang==='ru'?'Коп.':'Copy'}</button></span> : ''}</td>
              <td>{c.full_name||''}</td>
              <td>{c.company||''}</td>
              <td>{c.position||''}</td>
              <td>{c.email||''}</td>
              <td>{c.phone||''}</td>
              <td>{c.address||''}</td>
              <td>{c.website ? <a href={c.website} target="_blank" rel="noreferrer" onClick={(e)=> e.stopPropagation()}>{c.website}</a> : ''}</td>
              <td>{c.comment||''}</td>
            </tr>
          ))}
          <tr style={{background:'#f7f7f7'}}>
            <td></td>
            <td style={{color:'#555'}}>{lang==='ru' ? 'Авто' : 'Auto'}</td>
            <td><input value={newContact.full_name} onChange={(e)=>setNewContact({...newContact, full_name:e.target.value})} placeholder={lang==='ru' ? 'Имя' : 'Name'} /></td>
            <td><input value={newContact.company} onChange={(e)=>setNewContact({...newContact, company:e.target.value})} placeholder={lang==='ru' ? 'Компания' : 'Company'} /></td>
            <td><input value={newContact.position} onChange={(e)=>setNewContact({...newContact, position:e.target.value})} placeholder={lang==='ru' ? 'Должность' : 'Position'} /></td>
            <td><input value={newContact.email} onChange={(e)=>setNewContact({...newContact, email:e.target.value})} placeholder="Email" /></td>
            <td><input value={newContact.phone} onChange={(e)=>setNewContact({...newContact, phone:e.target.value})} placeholder={lang==='ru' ? 'Телефон' : 'Phone'} /></td>
            <td><input value={newContact.address} onChange={(e)=>setNewContact({...newContact, address:e.target.value})} placeholder={lang==='ru' ? 'Адрес' : 'Address'} /></td>
            <td><input value={newContact.comment} onChange={(e)=>setNewContact({...newContact, comment:e.target.value})} placeholder={lang==='ru' ? 'Комментарий' : 'Comment'} /></td>
          </tr>
          <tr><td colSpan="10" style={{textAlign:'right'}}><button onClick={createNew}>➕ {lang==='ru' ? 'Добавить' : 'Add'}</button></td></tr>
        </tbody>
      </table>
    </div>
  );
}
