import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('axios');

describe('api utilities', () => {
  const mockedAxios = axios as unknown as {
    post: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
  };

  const requestUse = vi.fn();
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: {
        use: requestUse,
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    mockedAxios.create = vi.fn(() => instance);
    mockedAxios.post = vi.fn();
  });

  it('authAPI.login posts and returns response payload', async () => {
    const { authAPI } = await import('../utils/api');
    mockedAxios.post.mockResolvedValue({ data: { token: 'abc', user: { id: 1 } } });
    const res = await authAPI.login('u', 'p', 'patient');
    expect(mockedAxios.post).toHaveBeenCalled();
    expect(res.token).toBe('abc');
  });

  it('session and doctor apis call axios instance correctly', async () => {
    const { doctorAPI, exerciseAPI, sessionAPI } = await import('../utils/api');
    instance.post.mockResolvedValue({ data: { session_id: 10 } });
    instance.get.mockResolvedValue({ data: { sessions: [], analytics: [], patients: [], exercises: [] } });

    await sessionAPI.startSession('squat');
    await sessionAPI.endSession(10);
    await sessionAPI.getMyHistory(5);
    await sessionAPI.getErrorAnalytics();
    await doctorAPI.getPatients();
    await doctorAPI.getPatientHistory(2, 3);
    await doctorAPI.getPatientErrorAnalytics(2);
    await exerciseAPI.getExercises();

    expect(instance.post).toHaveBeenCalledWith('/sessions/start', null, {
      params: { exercise_name: 'squat' },
    });
    expect(instance.post).toHaveBeenCalledWith('/sessions/10/end');
    expect(instance.get).toHaveBeenCalledWith('/sessions/my-history', { params: { limit: 5 } });
    expect(instance.get).toHaveBeenCalledWith('/sessions/error-analytics');
    expect(instance.get).toHaveBeenCalledWith('/doctor/patients');
    expect(instance.get).toHaveBeenCalledWith('/doctor/patient/2/history', { params: { limit: 3 } });
    expect(instance.get).toHaveBeenCalledWith('/doctor/patient/2/error-analytics');
    expect(instance.get).toHaveBeenCalledWith('/exercises');
  });

  it('adds bearer token through interceptor', async () => {
    const handlers: Array<(config: { headers: Record<string, string> }) => { headers: Record<string, string> }> = [];
    requestUse.mockImplementation((fn) => {
      handlers.push(fn);
      return 0;
    });

    sessionStorage.setItem('token', 'token-123');
    const { default: api } = await import('../utils/api');

    const config = handlers[0]({ headers: {} });
    expect(config.headers.Authorization).toBe('Bearer token-123');
    expect(api).toBeDefined();
  });
});

