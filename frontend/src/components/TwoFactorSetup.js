import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * TwoFactorSetup Component
 * 
 * Step-by-step wizard for enabling 2FA:
 * 1. Generate QR code
 * 2. Scan with authenticator app
 * 3. Verify OTP code
 * 4. Save backup codes
 */
const TwoFactorSetup = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // 2FA Setup Data
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [secret, setSecret] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  
  // User Input
  const [otpCode, setOtpCode] = useState('');
  
  const API_BASE = '/api';

  // Step 1: Initialize 2FA Setup
  useEffect(() => {
    if (step === 1) {
      initializeSetup();
    }
  }, [step]);

  const initializeSetup = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${API_BASE}/auth/2fa/setup`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setQrCodeUrl(response.data.qr_code);
      setSecret(response.data.secret);
      setStep(2);
    } catch (err) {
      console.error('2FA setup initialization failed:', err);
      setError(err.response?.data?.detail || 'Failed to initialize 2FA setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP and Enable 2FA
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    
    if (!otpCode || otpCode.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${API_BASE}/auth/2fa/enable`,
        { token: otpCode },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setBackupCodes(response.data.backup_codes);
      setStep(3);
    } catch (err) {
      console.error('2FA verification failed:', err);
      setError(err.response?.data?.detail || 'Invalid verification code. Please try again.');
      setOtpCode('');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Download Backup Codes
  const handleDownloadBackupCodes = () => {
    const content = `BACKUP CODES FOR TWO-FACTOR AUTHENTICATION
Generated: ${new Date().toLocaleString()}

IMPORTANT: Save these codes in a secure location.
Each code can only be used once.

${backupCodes.join('\n')}

If you lose access to your authenticator app, you can use these codes to log in.
`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `2fa-backup-codes-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  // Render Step 1: Loading
  if (step === 1) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Setting Up Two-Factor Authentication
          </h2>
          <p className="text-gray-600">Please wait...</p>
        </div>
      </div>
    );
  }

  // Render Step 2: QR Code & Verification
  if (step === 2) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Enable Two-Factor Authentication
          </h2>
          <p className="text-gray-600">
            Step 2 of 3: Scan QR code with your authenticator app
          </p>
        </div>

        <div className="space-y-6">
          {/* QR Code */}
          <div className="bg-gray-50 p-6 rounded-lg text-center">
            <p className="text-sm text-gray-700 mb-4 font-medium">
              Scan this QR code with your authenticator app:
            </p>
            {qrCodeUrl ? (
              <img 
                src={qrCodeUrl} 
                alt="2FA QR Code" 
                className="mx-auto border-4 border-white shadow-lg rounded-lg"
                style={{ maxWidth: '300px' }}
              />
            ) : (
              <div className="w-64 h-64 mx-auto bg-gray-200 rounded-lg flex items-center justify-center">
                <span className="text-gray-500">Loading QR Code...</span>
              </div>
            )}
          </div>

          {/* Manual Entry */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-900 mb-2">
              Can't scan the QR code?
            </p>
            <p className="text-xs text-blue-800 mb-2">
              Enter this secret key manually in your authenticator app:
            </p>
            <div className="bg-white p-3 rounded border border-blue-300 font-mono text-sm text-center break-all">
              {secret}
            </div>
          </div>

          {/* Supported Apps */}
          <div className="text-sm text-gray-600">
            <p className="font-medium mb-2">Recommended authenticator apps:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-700">
              <li>Google Authenticator (iOS, Android)</li>
              <li>Microsoft Authenticator (iOS, Android)</li>
              <li>Authy (iOS, Android, Desktop)</li>
              <li>1Password (Cross-platform)</li>
            </ul>
          </div>

          {/* Verification Form */}
          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter the 6-digit code from your authenticator app:
              </label>
              <input
                type="text"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="000000"
                maxLength="6"
                autoComplete="off"
                disabled={loading}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                <p className="font-medium">Error:</p>
                <p>{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleCancel}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading || otpCode.length !== 6}
              >
                {loading ? 'Verifying...' : 'Verify & Enable'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Render Step 3: Backup Codes
  if (step === 3) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="mb-6">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">
            Two-Factor Authentication Enabled!
          </h2>
          <p className="text-gray-600 text-center">
            Step 3 of 3: Save your backup codes
          </p>
        </div>

        <div className="space-y-6">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-semibold text-yellow-900 mb-1">
                  IMPORTANT: Save these backup codes now!
                </p>
                <p className="text-sm text-yellow-800">
                  If you lose access to your authenticator app, these codes are the only way to recover your account.
                  Each code can only be used once.
                </p>
              </div>
            </div>
          </div>

          {/* Backup Codes */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Your Backup Codes:</h3>
            <div className="grid grid-cols-2 gap-3">
              {backupCodes.map((code, index) => (
                <div
                  key={index}
                  className="bg-white px-4 py-3 rounded border border-gray-300 font-mono text-center text-sm"
                >
                  {code}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
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
              onClick={handleComplete}
              className="w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              I've Saved My Codes - Continue
            </button>
          </div>

          {/* Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-900 mb-2">
              💡 Security Tips:
            </p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Store backup codes in a password manager</li>
              <li>• Keep a printed copy in a secure location</li>
              <li>• Never share your codes with anyone</li>
              <li>• Generate new codes if you suspect they're compromised</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default TwoFactorSetup;

