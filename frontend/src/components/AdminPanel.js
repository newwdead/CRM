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

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
      fetchPendingUsers();
    } else if (activeTab === 'settings') {
      fetchSystemSettings();
      fetchEditableSettings();
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
    </div>
  );
}

export default AdminPanel;

