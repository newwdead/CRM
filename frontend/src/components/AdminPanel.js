import React, { useState, useEffect } from 'react';

function AdminPanel({ t, lang }) {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [systemSettings, setSystemSettings] = useState(null);
  const [editableSettings, setEditableSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Editing user state
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    email: '',
    full_name: '',
    password: ''
  });

  // Editing settings state
  const [editingSettings, setEditingSettings] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    tesseract_langs: '',
    parsio_api_key: '',
    google_vision_api_key: '',
    telegram_bot_token: '',
    telegram_webhook_url: '',
    token_expire_minutes: 10080,
    require_admin_approval: true
  });

  // Backups state
  const [backups, setBackups] = useState([]);
  const [backupsLoading, setBackupsLoading] = useState(false);

  // System resources state
  const [resources, setResources] = useState(null);

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
      fetchPendingUsers();
    } else if (activeTab === 'settings') {
      fetchSystemSettings();
      fetchEditableSettings();
    } else if (activeTab === 'backups') {
      fetchBackups();
    } else if (activeTab === 'resources') {
      fetchResources();
    }
  }, [activeTab]);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/auth/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      setError('Failed to fetch users');
    }
  };

  const fetchPendingUsers = async () => {
    try {
      const response = await fetch('/api/settings/pending-users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setPendingUsers(data);
      }
    } catch (error) {
      console.error('Failed to fetch pending users:', error);
    }
  };

  const fetchSystemSettings = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/settings/system', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSystemSettings(data);
      } else {
        setError('Failed to fetch system settings');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchEditableSettings = async () => {
    try {
      const response = await fetch('/api/settings/editable', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setEditableSettings(data);
        setSettingsForm({
          tesseract_langs: data.ocr.tesseract_langs || '',
          parsio_api_key: data.ocr.parsio_api_key || '',
          google_vision_api_key: data.ocr.google_vision_api_key || '',
          telegram_bot_token: data.telegram.bot_token || '',
          telegram_webhook_url: data.telegram.webhook_url || '',
          token_expire_minutes: data.auth.token_expire_minutes || 10080,
          require_admin_approval: data.auth.require_admin_approval !== false
        });
      }
    } catch (error) {
      console.error('Failed to fetch editable settings:', error);
    }
  };

  const handleUpdateSettings = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await fetch('/api/settings/editable', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ocr: {
            tesseract_langs: settingsForm.tesseract_langs,
            parsio_api_key: settingsForm.parsio_api_key,
            google_vision_api_key: settingsForm.google_vision_api_key
          },
          telegram: {
            bot_token: settingsForm.telegram_bot_token,
            webhook_url: settingsForm.telegram_webhook_url
          },
          auth: {
            token_expire_minutes: parseInt(settingsForm.token_expire_minutes),
            require_admin_approval: settingsForm.require_admin_approval
          }
        })
      });

      if (response.ok) {
        setSuccess(t?.settingsUpdated || 'Settings updated successfully!');
        setEditingSettings(false);
        fetchEditableSettings();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update settings');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleActivateUser = async (userId, isActive) => {
    setError('');
    setSuccess('');
    try {
      const response = await fetch(`/api/auth/users/${userId}/activate`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ is_active: isActive })
      });

      if (response.ok) {
        setSuccess(isActive ? 'User approved successfully!' : 'User deactivated');
        fetchUsers();
        fetchPendingUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update user');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  const handleToggleAdmin = async (userId, isAdmin) => {
    setError('');
    setSuccess('');
    try {
      const response = await fetch(`/api/auth/users/${userId}/admin`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ is_admin: isAdmin })
      });

      if (response.ok) {
        setSuccess('Admin status updated successfully!');
        fetchUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update admin status');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      const response = await fetch(`/api/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setSuccess('User deleted successfully!');
        fetchUsers();
        fetchPendingUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete user');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  const startEditUser = (user) => {
    setEditingUser(user);
    setEditForm({
      email: user.email || '',
      full_name: user.full_name || '',
      password: ''
    });
    setError('');
    setSuccess('');
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const updateData = {};
      if (editForm.email !== editingUser.email) updateData.email = editForm.email;
      if (editForm.full_name !== editingUser.full_name) updateData.full_name = editForm.full_name;
      if (editForm.password) updateData.password = editForm.password;

      const response = await fetch(`/api/auth/users/${editingUser.id}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        setSuccess('User updated successfully!');
        setEditingUser(null);
        fetchUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update user');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  // Backup functions
  const fetchBackups = async () => {
    setBackupsLoading(true);
    try {
      const response = await fetch('/api/backups/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBackups(data);
      }
    } catch (error) {
      console.error('Error fetching backups:', error);
    } finally {
      setBackupsLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    setError('');
    setSuccess('');
    setBackupsLoading(true);
    try {
      const response = await fetch('/api/backups/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
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
      setBackupsLoading(false);
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

  // Resources function
  const fetchResources = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/system/resources', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setResources(data);
      }
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h2>🛡️ Admin Panel</h2>
        <p>Manage users and system settings</p>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users Management
          {pendingUsers.length > 0 && (
            <span className="badge badge-warning">{pendingUsers.length}</span>
          )}
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ System Settings
        </button>
        <button
          className={`tab ${activeTab === 'backups' ? 'active' : ''}`}
          onClick={() => setActiveTab('backups')}
        >
          💾 Backups
        </button>
        <button
          className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => setActiveTab('resources')}
        >
          🔗 Resources
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {activeTab === 'users' && (
        <div className="tab-content">
          {/* Pending Users */}
          {pendingUsers.length > 0 && (
            <div className="section">
              <h3>⏳ Pending Approval ({pendingUsers.length})</h3>
              <div className="user-grid">
                {pendingUsers.map(user => (
                  <div key={user.id} className="user-card pending">
                    <div className="user-info">
                      <h4>{user.username}</h4>
                      <p>{user.email}</p>
                      {user.full_name && <p className="text-secondary">{user.full_name}</p>}
                      <p className="text-xs text-secondary">
                        Registered: {new Date(user.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="user-actions">
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleActivateUser(user.id, true)}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteUser(user.id, user.username)}
                      >
                        ✕ Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All Users */}
          <div className="section">
            <h3>👥 All Users ({users.length})</h3>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Full Name</th>
                    <th>Status</th>
                    <th>Role</th>
                    <th>Registered</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id}>
                      <td><strong>{user.username}</strong></td>
                      <td>{user.email}</td>
                      <td>{user.full_name || '-'}</td>
                      <td>
                        {user.is_active ? (
                          <span className="badge badge-success">Active</span>
                        ) : (
                          <span className="badge badge-warning">Inactive</span>
                        )}
                      </td>
                      <td>
                        {user.is_admin ? (
                          <span className="badge badge-primary">Admin</span>
                        ) : (
                          <span className="badge">User</span>
                        )}
                      </td>
                      <td className="text-xs">{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="btn-group">
                          <button
                            className="btn btn-sm"
                            onClick={() => startEditUser(user)}
                            title="Edit user"
                          >
                            ✏️
                          </button>
                          <button
                            className="btn btn-sm"
                            onClick={() => handleActivateUser(user.id, !user.is_active)}
                            title={user.is_active ? 'Deactivate' : 'Activate'}
                          >
                            {user.is_active ? '🔓' : '🔒'}
                          </button>
                          <button
                            className="btn btn-sm"
                            onClick={() => handleToggleAdmin(user.id, !user.is_admin)}
                            title={user.is_admin ? 'Remove admin' : 'Make admin'}
                          >
                            {user.is_admin ? '👤' : '🛡️'}
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            title="Delete user"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Edit User Modal */}
          {editingUser && (
            <div className="modal-overlay" onClick={() => setEditingUser(null)}>
              <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Edit User: {editingUser.username}</h3>
                  <button className="btn-close" onClick={() => setEditingUser(null)}>✕</button>
                </div>
                <form onSubmit={handleUpdateUser}>
                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={editForm.email}
                      onChange={e => setEditForm({...editForm, email: e.target.value})}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      value={editForm.full_name}
                      onChange={e => setEditForm({...editForm, full_name: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>New Password (leave blank to keep current)</label>
                    <input
                      type="password"
                      value={editForm.password}
                      onChange={e => setEditForm({...editForm, password: e.target.value})}
                      placeholder="Enter new password"
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn" onClick={() => setEditingUser(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary">
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="tab-content">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>{t?.systemSettings || 'System Settings'}</h3>
            <button 
              onClick={() => setEditingSettings(!editingSettings)}
              className="btn btn-primary"
            >
              {editingSettings ? (t?.cancel || 'Cancel') : (t?.editSettings || 'Edit Settings')}
            </button>
          </div>

          {editingSettings && editableSettings ? (
            <form onSubmit={handleUpdateSettings} className="settings-edit-form">
              <div className="section">
                <h4>{t?.ocrSettings || '🤖 OCR Settings'}</h4>
                <div className="form-group">
                  <label>{t?.tesseractLanguages || 'Tesseract Languages'}</label>
                  <input
                    type="text"
                    value={settingsForm.tesseract_langs}
                    onChange={(e) => setSettingsForm({...settingsForm, tesseract_langs: e.target.value})}
                    placeholder="rus+eng"
                  />
                  <small>Comma-separated language codes (e.g., rus+eng, eng+fra)</small>
                </div>
                <div className="form-group">
                  <label>{t?.parsioApiKey || 'Parsio API Key'}</label>
                  <input
                    type="password"
                    value={settingsForm.parsio_api_key}
                    onChange={(e) => setSettingsForm({...settingsForm, parsio_api_key: e.target.value})}
                    placeholder="Enter Parsio API key"
                  />
                </div>
                <div className="form-group">
                  <label>{t?.googleVisionApiKey || 'Google Vision API Key'}</label>
                  <input
                    type="password"
                    value={settingsForm.google_vision_api_key}
                    onChange={(e) => setSettingsForm({...settingsForm, google_vision_api_key: e.target.value})}
                    placeholder="Enter Google Vision API key"
                  />
                </div>
              </div>

              <div className="section">
                <h4>{t?.telegramIntegration || '📱 Telegram Integration'}</h4>
                <div className="form-group">
                  <label>{t?.telegramBotToken || 'Telegram Bot Token'}</label>
                  <input
                    type="password"
                    value={settingsForm.telegram_bot_token}
                    onChange={(e) => setSettingsForm({...settingsForm, telegram_bot_token: e.target.value})}
                    placeholder="Enter Telegram Bot token"
                  />
                </div>
                <div className="form-group">
                  <label>{t?.telegramWebhookUrl || 'Telegram Webhook URL'}</label>
                  <input
                    type="text"
                    value={settingsForm.telegram_webhook_url}
                    onChange={(e) => setSettingsForm({...settingsForm, telegram_webhook_url: e.target.value})}
                    placeholder="https://yourdomain.com/telegram/webhook"
                  />
                </div>
              </div>

              <div className="section">
                <h4>{t?.authentication || '🔐 Authentication'}</h4>
                <div className="form-group">
                  <label>{t?.tokenExpirationMinutes || 'Token Expiration (minutes)'}</label>
                  <input
                    type="number"
                    value={settingsForm.token_expire_minutes}
                    onChange={(e) => setSettingsForm({...settingsForm, token_expire_minutes: e.target.value})}
                    min="60"
                    max="43200"
                  />
                  <small>Default: 10080 minutes (7 days)</small>
                </div>
                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="checkbox"
                      checked={settingsForm.require_admin_approval}
                      onChange={(e) => setSettingsForm({...settingsForm, require_admin_approval: e.target.checked})}
                    />
                    {t?.requireAdminApproval || 'Require Admin Approval'}
                  </label>
                  <small>New users need admin approval to activate their accounts</small>
                </div>
              </div>

              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (t?.loading || 'Saving...') : (t?.save || 'Save Settings')}
              </button>
            </form>
          ) : loading ? (
            <p>{t?.loading || 'Loading system settings...'}</p>
          ) : systemSettings ? (
            <div className="settings-grid">
              <div className="settings-card">
                <h3>📊 Database Statistics</h3>
                <div className="stats">
                  <div className="stat-item">
                    <span className="stat-label">Total Contacts:</span>
                    <span className="stat-value">{systemSettings.database.total_contacts}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Users:</span>
                    <span className="stat-value">{systemSettings.database.total_users}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Pending Users:</span>
                    <span className="stat-value badge badge-warning">
                      {systemSettings.database.pending_users}
                    </span>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>🤖 OCR Settings</h3>
                <div className="stats">
                  <div className="stat-item">
                    <span className="stat-label">Default Provider:</span>
                    <span className="stat-value badge badge-primary">
                      {systemSettings.ocr.default_provider}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Tesseract Languages:</span>
                    <span className="stat-value">{systemSettings.ocr.tesseract_langs}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Available Providers:</span>
                    <span className="stat-value">
                      {systemSettings.ocr.available_providers.join(', ')}
                    </span>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>📱 Telegram Integration</h3>
                <div className="stats">
                  <div className="stat-item">
                    <span className="stat-label">Bot Token:</span>
                    <span className="stat-value">
                      {systemSettings.telegram.bot_token_configured ? (
                        <span className="badge badge-success">✓ Configured</span>
                      ) : (
                        <span className="badge badge-danger">✕ Not Configured</span>
                      )}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Webhook URL:</span>
                    <span className="stat-value text-xs">
                      {systemSettings.telegram.webhook_url || 'Not set'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>🔐 Authentication</h3>
                <div className="stats">
                  <div className="stat-item">
                    <span className="stat-label">Token Expiration:</span>
                    <span className="stat-value">
                      {systemSettings.authentication.token_expire_minutes} minutes
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Admin Approval Required:</span>
                    <span className="stat-value">
                      {systemSettings.authentication.require_admin_approval ? (
                        <span className="badge badge-success">✓ Yes</span>
                      ) : (
                        <span className="badge">No</span>
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>ℹ️ Application Info</h3>
                <div className="stats">
                  <div className="stat-item">
                    <span className="stat-label">Version:</span>
                    <span className="stat-value badge badge-primary">
                      {systemSettings.application.version}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Environment:</span>
                    <span className="stat-value">
                      {systemSettings.application.environment}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p>Failed to load system settings</p>
          )}
        </div>
      )}

      {/* Backups Tab */}
      {activeTab === 'backups' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>💾 Database Backups</h3>
            <button 
              onClick={handleCreateBackup}
              className="btn btn-primary"
              disabled={backupsLoading}
            >
              {backupsLoading ? 'Creating...' : '📦 Create Backup Now'}
            </button>
          </div>

          {backupsLoading && <p>Loading backups...</p>}

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
                        <td>{backup.created_at_human}</td>
                        <td>{backup.size_human}</td>
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
      )}

      {/* Resources Tab */}
      {activeTab === 'resources' && (
        <div className="tab-content">
          <h3>🔗 System Resources & Links</h3>
          <p style={{ marginBottom: '20px', color: '#666' }}>
            Quick access to all deployed services and monitoring dashboards
          </p>

          {loading && <p>Loading resources...</p>}

          {resources && resources.services ? (
            <div className="resources-grid" style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
              gap: '20px',
              marginTop: '20px'
            }}>
              {Object.entries(resources.services).map(([key, service]) => (
                <div key={key} className="resource-card" style={{
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: '#f9f9f9'
                }}>
                  <h4 style={{ marginTop: 0, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {service.name}
                  </h4>
                  <p style={{ color: '#666', fontSize: '0.9em', marginBottom: '15px' }}>
                    {service.description}
                  </p>
                  
                  {service.url ? (
                    <div style={{ marginBottom: '10px' }}>
                      <strong style={{ fontSize: '0.85em', color: '#666' }}>Production URL:</strong>
                      <div>
                        <a 
                          href={service.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn btn-primary btn-sm"
                          style={{ marginTop: '5px', display: 'inline-block' }}
                        >
                          🌐 Open {service.name}
                        </a>
                      </div>
                    </div>
                  ) : (
                    <div style={{ marginBottom: '10px' }}>
                      <span className="badge badge-secondary" style={{ fontSize: '0.8em' }}>
                        Internal Only
                      </span>
                    </div>
                  )}

                  <div>
                    <strong style={{ fontSize: '0.85em', color: '#666' }}>Local URL:</strong>
                    <div>
                      <code style={{ 
                        display: 'block', 
                        padding: '8px', 
                        backgroundColor: '#fff', 
                        borderRadius: '4px',
                        fontSize: '0.85em',
                        marginTop: '5px',
                        border: '1px solid #ddd'
                      }}>
                        {service.local_url}
                      </code>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>Failed to load resources</p>
          )}

          {resources && resources.environment && (
            <div className="alert info" style={{ marginTop: '30px' }}>
              <h4 style={{ marginTop: 0 }}>🌍 Environment Info</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                <div>
                  <strong>Domain:</strong> <code>{resources.environment.domain}</code>
                </div>
                <div>
                  <strong>Protocol:</strong> <code>{resources.environment.protocol}</code>
                </div>
                <div>
                  <strong>Server:</strong> <code>{resources.environment.server_host}</code>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AdminPanel;

