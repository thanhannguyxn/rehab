import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import { Landing } from '../pages/Landing';
import { ThemeProvider } from '../context/ThemeContext';

import { useAuth } from '../context/AuthContext';

// Mock useAuth
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ 
    t: (key: string) => key,
    i18n: { language: 'en', changeLanguage: vi.fn() }
  })
}));

describe('Landing Page', () => {
  beforeAll(() => {
    const mockIntersectionObserver = vi.fn();
    mockIntersectionObserver.mockReturnValue({
      observe: () => null,
      unobserve: () => null,
      disconnect: () => null
    });
    window.IntersectionObserver = mockIntersectionObserver;
  });

  it('renders landing page correctly', () => {
    (useAuth as any).mockReturnValue({ user: null });
    render(
      <ThemeProvider>
        <MemoryRouter>
          <Landing />
        </MemoryRouter>
      </ThemeProvider>
    );
    // Should render the title or branding somewhere
    expect(screen.getAllByText(/Rehab AI|landing/i).length).toBeGreaterThan(0);
  });
});
