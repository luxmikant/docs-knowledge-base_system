import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/auth.css';

export default function AuthPage() {
  const { isAuthenticated, login, signup, loading } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' or 'signup'

  // Login form state
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Signup form state
  const [signupUsername, setSignupUsername] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [signupRole, setSignupRole] = useState('user');
  const [adminSignupCode, setAdminSignupCode] = useState('');
  const [signupError, setSignupError] = useState('');
  const [usernameCheckMsg, setUsernameCheckMsg] = useState('');
  const [emailCheckMsg, setEmailCheckMsg] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/tasks" replace />;
  }

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');

    if (!loginUsername || !loginPassword) {
      setLoginError('Username and password are required');
      return;
    }

    const result = await login(loginUsername, loginPassword);
    if (!result.ok) {
      setLoginError(result.message);
    }
  };

  // Signup handler
  const handleSignup = async (e) => {
    e.preventDefault();
    setSignupError('');

    // Validation
    if (!signupUsername || !signupEmail || !signupPassword || !signupConfirmPassword) {
      setSignupError('All fields are required');
      return;
    }

    if (signupPassword.length < 8) {
      setSignupError('Password must be at least 8 characters');
      return;
    }

    if (signupPassword !== signupConfirmPassword) {
      setSignupError('Passwords do not match');
      return;
    }

    if (signupRole === 'admin' && !adminSignupCode) {
      setSignupError('Admin signup code is required for admin registration');
      return;
    }

    const result = await signup(
      signupUsername,
      signupEmail,
      signupPassword,
      signupRole === 'admin' ? adminSignupCode : '',
      signupRole
    );

    if (!result.ok) {
      setSignupError(result.message);
    }
  };

  // Real-time email validation (client-side only for UX feedback)
  const handleEmailChange = (e) => {
    const email = e.target.value;
    setSignupEmail(email);

    if (email && !email.includes('@')) {
      setEmailCheckMsg('Invalid email format');
    } else if (email) {
      setEmailCheckMsg('✓');
    } else {
      setEmailCheckMsg('');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>AI Task Hub</h1>
          <p>Knowledge + Workflows Platform</p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs">
          <button
            className={`tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setLoginError('');
            }}
            disabled={loading}
          >
            Login
          </button>
          <button
            className={`tab-btn ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => {
              setMode('signup');
              setSignupError('');
            }}
            disabled={loading}
          >
            Sign Up
          </button>
        </div>

        {/* Login Form */}
        {mode === 'login' && (
          <form className="auth-card" onSubmit={handleLogin}>
            <h2>Welcome Back</h2>
            <p className="auth-subtitle">Login to access your workspace</p>

            <label>
              Username
              <input
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                placeholder="your_username"
                required
                disabled={loading}
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </label>

            {loginError && <div className="error-box">{loginError}</div>}

            <button type="submit" disabled={loading} className="auth-btn">
              {loading ? 'Signing in...' : 'Login'}
            </button>

            <p className="auth-footer">
              New here? <button type="button" onClick={() => setMode('signup')} className="link-btn">Create an account</button>
            </p>
          </form>
        )}

        {/* Signup Form */}
        {mode === 'signup' && (
          <form className="auth-card" onSubmit={handleSignup}>
            <h2>Create Account</h2>
            <p className="auth-subtitle">Join the platform to manage tasks and documents</p>

            <label>
              Username
              <input
                value={signupUsername}
                onChange={(e) => setSignupUsername(e.target.value)}
                placeholder="your_username"
                required
                disabled={loading}
              />
            </label>

            <label>
              Email
              <div className="input-with-check">
                <input
                  type="email"
                  value={signupEmail}
                  onChange={handleEmailChange}
                  placeholder="you@example.com"
                  required
                  disabled={loading}
                />
                {emailCheckMsg && <span className="check-status">{emailCheckMsg}</span>}
              </div>
            </label>

            <label>
              Password
              <input
                type="password"
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
                placeholder="Min 8 characters"
                minLength="8"
                required
                disabled={loading}
              />
            </label>

            <label>
              Confirm Password
              <input
                type="password"
                value={signupConfirmPassword}
                onChange={(e) => setSignupConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </label>

            <label>
              Role
              <select
                value={signupRole}
                onChange={(e) => setSignupRole(e.target.value)}
                disabled={loading}
              >
                <option value="user">User (Document Search & Tasks)</option>
                <option value="admin">Admin (Full Access)</option>
              </select>
            </label>

            {signupRole === 'admin' && (
              <label className="admin-label">
                Admin Signup Code
                <input
                  type="password"
                  value={adminSignupCode}
                  onChange={(e) => setAdminSignupCode(e.target.value)}
                  placeholder="Enter admin signup code"
                  required
                  disabled={loading}
                />
                <small>Required to register as admin</small>
              </label>
            )}

            {signupError && <div className="error-box">{signupError}</div>}

            <button type="submit" disabled={loading} className="auth-btn">
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>

            <p className="auth-footer">
              Already have an account? <button type="button" onClick={() => setMode('login')} className="link-btn">Login here</button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
