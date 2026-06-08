import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { authAPI, setAccessToken } from '../utils/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updated: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const didRestore = useRef(false);

  // On mount: try a silent token refresh to restore session from the HttpOnly cookie.
  // If the cookie is missing or expired, the user simply lands on the login page.
  useEffect(() => {
    if (didRestore.current) return;
    didRestore.current = true;

    const restore = async () => {
      try {
        const { access_token, user: restoredUser } = await authAPI.refreshToken();
        setAccessToken(access_token);
        setUser(restoredUser);
      } catch {
        // No valid refresh token — user needs to log in.
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    restore();
  }, []);

  // The response interceptor in api.ts fires this when a refresh attempt fails,
  // meaning the session is gone and we need to clear the local user state.
  useEffect(() => {
    const onForcedLogout = () => {
      setUser(null);
    };
    window.addEventListener('auth:logout', onForcedLogout);
    return () => window.removeEventListener('auth:logout', onForcedLogout);
  }, []);

  const login = async (username: string, password: string, role: string) => {
    const { access_token, user: loggedInUser } = await authAPI.login(username, password, role);
    setAccessToken(access_token);
    setUser(loggedInUser);
  };

  const logout = async () => {
    try {
      await authAPI.logoutUser();
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  };

  const updateUser = (updated: Partial<User>) => {
    setUser(prev => prev ? { ...prev, ...updated } : prev);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
