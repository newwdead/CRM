import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';

/**
 * Backup Management Component
 * Manages database backups - creation, listing, and deletion
 */
function BackupManagement() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
      // Use /api/ prefix for Nginx routing
      const response = await fetch('/api/backups', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'  // Disable caching
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
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
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
    }
  };

  return (
    <div className="backup-management">
      <div className="section-header">
        <h3>💾 Database Backups</h3>
        <button 
          onClick={handleCreateBackup}
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : '📦 Create Backup Now'}
        </button>
      </div>

      {/* Success/Error Messages */}
      {success && <div className="alert success">{success}</div>}
      {error && <div className="alert error">{error}</div>}

      {loading && <p>Loading backups...</p>}

      {backups.backups && backups.backups.length > 0 ? (
        <div>
          <div className="alert info" style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <strong>Total Backups:</strong> {backups.total_count}
              </div>
              <div>
                <strong>Total Size:</strong> {backups.total_size_human}
              </div>
              <div>
                <strong>Location:</strong> <code>{backups.backup_dir}</code>
              </div>
              <div>
                <strong>Retention:</strong> 30 days
              </div>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Created At</th>
                  <th>Size</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {backups.backups.map((backup, idx) => (
                  <tr key={idx}>
                    <td>
                      <code style={{ fontSize: '0.85em' }}>{backup.filename}</code>
                    </td>
                    <td>{backup.created_date} ({backup.created_relative})</td>
                    <td>{backup.size_mb} MB</td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => handleDeleteBackup(backup.filename)}
                        className="btn btn-danger btn-sm"
                        style={{ fontSize: '0.8em', padding: '4px 12px' }}
                      >
                        🗑️ Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="alert info" style={{ marginTop: '20px' }}>
            <strong>💡 Auto Backup:</strong> Automatic backups run daily at 3:00 AM. 
            Backups older than 30 days are automatically removed.
          </div>
        </div>
      ) : (
        <div className="alert warning">
          <p>No backups found. Click "Create Backup Now" to create your first backup.</p>
        </div>
      )}
    </div>
  );
}

export default BackupManagement;

