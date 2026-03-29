import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { PatientDetail } from '../pages/PatientDetail';
import { doctorAPI } from '../utils/api';

vi.mock('../utils/api', () => ({
  doctorAPI: {
    getPatientHistory: vi.fn().mockResolvedValue({ sessions: [] }),
    getPatientErrorAnalytics: vi.fn().mockResolvedValue({}),
  }
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

describe('PatientDetail Page', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter>
        <PatientDetail />
      </MemoryRouter>
    );
  });
});
