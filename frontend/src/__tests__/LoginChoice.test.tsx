import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LoginChoice } from '../pages/LoginChoice';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key, // Simply return the translation key for testing
  })
}));

describe('LoginChoice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <LoginChoice />
      </MemoryRouter>
    );
  };

  it('renders the branding and main title', () => {
    renderComponent();
    expect(screen.getByText('Rehab AI')).toBeInTheDocument();
    expect(screen.getByText('loginChoice.title')).toBeInTheDocument();
    expect(screen.getByText('loginChoice.subtitle')).toBeInTheDocument();
  });

  it('renders patient and doctor option links', () => {
    renderComponent();
    
    // Patient option
    expect(screen.getByText('loginChoice.patientTitle')).toBeInTheDocument();
    expect(screen.getByText('loginChoice.patientSubtitle')).toBeInTheDocument();
    
    // Doctor option
    expect(screen.getByText('loginChoice.doctorTitle')).toBeInTheDocument();
    expect(screen.getByText('loginChoice.doctorSubtitle')).toBeInTheDocument();

    // Check if the links point to the right paths
    const links = screen.getAllByRole('link');
    // Patient link, Doctor link, and Back to Home link
    expect(links.length).toBe(3);
    
    expect(links[0].getAttribute('href')).toBe('/login/patient');
    expect(links[1].getAttribute('href')).toBe('/login/doctor');
    expect(links[2].getAttribute('href')).toBe('/');
  });
});
