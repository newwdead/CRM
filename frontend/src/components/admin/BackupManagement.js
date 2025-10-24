import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import toast from 'react-hot-toast';

/**
 * Backup Management Component
 * Manages database backups - creation, listing, deletion, and configuration
 * Combined functionality from Admin Panel → Backups + System Settings → Backup
 */
function BackupManagement() {
  const [backups, setBackups] = useState({ backups: [], total: 0, total_size_human: '0 MB', backup_dir: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [backupConfig, setBackupConfig] = useState(null);
  const [editingConfig, setEditingConfig] = useState(false);
  const [configForm, setConfigForm] = useState({});

  useEffect(() => {
    fetchBackups();
    fetchBackupConfig();
  }, []);

  const fetchBackupConfig = async () => {
    try {
      const response = await fetch('/api/settings/integrations/backup', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBackupConfig(data);
        setConfigForm(data.config || {});
      }
    } catch (error) {
      logger.error('Error fetching backup config:', error);
    }
  };

  const toggleBackupIntegration = async () => {
    try {
      const response = await fetch('/api/settings/integrations/backup/toggle', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        toast.success(backupConfig.enabled ? 'Backup disabled' : 'Backup enabled');
        fetchBackupConfig();
      }
    } catch (error) {
      toast.error('Failed to toggle backup');
      logger.error('Error toggling backup:', error);
    }
  };

  const saveBackupConfig = async () => {
    try {
      const response = await fetch('/api/settings/integrations/backup/config', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config: configForm })
      });
      if (response.ok) {
        toast.success('Configuration saved');
        setEditingConfig(false);
        fetchBackupConfig();
      } else {
        toast.error('Failed to save configuration');
      }
    } catch (error) {
      toast.error('Failed to save configuration');
      logger.error('Error saving config:', error);
    }
  };

  const testBackupConnection = async () => {
    try {
      const response = await fetch('/api/settings/integrations/backup/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      });
      if (response.ok) {
        toast.success('Backup system test successful');
      } else {
        toast.error('Backup system test failed');
      }
    } catch (error) {
      toast.error('Failed to test backup');
      logger.error('Error testing backup:', error);
    }
  };

  const fetchBackups = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/backups', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'
      });
      if (response.ok) {
        const data = await response.json();
        setBackups(data);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || 'Failed to fetch backups');
        logger.error('Failed to fetch backups:', response.status, errorData);
      }
    } catch (error) {
      setError('Network error: Failed to connect to server');
      logger.error('Error fetching backups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      const response = await fetch('/api/backups/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'
      });
      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message || 'Backup created successfully!');
        fetchBackups();
        setTimeout(() => setSuccess(''), 5000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create backup');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBackup = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete backup ${filename}?`)) {
      return;
    }
    
    setError('');
    setSuccess('');
    try {
      const response = await fetch(`/api/backups/${filename}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'
      });
      if (response.ok) {
        setSuccess(`Backup ${filename} deleted successfully!`);
        fetchBackups();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete backup');
      }
    } catch (error) {
      setError('Network error');
      logger.error('Error deleting backup:', error);
    }
  };

  return (
    <div className="backup-management" style={{ padding: '20px', backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', color: '#333' }}>💾 Backup & Recovery</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
          Manage database backups, configure automatic backup schedule, and recovery options
        </p>
      </div>

      {/* Backup Configuration Section */}
      {backupConfig && (
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          border: `2px solid ${backupConfig.enabled ? '#28a745' : '#6c757d'}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
            <div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#333' }}>
                ⚙️ Automatic Backup Configuration
              </h3>
              <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
                Configure automatic backup schedule and retention policy
              </p>
            </div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              backgroundColor: backupConfig.enabled ? '#28a745' : '#6c757d',
              color: '#fff',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600'
            }}>
              {backupConfig.enabled ? '✅ Enabled' : '⏸️ Disabled'}
            </div>
          </div>

          {editingConfig ? (
            <div style={{ marginTop: '16px' }}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600' }}>
                  Backup Schedule (cron)
                </label>
                <input
                  type="text"
                  value={configForm.schedule || ''}
                  onChange={(e) => setConfigForm({ ...configForm, schedule: e.target.value })}
                  placeholder="0 2 * * * (daily at 2 AM)"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e1e4e8',
                    borderRadius: '6px',
                    fontSize: '13px'
                  }}
                />
              </div>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '13px', fontWeight: '600' }}>
                  Retention Days
                </label>
                <input
                  type="number"
                  value={configForm.retention_days || 30}
                  onChange={(e) => setConfigForm({ ...configForm, retention_days: parseInt(e.target.value) })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e1e4e8',
                    borderRadius: '6px',
                    fontSize: '13px'
                  }}
                />
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                <button
                  onClick={saveBackupConfig}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#28a745',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600'
                  }}
                >
                  💾 Save
                </button>
                <button
                  onClick={() => { setEditingConfig(false); setConfigForm(backupConfig.config || {}); }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#6c757d',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600'
                  }}
                >
                  ❌ Cancel
                </button>
              </div>
            </div>
          ) : (
            <div>
              {backupConfig.config_summary && (
                <div style={{
                  padding: '12px',
                  backgroundColor: '#f6f8fa',
                  borderRadius: '6px',
                  fontSize: '13px',
                  color: '#586069',
                  marginBottom: '16px'
                }}>
                  {Object.entries(backupConfig.config_summary).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '4px' }}>
                      <strong>{key}:</strong> {String(value)}
                    </div>
                  ))}
                </div>
              )}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  onClick={toggleBackupIntegration}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: backupConfig.enabled ? '#ffc107' : '#28a745',
                    color: backupConfig.enabled ? '#000' : '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600'
                  }}
                >
                  {backupConfig.enabled ? '⏸️ Disable' : '▶️ Enable'}
                </button>
                {backupConfig.enabled && (
                  <>
                    <button
                      onClick={testBackupConnection}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#0366d6',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      🔍 Test System
                    </button>
                    <button
                      onClick={() => setEditingConfig(true)}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#6c757d',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}
                    >
                      ⚙️ Configure
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Backups Section */}
      <div style={{
        backgroundColor: '#fff',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#333' }}>📦 Manual Backups</h3>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              Create backups manually or manage existing backup files
            </p>
          </div>
          <button 
            onClick={handleCreateBackup}
            className="btn btn-primary"
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: loading ? '#ccc' : '#0366d6',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            {loading ? '⏳ Creating...' : '📦 Create Backup Now'}
          </button>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '6px',
            color: '#155724'
          }}>
            {success}
          </div>
        )}
        {error && (
          <div style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '6px',
            color: '#721c24'
          }}>
            {error}
          </div>
        )}

        {loading && <p style={{ textAlign: 'center', color: '#666' }}>Loading backups...</p>}

        {backups.backups && backups.backups.length > 0 ? (
          <div>
            <div style={{
              padding: '12px',
              marginBottom: '20px',
              backgroundColor: '#e7f3ff',
              border: '1px solid #b3d9ff',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#004085'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <strong>Total Backups:</strong> {backups.total}
                </div>
                <div>
                  <strong>Total Size:</strong> {backups.total_size_human}
                </div>
                <div>
                  <strong>Location:</strong> <code>{backups.backup_dir}</code>
                </div>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f6f8fa', borderBottom: '2px solid #e1e4e8' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#333' }}>Filename</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#333' }}>Created At</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#333' }}>Size</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontSize: '13px', fontWeight: '600', color: '#333' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {backups.backups.map((backup, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e1e4e8' }}>
                      <td style={{ padding: '12px', fontSize: '13px' }}>
                        <code style={{ fontSize: '0.9em', backgroundColor: '#f6f8fa', padding: '2px 6px', borderRadius: '3px' }}>
                          {backup.filename}
                        </code>
                      </td>
                      <td style={{ padding: '12px', fontSize: '13px', color: '#586069' }}>
                        {backup.created_date} 
                        <span style={{ marginLeft: '8px', color: '#6a737d', fontSize: '0.9em' }}>
                          ({backup.created_relative})
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontSize: '13px', color: '#586069' }}>
                        {backup.size_mb} MB
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <button
                          onClick={() => handleDeleteBackup(backup.filename)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#dc3545',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}
                        >
                          🗑️ Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          !loading && (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              backgroundColor: '#fff3cd',
              border: '1px solid #ffeeba',
              borderRadius: '6px',
              color: '#856404'
            }}>
              <p style={{ margin: 0 }}>No backups found. Click "Create Backup Now" to create your first backup.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}

export default BackupManagement;
