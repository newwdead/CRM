import React, { useState } from 'react';

/**
 * Login Component with 2FA Support
 * 
 * Flow:
 * 1. User enters username/password
 * 2. If 2FA enabled, show OTP input
 * 3. Verify OTP and complete login
 * 4. Option to use backup code
 */
export default function LoginWith2FA({ lang = 'ru', onLogin, onSwitchToRegister }) {
  // Form states
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);
  
  // Flow control
  const [step, setStep] = useState('credentials'); // 'credentials' | 'otp'
  const [tempToken, setTempToken] = useState(null);
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const t = lang === 'ru' ? {
    title: 'Вход в систему',
    username: 'Имя пользователя или Email',
    password: 'Пароль',
    login: 'Войти',
    logging: 'Вход...',
    noAccount: 'Нет аккаунта?',
    register: 'Зарегистрироваться',
    error: 'Ошибка входа',
    invalidCredentials: 'Неверное имя пользователя или пароль',
    networkError: 'Ошибка сети. Проверьте подключение.',
    defaultAdmin: 'По умолчанию: admin / admin123',
    
    // 2FA
    twoFactorTitle: 'Двухфакторная аутентификация',
    enterCode: 'Введите 6-значный код из вашего приложения:',
    enterBackupCode: 'Введите резервный код:',
    otpPlaceholder: '000000',
    backupCodePlaceholder: 'XXXX-XXXX-XXXX-XXXX',
    verify: 'Подтвердить',
    verifying: 'Проверка...',
    useBackupCode: 'Использовать резервный код',
    useAuthenticator: 'Использовать код из приложения',
    invalidOTP: 'Неверный код. Попробуйте снова.',
    backButton: 'Назад',
  } : {
    title: 'Login',
    username: 'Username or Email',
    password: 'Password',
    login: 'Login',
    logging: 'Logging in...',
    noAccount: 'No account?',
    register: 'Register',
    error: 'Login Error',
    invalidCredentials: 'Invalid username or password',
    networkError: 'Network error. Check your connection.',
    defaultAdmin: 'Default: admin / admin123',
    
    // 2FA
    twoFactorTitle: 'Two-Factor Authentication',
    enterCode: 'Enter the 6-digit code from your app:',
    enterBackupCode: 'Enter your backup code:',
    otpPlaceholder: '000000',
    backupCodePlaceholder: 'XXXX-XXXX-XXXX-XXXX',
    verify: 'Verify',
    verifying: 'Verifying...',
    useBackupCode: 'Use backup code',
    useAuthenticator: 'Use authenticator app',
    invalidOTP: 'Invalid code. Please try again.',
    backButton: 'Back',
  };

  // Step 1: Submit username/password
  const handleCredentialsSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(t.invalidCredentials);
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Check if 2FA is required
      if (data.require_2fa) {
        setTempToken(data.temp_token);
        setStep('otp');
      } else {
        // No 2FA, complete login
        await completeLogin(data.access_token);
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || t.networkError);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP/Backup Code
  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('/api/auth/2fa/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tempToken}`
        },
        body: JSON.stringify({ 
          token: otpCode,
          is_backup_code: useBackupCode
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(t.invalidOTP);
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Verification failed');
      }

      const data = await response.json();
      await completeLogin(data.access_token);
    } catch (err) {
      console.error('2FA verification error:', err);
      setError(err.message || t.networkError);
      setOtpCode('');
    } finally {
      setLoading(false);
    }
  };

  // Complete login flow
  const completeLogin = async (accessToken) => {
    try {
      // Save token
      localStorage.setItem('access_token', accessToken);
      
      // Fetch user info
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Call parent callback
        if (onLogin) {
          onLogin(userData, accessToken);
        }
      }
    } catch (err) {
      console.error('Failed to fetch user info:', err);
      setError('Login successful but failed to load user data');
    }
  };

  // Back to credentials
  const handleBack = () => {
    setStep('credentials');
    setOtpCode('');
    setTempToken(null);
    setError(null);
  };

  // Render Step 1: Credentials
  if (step === 'credentials') {
    return (
      <div className="modal-overlay" onClick={(e) => e.stopPropagation()}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
          <h2 style={{ marginTop: 0, textAlign: 'center' }}>🔐 {t.title}</h2>

          {error && (
            <div className="alert danger" style={{ marginBottom: '16px' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleCredentialsSubmit}>
            <div className="form-group">
              <label>{t.username}</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                autoFocus
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>{t.password}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                required
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="success"
              style={{ width: '100%', marginTop: '8px' }}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{
                    width: '16px',
                    height: '16px',
                    display: 'inline-block',
                    marginRight: '8px',
                    borderWidth: '2px'
                  }}></div>
                  {t.logging}
                </>
              ) : (
                t.login
              )}
            </button>
          </form>

          <div style={{
            textAlign: 'center',
            marginTop: '20px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-color)'
          }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              {t.noAccount}{' '}
            </span>
            <button
              onClick={onSwitchToRegister}
              className="secondary"
              style={{ padding: '4px 12px', fontSize: '14px' }}
              disabled={loading}
            >
              {t.register}
            </button>
          </div>

          <div className="alert info" style={{ marginTop: '16px', fontSize: '12px' }}>
            💡 {t.defaultAdmin}
          </div>
        </div>
      </div>
    );
  }

  // Render Step 2: OTP Verification
  if (step === 'otp') {
    return (
      <div className="modal-overlay" onClick={(e) => e.stopPropagation()}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
          <h2 style={{ marginTop: 0, textAlign: 'center' }}>🔒 {t.twoFactorTitle}</h2>

          {error && (
            <div className="alert danger" style={{ marginBottom: '16px' }}>
              {error}
            </div>
          )}

          <div className="alert info" style={{ marginBottom: '16px' }}>
            <strong>{username}</strong>
          </div>

          <form onSubmit={handleOTPSubmit}>
            <div className="form-group">
              <label>
                {useBackupCode ? t.enterBackupCode : t.enterCode}
              </label>
              <input
                type="text"
                value={otpCode}
                onChange={(e) => {
                  const value = e.target.value;
                  if (useBackupCode) {
                    // Allow alphanumeric for backup codes
                    setOtpCode(value.toUpperCase());
                  } else {
                    // Only digits for OTP
                    setOtpCode(value.replace(/\D/g, '').slice(0, 6));
                  }
                }}
                placeholder={useBackupCode ? t.backupCodePlaceholder : t.otpPlaceholder}
                maxLength={useBackupCode ? 20 : 6}
                className="text-center"
                style={{
                  fontSize: useBackupCode ? '16px' : '24px',
                  letterSpacing: useBackupCode ? '1px' : '8px',
                  fontFamily: 'monospace',
                  textAlign: 'center'
                }}
                required
                autoFocus
                disabled={loading}
                autoComplete="off"
              />
            </div>

            <button
              type="submit"
              disabled={loading || (!useBackupCode && otpCode.length !== 6) || (useBackupCode && !otpCode)}
              className="success"
              style={{ width: '100%', marginTop: '8px' }}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{
                    width: '16px',
                    height: '16px',
                    display: 'inline-block',
                    marginRight: '8px',
                    borderWidth: '2px'
                  }}></div>
                  {t.verifying}
                </>
              ) : (
                t.verify
              )}
            </button>
          </form>

          <div style={{ marginTop: '16px', textAlign: 'center' }}>
            <button
              onClick={() => {
                setUseBackupCode(!useBackupCode);
                setOtpCode('');
                setError(null);
              }}
              className="secondary"
              style={{ fontSize: '14px', padding: '6px 12px' }}
              disabled={loading}
            >
              {useBackupCode ? t.useAuthenticator : t.useBackupCode}
            </button>
          </div>

          <div style={{
            textAlign: 'center',
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-color)'
          }}>
            <button
              onClick={handleBack}
              className="secondary"
              style={{ fontSize: '14px', padding: '6px 12px' }}
              disabled={loading}
            >
              ← {t.backButton}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

