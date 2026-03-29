import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { PatientDashboard } from '../pages/PatientDashboard';
import { useAuth } from '../context/AuthContext';
import { sessionAPI } from '../utils/api';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../utils/api', () => ({
  sessionAPI: {
    getMyHistory: vi.fn().mockResolvedValue({ sessions: [] }),
    getErrorAnalytics: vi.fn().mockResolvedValue({ summary: {} }),
  }
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

describe('PatientDashboard Page', () => {
  it('renders without crashing', () => {
    (useAuth as any).mockReturnValue({ user: { username: 'Patient1', role: 'patient' } });
    
    render(
      <MemoryRouter>
        <PatientDashboard />
      </MemoryRouter>
    );
  });
});
