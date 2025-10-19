import React, { useState } from 'react';
import '../index.css';

function LoginPage({ onLoginSuccess }) {
  const [showRegister, setShowRegister] = useState(false);
  
  // Login state
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  
  // Register state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [registerError, setRegisterError] = useState('');
  const [registerSuccess, setRegisterSuccess] = useState('');
  const [registerLoading, setRegisterLoading] = useState(false);

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', loginData.username);
      formData.append('password', loginData.password);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        // Check for specific error messages
        if (response.status === 403) {
          setLoginError('⏳ ' + data.detail);
        } else {
          setLoginError(data.detail || 'Login failed');
        }
        setLoginLoading(false);
        return;
      }

      // Save token and user info
      localStorage.setItem('token', data.access_token);
      
      // Fetch user info
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        localStorage.setItem('user', JSON.stringify(userData));
        onLoginSuccess(userData);
      } else {
        setLoginError('Failed to fetch user information');
        setLoginLoading(false);
      }
    } catch (error) {
      setLoginError('Network error: ' + error.message);
      setLoginLoading(false);
    }
  };

  // Handle Register
  const handleRegister = async (e) => {
    e.preventDefault();
    setRegisterError('');
    setRegisterSuccess('');
    setRegisterLoading(true);

    // Validation
    if (registerData.password !== registerData.confirmPassword) {
      setRegisterError('Passwords do not match');
      setRegisterLoading(false);
      return;
    }

    if (registerData.password.length < 6) {
      setRegisterError('Password must be at least 6 characters');
      setRegisterLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: registerData.username,
          email: registerData.email,
          password: registerData.password,
          full_name: registerData.full_name || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setRegisterError(data.detail || 'Registration failed');
        setRegisterLoading(false);
        return;
      }

      // Registration successful
      setRegisterSuccess('✅ Registration successful! Your account is awaiting administrator approval. You will be notified once approved.');
      setRegisterData({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        full_name: ''
      });
      
      // Switch to login after 5 seconds
      setTimeout(() => {
        setShowRegister(false);
        setRegisterSuccess('');
      }, 5000);
      
      setRegisterLoading(false);
    } catch (error) {
      setRegisterError('Network error: ' + error.message);
      setRegisterLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <div className="login-logo">
            <span className="logo-icon">💼</span>
            <h1>ibbase</h1>
          </div>
          <p className="login-subtitle">Business Card Management System</p>
        </div>

        <div className="login-tabs">
          <button
            className={`login-tab ${!showRegister ? 'active' : ''}`}
            onClick={() => {
              setShowRegister(false);
              setLoginError('');
              setRegisterError('');
              setRegisterSuccess('');
            }}
          >
            Login
          </button>
          <button
            className={`login-tab ${showRegister ? 'active' : ''}`}
            onClick={() => {
              setShowRegister(true);
              setLoginError('');
              setRegisterError('');
              setRegisterSuccess('');
            }}
          >
            Register
          </button>
        </div>

        {!showRegister ? (
          // Login Form
          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label htmlFor="login-username">Username or Email</label>
              <input
                type="text"
                id="login-username"
                value={loginData.username}
                onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                placeholder="Enter your username or email"
                required
                autoFocus
                disabled={loginLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                type="password"
                id="login-password"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                placeholder="Enter your password"
                required
                disabled={loginLoading}
              />
            </div>

            {loginError && (
              <div className="alert alert-error">
                {loginError}
              </div>
            )}

            <button type="submit" className="btn-login" disabled={loginLoading}>
              {loginLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        ) : (
          // Register Form
          <form onSubmit={handleRegister} className="login-form">
            <div className="form-group">
              <label htmlFor="register-username">Username *</label>
              <input
                type="text"
                id="register-username"
                value={registerData.username}
                onChange={(e) => setRegisterData({ ...registerData, username: e.target.value })}
                placeholder="Choose a username"
                required
                autoFocus
                disabled={registerLoading}
                minLength="3"
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-email">Email *</label>
              <input
                type="email"
                id="register-email"
                value={registerData.email}
                onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                placeholder="your.email@example.com"
                required
                disabled={registerLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-fullname">Full Name</label>
              <input
                type="text"
                id="register-fullname"
                value={registerData.full_name}
                onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
                placeholder="John Doe (optional)"
                disabled={registerLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-password">Password *</label>
              <input
                type="password"
                id="register-password"
                value={registerData.password}
                onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                placeholder="At least 6 characters"
                required
                disabled={registerLoading}
                minLength="6"
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-confirm">Confirm Password *</label>
              <input
                type="password"
                id="register-confirm"
                value={registerData.confirmPassword}
                onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                placeholder="Re-enter your password"
                required
                disabled={registerLoading}
                minLength="6"
              />
            </div>

            {registerError && (
              <div className="alert alert-error">
                {registerError}
              </div>
            )}

            {registerSuccess && (
              <div className="alert alert-success">
                {registerSuccess}
              </div>
            )}

            <button type="submit" className="btn-login" disabled={registerLoading || registerSuccess}>
              {registerLoading ? 'Registering...' : 'Register'}
            </button>

            <div className="register-info">
              <small>
                ⚠️ Your account will require administrator approval before you can log in.
              </small>
            </div>
          </form>
        )}

        <div className="login-footer">
          <p>© 2025 ibbase v1.9 - Business Card Management System</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;

