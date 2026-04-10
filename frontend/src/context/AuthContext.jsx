import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setUser(null);
      localStorage.removeItem('user');
    }
  }, [token]);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { username, password });
      const nextToken = response.data.token;
      const nextUser = response.data.user;
      localStorage.setItem('token', nextToken);
      localStorage.setItem('user', JSON.stringify(nextUser));
      setToken(nextToken);
      setUser(nextUser);
      return { ok: true };
    } catch (error) {
      const message = error?.response?.data?.error || 'Login failed';
      return { ok: false, message };
    } finally {
      setLoading(false);
    }
  };

  const signup = async (username, email, password, adminSignupCode = '', role = 'user') => {
    setLoading(true);
    try {
      const payload = {
        username,
        email,
        password,
        role,
      };
      
      if (adminSignupCode) {
        payload.admin_signup_code = adminSignupCode;
      }

      const response = await api.post('/auth/signup', payload);
      const nextToken = response.data.token;
      const nextUser = response.data.user;
      localStorage.setItem('token', nextToken);
      localStorage.setItem('user', JSON.stringify(nextUser));
      setToken(nextToken);
      setUser(nextUser);
      return { ok: true };
    } catch (error) {
      let message = 'Signup failed';
      if (error?.response?.data?.error) {
        message = error.response.data.error;
      } else if (error?.response?.data?.username?.[0]) {
        message = error.response.data.username[0];
      } else if (error?.response?.data?.email?.[0]) {
        message = error.response.data.email[0];
      } else if (error?.response?.data?.admin_signup_code?.[0]) {
        message = error.response.data.admin_signup_code[0];
      }
      return { ok: false, message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const refreshMe = async () => {
    if (!token) return;
    try {
      const response = await api.get('/auth/me');
      localStorage.setItem('user', JSON.stringify(response.data));
      setUser(response.data);
    } catch {
      logout();
    }
  };

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      isAdmin: user?.role === 'admin',
      loading,
      login,
      signup,
      logout,
      refreshMe,
    }),
    [token, user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
