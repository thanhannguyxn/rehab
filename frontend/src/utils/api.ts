import axios from 'axios';
import type { LoginResponse, Exercise, Session, Patient, ErrorAnalyticsResponse } from './types';
import { API_URL } from './config';

// ─── In-memory access token storage ──────────────────────────────────────────
// Never stored in localStorage/sessionStorage — lives only in JS heap.
// Cleared automatically on page refresh; re-populated by the silent refresh on mount.

let _accessToken: string | null = null;

export const setAccessToken = (token: string | null) => { _accessToken = token; };
export const getAccessToken = () => _accessToken;

// ─── Axios instance ───────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // send HttpOnly refresh-token cookie on every request
});

api.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`;
  }
  return config;
});

// ─── 401 → silent refresh → retry ────────────────────────────────────────────

let _isRefreshing = false;
let _refreshQueue: ((token: string) => void)[] = [];

const _flushQueue = (token: string) => {
  _refreshQueue.forEach((cb) => cb(token));
  _refreshQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // Only retry once, and never retry the refresh endpoint itself
    const isRefreshEndpoint = original?.url?.includes('/auth/refresh');
    if (error.response?.status !== 401 || original?._retry || isRefreshEndpoint) {
      return Promise.reject(error);
    }

    if (_isRefreshing) {
      // Another request already triggered a refresh — queue this one
      return new Promise((resolve) => {
        _refreshQueue.push((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    original._retry = true;
    _isRefreshing = true;

    try {
      const { data } = await api.post<LoginResponse>('/auth/refresh');
      setAccessToken(data.access_token);
      _flushQueue(data.access_token);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    } catch (refreshError) {
      setAccessToken(null);
      _refreshQueue = [];
      // Notify AuthContext to clear user state
      window.dispatchEvent(new Event('auth:logout'));
      return Promise.reject(refreshError);
    } finally {
      _isRefreshing = false;
    }
  },
);

// ─── Response types ───────────────────────────────────────────────────────────

interface PatientChatResponse {
  reply: string;
  safety_escalation: boolean;
  used_llm: boolean;
}

interface DoctorChatResponse {
  reply: string;
  used_llm: boolean;
}

interface PatientScheduleNotification {
  id: number;
  exercise_name: string;
  scheduled_for: string;
  doctor_name: string;
  message: string;
}

export interface ChatHistoryEntry {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authAPI = {
  async login(username: string, password: string, role: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/login', { username, password, role });
    return data;
  },

  async register(payload: {
    username: string;
    password: string;
    full_name: string;
    age?: number;
    gender?: string;
    role?: string;
  }): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/register', payload);
    return data;
  },

  async refreshToken(): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/auth/refresh');
    return data;
  },

  async logoutUser(): Promise<void> {
    await api.post('/auth/logout');
  },

  async createPatient(payload: {
    full_name: string;
    username: string;
    email?: string;
    age?: number;
    gender?: string;
    height_cm?: number;
    weight_kg?: number;
    injury_type?: string;
    medical_conditions?: string;
    mobility_level?: string;
    pain_level?: number;
    doctor_notes?: string;
  }): Promise<{ user: Patient; plain_password: string; email_sent: boolean }> {
    const { data } = await api.post('/auth/create-patient', payload);
    return data;
  },
};

// ─── Exercises ────────────────────────────────────────────────────────────────

export const exerciseAPI = {
  async getExercises(): Promise<{ exercises: Exercise[] }> {
    const { data } = await api.get('/exercises');
    return data;
  },
};

// ─── Sessions ─────────────────────────────────────────────────────────────────

export const sessionAPI = {
  async startSession(exerciseName: string): Promise<{ session_id: number }> {
    const { data } = await api.post('/sessions/start', null, {
      params: { exercise_name: exerciseName },
    });
    return data;
  },

  async endSession(sessionId: number): Promise<Session> {
    const { data } = await api.post(`/sessions/${sessionId}/end`);
    return data;
  },

  async getMyHistory(limit = 20): Promise<{ sessions: Session[] }> {
    const { data } = await api.get('/sessions/my-history', { params: { limit } });
    return data;
  },

  async getErrorAnalytics(): Promise<ErrorAnalyticsResponse> {
    const { data } = await api.get('/sessions/error-analytics');
    return data;
  },
};

// ─── Doctor ───────────────────────────────────────────────────────────────────

export const doctorAPI = {
  async getPatients(): Promise<{ patients: Patient[] }> {
    const { data } = await api.get('/doctor/patients');
    return data;
  },

  async getPatientHistory(patientId: number, limit = 20): Promise<{ sessions: Session[] }> {
    const { data } = await api.get(`/doctor/patient/${patientId}/history`, { params: { limit } });
    return data;
  },

  async getPatientErrorAnalytics(patientId: number): Promise<ErrorAnalyticsResponse> {
    const { data } = await api.get(`/doctor/patient/${patientId}/error-analytics`);
    return data;
  },
};

// ─── Exercise management (doctor) ─────────────────────────────────────────────

export const exerciseManagementAPI = {
  async getPendingList(): Promise<{ pending_exercises: unknown[] }> {
    const { data } = await api.get('/doctor/exercises/pending');
    return data;
  },

  async getApprovedList(): Promise<{ exercises: unknown[] }> {
    const { data } = await api.get('/doctor/exercises');
    return data;
  },

  async upload(file: File): Promise<unknown> {
    const form = new FormData();
    form.append('file', file);
    const { data } = await api.post('/doctor/exercises/upload', form);
    return data;
  },

  async updateExercise(id: string, payload: unknown): Promise<unknown> {
    const { data } = await api.put(`/doctor/exercises/${id}`, payload);
    return data;
  },

  async deleteExercise(id: string): Promise<unknown> {
    const { data } = await api.delete(`/doctor/exercises/${id}`);
    return data;
  },

  async getPendingDetail(id: string): Promise<unknown> {
    const { data } = await api.get(`/doctor/exercises/pending/${id}`);
    return data;
  },

  async updatePending(id: string, payload: unknown): Promise<unknown> {
    const { data } = await api.put(`/doctor/exercises/pending/${id}`, payload);
    return data;
  },

  async approve(id: string): Promise<unknown> {
    const { data } = await api.post(`/doctor/exercises/approve/${id}`);
    return data;
  },

  async reanalyze(id: string): Promise<unknown> {
    const { data } = await api.post(`/doctor/exercises/reanalyze/${id}`);
    return data;
  },

  async deletePending(id: string): Promise<unknown> {
    const { data } = await api.delete(`/doctor/exercises/pending/${id}`);
    return data;
  },
};

// ─── Profile ──────────────────────────────────────────────────────────────────

export const profileAPI = {
  async getMe(): Promise<Record<string, unknown>> {
    const { data } = await api.get('/profile/me');
    return data;
  },

  async update(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    const { data } = await api.post('/profile/update', payload);
    return data;
  },

  async getPersonalizedParams(exerciseType: string): Promise<Record<string, unknown>> {
    const { data } = await api.post('/personalized-params', { exercise_type: exerciseType });
    return data;
  },
};

// ─── Agent / Chat ─────────────────────────────────────────────────────────────

export const agentAPI = {
  async patientChat(message: string, exerciseType?: string): Promise<PatientChatResponse> {
    const { data } = await api.post('/agent/patient/chat', { message, exercise_type: exerciseType });
    return data;
  },

  async getPatientChatHistory(limit = 40): Promise<ChatHistoryEntry[]> {
    const { data } = await api.get('/agent/patient/history', { params: { limit } });
    return data;
  },

  async clearPatientChatHistory(): Promise<{ ok: boolean; deleted: number }> {
    const { data } = await api.delete('/agent/patient/history');
    return data;
  },

  async doctorChat(message: string, patientId?: number): Promise<DoctorChatResponse> {
    const { data } = await api.post('/agent/doctor/chat', { message, patient_id: patientId });
    return data;
  },

  async getDoctorChatHistory(limit = 40): Promise<ChatHistoryEntry[]> {
    const { data } = await api.get('/agent/doctor/history', { params: { limit } });
    return data;
  },

  async clearDoctorChatHistory(): Promise<{ ok: boolean; deleted: number }> {
    const { data } = await api.delete('/agent/doctor/history');
    return data;
  },

  async getPatientNotifications(): Promise<{ notifications: PatientScheduleNotification[] }> {
    const { data } = await api.get('/agent/patient/notifications');
    return data;
  },

  async markPatientNotificationRead(scheduleId: number): Promise<{ ok: boolean }> {
    const { data } = await api.post(`/agent/patient/notifications/${scheduleId}/read`);
    return data;
  },

  async getPatientSchedules(): Promise<{
    schedules: Array<{
      id: number;
      exercise_name: string;
      scheduled_for: string;
      doctor_name: string;
      note?: string;
      is_read: boolean;
      created_at: string;
    }>;
  }> {
    const { data } = await api.get('/agent/patient/schedules');
    return data;
  },
};

export default api;
