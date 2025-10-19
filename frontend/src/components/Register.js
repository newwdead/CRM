import React, { useState } from 'react';

export default function Register({ lang = 'ru', onRegister, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  const t = lang === 'ru' ? {
    title: 'Регистрация',
    username: 'Имя пользователя',
    usernamePlaceholder: 'username',
    usernameHelp: 'Только буквы, цифры, _ и - (минимум 3 символа)',
    email: 'Email',
    emailPlaceholder: 'user@example.com',
    password: 'Пароль',
    passwordPlaceholder: '••••••',
    passwordHelp: 'Минимум 6 символов',
    confirmPassword: 'Подтвердите пароль',
    fullName: 'Полное имя (опционально)',
    fullNamePlaceholder: 'Иван Иванов',
    register: 'Зарегистрироваться',
    registering: 'Регистрация...',
    haveAccount: 'Уже есть аккаунт?',
    login: 'Войти',
    error: 'Ошибка регистрации',
    passwordMismatch: 'Пароли не совпадают',
    invalidUsername: 'Недопустимое имя пользователя',
    invalidEmail: 'Недопустимый email',
    shortPassword: 'Пароль должен быть минимум 6 символов',
    usernameExists: 'Имя пользователя уже занято',
    emailExists: 'Email уже зарегистрирован',
    networkError: 'Ошибка сети. Проверьте подключение.',
  } : {
    title: 'Register',
    username: 'Username',
    usernamePlaceholder: 'username',
    usernameHelp: 'Letters, numbers, _ and - only (min 3 chars)',
    email: 'Email',
    emailPlaceholder: 'user@example.com',
    password: 'Password',
    passwordPlaceholder: '••••••',
    passwordHelp: 'Minimum 6 characters',
    confirmPassword: 'Confirm Password',
    fullName: 'Full Name (optional)',
    fullNamePlaceholder: 'John Doe',
    register: 'Register',
    registering: 'Registering...',
    haveAccount: 'Already have an account?',
    login: 'Login',
    error: 'Registration Error',
    passwordMismatch: 'Passwords do not match',
    invalidUsername: 'Invalid username',
    invalidEmail: 'Invalid email',
    shortPassword: 'Password must be at least 6 characters',
    usernameExists: 'Username already exists',
    emailExists: 'Email already registered',
    networkError: 'Network error. Check your connection.',
  };

  const validateForm = () => {
    const errors = {};

    // Username validation
    if (!formData.username) {
      errors.username = t.invalidUsername;
    } else if (formData.username.length < 3) {
      errors.username = t.usernameHelp;
    }

    // Email validation
    if (!formData.email) {
      errors.email = t.invalidEmail;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = t.invalidEmail;
    }

    // Password validation
    if (!formData.password) {
      errors.password = t.shortPassword;
    } else if (formData.password.length < 6) {
      errors.password = t.shortPassword;
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = t.passwordMismatch;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle specific errors
        if (errorData.detail) {
          if (errorData.detail.includes('Username') || errorData.detail.includes('username')) {
            throw new Error(t.usernameExists);
          } else if (errorData.detail.includes('Email') || errorData.detail.includes('email')) {
            throw new Error(t.emailExists);
          }
          throw new Error(errorData.detail);
        }
        
        throw new Error('Registration failed');
      }

      const userData = await response.json();
      
      // Auto-login after registration
      const formDataLogin = new FormData();
      formDataLogin.append('username', formData.username);
      formDataLogin.append('password', formData.password);

      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        body: formDataLogin,
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        localStorage.setItem('access_token', loginData.access_token);
        localStorage.setItem('user', JSON.stringify(userData));
        
        if (onRegister) {
          onRegister(userData, loginData.access_token);
        }
      } else {
        // Registration successful but auto-login failed, switch to login
        if (onSwitchToLogin) {
          onSwitchToLogin();
        }
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message || t.networkError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.stopPropagation()}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <h2 style={{ marginTop: 0, textAlign: 'center' }}>📝 {t.title}</h2>

        {error && (
          <div className="alert danger" style={{ marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Username */}
          <div className="form-group">
            <label>{t.username}</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder={t.usernamePlaceholder}
              required
              autoFocus
              disabled={loading}
            />
            {validationErrors.username ? (
              <div style={{ color: 'var(--danger-color)', fontSize: '12px', marginTop: '4px' }}>
                {validationErrors.username}
              </div>
            ) : (
              <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
                {t.usernameHelp}
              </div>
            )}
          </div>

          {/* Email */}
          <div className="form-group">
            <label>{t.email}</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder={t.emailPlaceholder}
              required
              disabled={loading}
            />
            {validationErrors.email && (
              <div style={{ color: 'var(--danger-color)', fontSize: '12px', marginTop: '4px' }}>
                {validationErrors.email}
              </div>
            )}
          </div>

          {/* Password */}
          <div className="form-group">
            <label>{t.password}</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder={t.passwordPlaceholder}
              required
              disabled={loading}
            />
            {validationErrors.password ? (
              <div style={{ color: 'var(--danger-color)', fontSize: '12px', marginTop: '4px' }}>
                {validationErrors.password}
              </div>
            ) : (
              <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
                {t.passwordHelp}
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div className="form-group">
            <label>{t.confirmPassword}</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder={t.passwordPlaceholder}
              required
              disabled={loading}
            />
            {validationErrors.confirmPassword && (
              <div style={{ color: 'var(--danger-color)', fontSize: '12px', marginTop: '4px' }}>
                {validationErrors.confirmPassword}
              </div>
            )}
          </div>

          {/* Full Name */}
          <div className="form-group">
            <label>{t.fullName}</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder={t.fullNamePlaceholder}
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
                {t.registering}
              </>
            ) : (
              t.register
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
            {t.haveAccount}{' '}
          </span>
          <button
            onClick={onSwitchToLogin}
            className="secondary"
            style={{ padding: '4px 12px', fontSize: '14px' }}
            disabled={loading}
          >
            {t.login}
          </button>
        </div>
      </div>
    </div>
  );
}

