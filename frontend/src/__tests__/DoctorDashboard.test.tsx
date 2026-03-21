import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { DoctorDashboard } from '../pages/DoctorDashboard';
import { useAuth } from '../context/AuthContext';
import { doctorAPI } from '../utils/api';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../utils/api', () => ({
  doctorAPI: {
    getPatients: vi.fn().mockResolvedValue({ patients: [] }),
    getPatientHistory: vi.fn().mockResolvedValue({ sessions: [] }),
    getPatientErrorAnalytics: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

describe('DoctorDashboard Page', () => {
  it('renders without crashing', () => {
    (useAuth as any).mockReturnValue({ user: { username: 'Doctor1', role: 'doctor' } });
    
    render(
      <MemoryRouter>
        <DoctorDashboard />
      </MemoryRouter>
    );
  });
});
