import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { authAPI, setAccessToken } from '../utils/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
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
    // Clear any tokens left over from the old sessionStorage-based auth system.
    sessionStorage.removeItem('token');
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    const restore = async () => {
      try {
        const { access_token, user: restoredUser } = await authAPI.refreshToken();
        setAccessToken(access_token);
        setUser(restoredUser);
        sessionStorage.setItem('user', JSON.stringify(restoredUser));
      } catch {
        // No valid refresh token — user needs to log in.
        sessionStorage.removeItem('user');
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
      sessionStorage.removeItem('user');
    };
    window.addEventListener('auth:logout', onForcedLogout);
    return () => window.removeEventListener('auth:logout', onForcedLogout);
  }, []);

  const login = async (username: string, password: string, role: string) => {
    const { access_token, user: loggedInUser } = await authAPI.login(username, password, role);
    setAccessToken(access_token);
    setUser(loggedInUser);
    // User object is not sensitive — storing it avoids a round-trip on the next render
    sessionStorage.setItem('user', JSON.stringify(loggedInUser));
  };

  const logout = async () => {
    try {
      // Tell the backend to clear the HttpOnly refresh-token cookie
      await authAPI.logoutUser();
    } finally {
      setAccessToken(null);
      setUser(null);
      sessionStorage.removeItem('user');
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
