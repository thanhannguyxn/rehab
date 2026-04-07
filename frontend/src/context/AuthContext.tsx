import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../utils/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

// Load user from sessionStorage on mount
  useEffect(() => {
    // Clear legacy auth keys from localStorage to avoid sending stale tokens.
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    const token = sessionStorage.getItem('token');
    const savedUser = sessionStorage.getItem('user');

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error('Failed to parse user data');
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
      }
    } else {
      // Keep token and user in sync: if one is missing, clear both.
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
    }
    
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string, role: string) => {
    const response = await authAPI.login(username, password, role);
    
    sessionStorage.setItem('token', response.token);
    sessionStorage.setItem('user', JSON.stringify(response.user));
    setUser(response.user);
  };

  const logout = () => {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};