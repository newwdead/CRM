import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TwoFactorSetup from './TwoFactorSetup';

/**
 * TwoFactorSettings Component
 * 
 * Manage 2FA settings in user profile:
 * - View 2FA status
 * - Enable 2FA (setup wizard)
 * - Disable 2FA
 * - Regenerate backup codes
 */
const TwoFactorSettings = () => {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');
  const [showSetup, setShowSetup] = useState(false);
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);
  const [showRegenerateCodes, setShowRegenerateCodes] = useState(false);
  const [newBackupCodes, setNewBackupCodes] = useState([]);

  const API_BASE = '/api';

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${API_BASE}/auth/2fa/status`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch 2FA status:', err);
      setError('Failed to load 2FA settings. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE}/auth/2fa/disable`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setShowDisableConfirm(false);
      await fetchStatus();
    } catch (err) {
      console.error('Failed to disable 2FA:', err);
      setError(err.response?.data?.detail || 'Failed to disable 2FA. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateBackupCodes = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${API_BASE}/auth/2fa/regenerate-backup-codes`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setNewBackupCodes(response.data.backup_codes);
      setShowRegenerateCodes(true);
    } catch (err) {
      console.error('Failed to regenerate backup codes:', err);
      setError(err.response?.data?.detail || 'Failed to regenerate backup codes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadBackupCodes = () => {
    const content = `BACKUP CODES FOR TWO-FACTOR AUTHENTICATION
Regenerated: ${new Date().toLocaleString()}

IMPORTANT: Save these codes in a secure location.
Each code can only be used once.
Your old backup codes are now invalid.

${newBackupCodes.join('\n')}

If you lose access to your authenticator app, you can use these codes to log in.
`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `2fa-backup-codes-regenerated-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Show Setup Wizard
  if (showSetup) {
    return (
      <TwoFactorSetup
        onComplete={() => {
          setShowSetup(false);
          fetchStatus();
        }}
        onCancel={() => setShowSetup(false)}
      />
    );
  }

  // Show Regenerate Backup Codes Modal
  if (showRegenerateCodes) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          New Backup Codes Generated
        </h2>

        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-yellow-900 mb-1">
              ⚠️ Your old backup codes are now invalid
            </p>
            <p className="text-sm text-yellow-800">
              Make sure to save these new codes. Your previous codes will no longer work.
            </p>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Your New Backup Codes:</h3>
            <div className="grid grid-cols-2 gap-3">
              {newBackupCodes.map((code, index) => (
                <div
                  key={index}
                  className="bg-white px-4 py-3 rounded border border-gray-300 font-mono text-center text-sm"
                >
                  {code}
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={handleDownloadBackupCodes}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Backup Codes
            </button>

            <button
              onClick={() => setShowRegenerateCodes(false)}
              className="w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show Disable Confirmation Modal
  if (showDisableConfirm) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Disable Two-Factor Authentication?
        </h2>

        <div className="space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-red-900 mb-2">
              ⚠️ Warning: This will reduce your account security
            </p>
            <p className="text-sm text-red-800">
              Disabling 2FA will make your account less secure. You will only need your password to log in.
            </p>
          </div>

          <p className="text-gray-700">
            Are you sure you want to disable two-factor authentication?
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => setShowDisableConfirm(false)}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              onClick={handleDisable2FA}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Disabling...' : 'Yes, Disable 2FA'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main Settings View
  if (loading && !status) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading 2FA settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Two-Factor Authentication
      </h2>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Current Status */}
        <div className="border border-gray-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-800">
                  Status
                </h3>
                {status?.is_enabled ? (
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                    Enabled
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-gray-100 text-gray-800 text-sm font-medium rounded-full">
                    Disabled
                  </span>
                )}
              </div>
              
              {status?.is_enabled ? (
                <p className="text-gray-600 text-sm">
                  Your account is protected with two-factor authentication.
                  {status.created_at && (
                    <span className="block mt-1 text-gray-500">
                      Enabled since: {new Date(status.created_at).toLocaleDateString()}
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-gray-600 text-sm">
                  Add an extra layer of security to your account by enabling two-factor authentication.
                </p>
              )}
            </div>

            <div className="ml-4">
              {status?.is_enabled ? (
                <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              ) : (
                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        {status?.is_enabled ? (
          <div className="space-y-4">
            {/* Backup Codes */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Backup Codes
              </h3>
              <p className="text-gray-600 text-sm mb-4">
                Backup codes can be used to access your account if you lose access to your authenticator app.
                {status.backup_codes_remaining !== undefined && (
                  <span className="block mt-1 font-medium text-gray-700">
                    Remaining codes: {status.backup_codes_remaining}
                  </span>
                )}
              </p>
              <button
                onClick={handleRegenerateBackupCodes}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={loading}
              >
                Regenerate Backup Codes
              </button>
            </div>

            {/* Disable 2FA */}
            <div className="border border-red-200 rounded-lg p-6 bg-red-50">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Disable Two-Factor Authentication
              </h3>
              <p className="text-gray-600 text-sm mb-4">
                Disabling 2FA will reduce the security of your account. Only do this if absolutely necessary.
              </p>
              <button
                onClick={() => setShowDisableConfirm(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                disabled={loading}
              >
                Disable 2FA
              </button>
            </div>
          </div>
        ) : (
          <div className="border border-blue-200 rounded-lg p-6 bg-blue-50">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Enable Two-Factor Authentication
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Two-factor authentication adds an extra layer of security by requiring a code from your phone
              in addition to your password.
            </p>
            <ul className="text-sm text-gray-700 mb-4 space-y-1">
              <li>✓ Protects against password theft</li>
              <li>✓ Works with popular authenticator apps</li>
              <li>✓ Includes backup codes for account recovery</li>
            </ul>
            <button
              onClick={() => setShowSetup(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Enable 2FA
            </button>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-900 mb-2">
            💡 About Two-Factor Authentication
          </p>
          <p className="text-sm text-gray-700">
            Two-factor authentication (2FA) is a security feature that requires two forms of identification to access your account:
            something you know (your password) and something you have (your phone with an authenticator app).
          </p>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorSettings;

