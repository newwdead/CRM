import React, { useState, useEffect } from 'react';

/**
 * User Management Component
 * Manages users, pending approvals, and user permissions
 */
function UserManagement() {
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
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
  
  // Reset password state
  const [resettingPassword, setResettingPassword] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    fetchUsers();
    fetchPendingUsers();
  }, []);

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
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    
    setError('');
    setSuccess('');
    setLoading(true);
    
    try {
      const response = await fetch(`/api/auth/users/${resettingPassword.id}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ new_password: newPassword })
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message || `Password reset successfully for user: ${resettingPassword.username}`);
        setResettingPassword(null);
        setNewPassword('');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to reset password');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
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
    <div className="user-management">
      {/* Success/Error Messages */}
      {success && <div className="alert success">{success}</div>}
      {error && <div className="alert error">{error}</div>}

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
                        className="btn btn-warning btn-sm"
                        onClick={() => setResettingPassword(user)}
                        title="Reset password"
                      >
                        🔑
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
      
      {/* Reset Password Modal */}
      {resettingPassword && (
        <div className="modal-overlay" onClick={() => setResettingPassword(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🔑 Reset Password: {resettingPassword.username}</h3>
              <button className="btn-close" onClick={() => setResettingPassword(null)}>✕</button>
            </div>
            <form onSubmit={handleResetPassword}>
              <div className="form-group">
                <label>New Password (minimum 6 characters)</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  minLength={6}
                  required
                />
                <small style={{ color: '#666', fontSize: '0.85em', marginTop: '5px', display: 'block' }}>
                  User will be able to log in with this new password immediately.
                </small>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn" onClick={() => {
                  setResettingPassword(null);
                  setNewPassword('');
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-warning" disabled={loading}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserManagement;

