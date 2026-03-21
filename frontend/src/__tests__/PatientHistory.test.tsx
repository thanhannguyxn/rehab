import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { PatientHistory } from '../pages/PatientHistory';
import { doctorAPI } from '../utils/api';

vi.mock('../utils/api', () => ({
  doctorAPI: {
    getPatientHistory: vi.fn().mockResolvedValue({ sessions: [] }),
  },
  sessionAPI: {
    getMyHistory: vi.fn().mockResolvedValue({ sessions: [] }),
  }
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn().mockReturnValue({ user: { role: 'patient' } }),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

describe('PatientHistory Page', () => {
  it('renders without crashing', () => {
    // Might need useParams depending on mode
    render(
      <MemoryRouter>
        <PatientHistory />
      </MemoryRouter>
    );
  });
});
