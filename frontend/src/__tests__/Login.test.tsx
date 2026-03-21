import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Login } from '../pages/Login';
import { useAuth } from '../context/AuthContext';

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  })
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as any,
    useNavigate: () => mockNavigate,
  };
});

describe('Login', () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({ login: mockLogin });
  });

  const renderComponentWithRole = (role: string) => {
    return render(
      <MemoryRouter initialEntries={[`/login/${role}`]}>
        <Routes>
          <Route path="/login/:role" element={<Login />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders patient login view correctly', () => {
    renderComponentWithRole('patient');
    
    // Check titles
    expect(screen.getByText(/login.loginButton login.patientAccount/)).toBeInTheDocument();
    
    // Check info visibility
    expect(screen.getByText('login.systemName')).toBeInTheDocument();
    
    // Form fields
    expect(screen.getByLabelText('login.usernameLabel')).toBeInTheDocument();
    expect(screen.getByLabelText('login.passwordLabel')).toBeInTheDocument();
  });

  it('renders doctor login view correctly', () => {
    renderComponentWithRole('doctor');
    
    // Check titles
    expect(screen.getByText(/login.loginButton login.doctorAccount/)).toBeInTheDocument();
  });

  it('handles successful login and navigation as doctor', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderComponentWithRole('doctor');

    const usernameInput = screen.getByLabelText('login.usernameLabel');
    const passwordInput = screen.getByLabelText('login.passwordLabel');
    const submitBtn = screen.getByRole('button', { name: 'login.loginButton' });

    await userEvent.type(usernameInput, 'doctor1');
    await userEvent.type(passwordInput, 'doctor123');
    await userEvent.click(submitBtn);

    expect(mockLogin).toHaveBeenCalledWith('doctor1', 'doctor123', 'doctor');
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('handles successful login and navigation as patient', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderComponentWithRole('patient');

    // Simulate input and submit
    await userEvent.type(screen.getByLabelText('login.usernameLabel'), 'patient1');
    await userEvent.type(screen.getByLabelText('login.passwordLabel'), 'pass123');
    await userEvent.click(screen.getByRole('button', { name: 'login.loginButton' }));

    expect(mockLogin).toHaveBeenCalledWith('patient1', 'pass123', 'patient');
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('displays error message on failed login', async () => {
    const errorObj = { response: { data: { detail: 'Invalid credentials error' } } };
    mockLogin.mockRejectedValueOnce(errorObj);
    renderComponentWithRole('patient');

    await userEvent.type(screen.getByLabelText('login.usernameLabel'), 'wrong');
    await userEvent.type(screen.getByLabelText('login.passwordLabel'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'login.loginButton' }));

    // Verify error is shown
    await waitFor(() => {
      expect(screen.getByText('Invalid credentials error')).toBeInTheDocument();
    });
    
    // Fallback translation test if detail is absent
    const errorObjEmpty = {};
    mockLogin.mockRejectedValueOnce(errorObjEmpty);
    await userEvent.click(screen.getByRole('button', { name: 'login.loginButton' }));
    
    await waitFor(() => {
      expect(screen.getByText('login.loginFailed')).toBeInTheDocument();
    });
  });
});
