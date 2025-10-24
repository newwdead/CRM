import React, { useState } from 'react';
import { setTokens } from '../utils/tokenManager';

export default function Login({ lang = 'ru', onLogin, onSwitchToRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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
    defaultAdmin: 'По умолчанию: admin / admin',
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
    defaultAdmin: 'Default: admin / admin',
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Form data for OAuth2
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
      
      // Save tokens using token manager (with auto-refresh)
      if (data.refresh_token) {
        setTokens(data.access_token, data.refresh_token, data.expires_in || 900);
      } else {
        // Fallback for old token format (no refresh token)
        localStorage.setItem('access_token', data.access_token);
      }
      
      // Fetch user info
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Call parent callback
        if (onLogin) {
          onLogin(userData, data.access_token);
        }
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || t.networkError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.stopPropagation()}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
        <h2 style={{ marginTop: 0, textAlign: 'center' }}>🔐 {t.title}</h2>

        {error && (
          <div className="alert danger" style={{ marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
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

