import React, { useState } from 'react';

export default function ImportExport(){
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');

  const handleExportCSV = ()=> window.open('/api/contacts/export', '_blank');
  const handleExportXLSX = ()=> window.open('/api/contacts/export/xlsx', '_blank');

  const handleImport = async ()=>{
    if(!file) return alert('Choose file');
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch('/api/contacts/import', { method:'POST', body: fd });
    const data = await res.json();
    setStatus(data.message || data.imported || data.error || JSON.stringify(data));
    window.dispatchEvent(new Event('refresh-contacts'));
  };

  return (
    <div style={{marginTop:10}}>
      <h3>📤 Import / Export</h3>
      <button onClick={handleExportCSV} style={{marginRight:8}}>⬇️ Export CSV</button>
      <button onClick={handleExportXLSX} style={{marginRight:8}}>📊 Export XLSX</button>
      <input type="file" accept=".csv,.xls,.xlsx" onChange={(e)=>setFile(e.target.files[0])} style={{marginRight:8}} />
      <button onClick={handleImport}>⬆️ Import</button>
      {status && <div style={{marginTop:8}}>{status}</div>}
    </div>
  );
}
