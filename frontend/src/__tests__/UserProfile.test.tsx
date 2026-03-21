import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { UserProfile } from '../pages/UserProfile';
import { useAuth } from '../context/AuthContext';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}));

describe('UserProfile Page', () => {
  it('renders without crashing', () => {
    (useAuth as any).mockReturnValue({ user: { username: 'user1', full_name: 'User One', role: 'patient' } });

    render(
      <MemoryRouter>
        <UserProfile />
      </MemoryRouter>
    );
  });
});
