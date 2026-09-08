import React, { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user');
      if (!savedUser || savedUser === 'undefined' || savedUser === 'null') return null;
      return JSON.parse(savedUser);
    } catch (err) {
      console.warn('Clearing invalid stored user session:', err);
      localStorage.removeItem('user');
      return null;
    }
  });
  const [token, setToken] = useState(() => {
    const savedToken = localStorage.getItem('token');
    return savedToken && savedToken !== 'undefined' ? savedToken : null;
  });
  const [loading, setLoading] = useState(true);

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  // Restore user profile on boot
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const res = await client.get('/auth/me');
          if (res.data.success) {
            setUser(res.data.data);
            localStorage.setItem('user', JSON.stringify(res.data.data));
          }
        } catch (err) {
          console.error('Failed to restore auth session:', err);
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (emailOrPhone, password) => {
    const res = await client.post('/auth/login', { emailOrPhone, password });
    if (res.data.success) {
      const { token: newToken, ...userObj } = res.data.data;
      setToken(newToken);
      setUser(userObj);
      localStorage.setItem('token', newToken);
      localStorage.setItem('user', JSON.stringify(userObj));
      return userObj;
    }
    throw new Error(res.data.message || 'Login failed');
  };

  const register = async (name, email, phone, password) => {
    const res = await client.post('/auth/register', { name, email, phone, password });
    if (res.data.success) {
      const { token: newToken, ...userObj } = res.data.data;
      setToken(newToken);
      setUser(userObj);
      localStorage.setItem('token', newToken);
      localStorage.setItem('user', JSON.stringify(userObj));
      return userObj;
    }
    throw new Error(res.data.message || 'Registration failed');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
