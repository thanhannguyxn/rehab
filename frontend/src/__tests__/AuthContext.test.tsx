import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { authAPI } from '../utils/api';

vi.mock('../utils/api', () => ({
  authAPI: {
    login: vi.fn(),
  },
}));

const TestComponent = () => {
  const { user, isLoading, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Ready'}</div>
      <div data-testid="user-info">{user ? user.username : 'No User'}</div>
      <button data-testid="login-btn" onClick={() => login('testuser', 'pass', 'patient')}>
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('provides default unauthenticated state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('loading').textContent).toBe('Ready');
    expect(screen.getByTestId('user-info').textContent).toBe('No User');
  });

  it('loads user from sessionStorage on mount', () => {
    const fakeUser = { id: 1, username: 'saveduser', role: 'patient' };
    sessionStorage.setItem('token', 'fake-token');
    sessionStorage.setItem('user', JSON.stringify(fakeUser));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('user-info').textContent).toBe('saveduser');
  });

  it('handles invalid user JSON in sessionStorage on mount gracefully', () => {
    // Hide console.error to avoid spamming the test output
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    sessionStorage.setItem('token', 'fake-token');
    sessionStorage.setItem('user', 'invalid-json');

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(consoleSpy).toHaveBeenCalledWith('Failed to parse user data');
    expect(screen.getByTestId('user-info').textContent).toBe('No User');
    expect(sessionStorage.getItem('token')).toBeNull();
    expect(sessionStorage.getItem('user')).toBeNull();
    
    consoleSpy.mockRestore();
  });

  it('login function calls authAPI, sets state, and saves to sessionStorage', async () => {
    const mockUser = { id: 2, username: 'testuser', role: 'patient' };
    (authAPI.login as any).mockResolvedValueOnce({ token: 'new-token', user: mockUser });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await userEvent.click(screen.getByTestId('login-btn'));

    expect(authAPI.login).toHaveBeenCalledWith('testuser', 'pass', 'patient');
    
    await waitFor(() => {
      expect(screen.getByTestId('user-info').textContent).toBe('testuser');
    });

    expect(sessionStorage.getItem('token')).toBe('new-token');
    expect(sessionStorage.getItem('user')).toBe(JSON.stringify(mockUser));
  });

  it('logout function clears state and sessionStorage', async () => {
    const fakeUser = { id: 3, username: 'logoutuser', role: 'doctor' };
    sessionStorage.setItem('token', 'fake-token');
    sessionStorage.setItem('user', JSON.stringify(fakeUser));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('user-info').textContent).toBe('logoutuser');

    await userEvent.click(screen.getByTestId('logout-btn'));

    expect(screen.getByTestId('user-info').textContent).toBe('No User');
    expect(sessionStorage.getItem('token')).toBeNull();
    expect(sessionStorage.getItem('user')).toBeNull();
  });

  it('throws an error if useAuth is used outside of AuthProvider', () => {
    // Hide console.error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => render(<TestComponent />)).toThrow(
      'useAuth must be used within AuthProvider'
    );
    
    consoleSpy.mockRestore();
  });
});
