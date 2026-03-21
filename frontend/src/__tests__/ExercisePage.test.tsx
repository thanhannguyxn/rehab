import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { ExercisePage } from '../pages/ExercisePage';
import { useAuth } from '../context/AuthContext';
import { sessionAPI } from '../utils/api';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../utils/api', () => ({
  sessionAPI: {
    startSession: vi.fn().mockResolvedValue({ session_id: 1 }),
    endSession: vi.fn().mockResolvedValue({}),
  },
  exerciseAPI: {
    getExercises: vi.fn().mockResolvedValue({ exercises: [] }),
  }
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn().mockReturnValue({
    isConnected: true,
    analysis: null,
    sendFrame: vi.fn(),
    sendCustomThresholds: vi.fn(),
    resetState: vi.fn(),
  })
}));

describe('ExercisePage Page', () => {
  it('renders without crashing', () => {
    (useAuth as any).mockReturnValue({ user: { username: 'patient1', role: 'patient' } });
    
    render(
      <MemoryRouter>
        <ExercisePage />
      </MemoryRouter>
    );
  });
});
