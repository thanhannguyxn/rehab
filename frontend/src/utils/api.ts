import axios from 'axios';
import type { LoginResponse, Exercise, Session, Patient, ErrorAnalyticsResponse } from './types';
import { API_URL } from './config';

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

// Get token from sessionStorage
const getToken = () => sessionStorage.getItem('token');

// Create axios instance with auth
const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests automatically
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============= AUTH APIs =============

export const authAPI = {
  async login(username: string, password: string, role: string): Promise<LoginResponse> {
    const response = await axios.post(`${API_URL}/auth/login`, {
      username,
      password,
      role,
    });
    return response.data;
  },

  async register(data: {
    username: string;
    password: string;
    full_name: string;
    age?: number;
    gender?: string;
    role?: string;
  }): Promise<LoginResponse> {
    const response = await axios.post(`${API_URL}/auth/register`, data);
    return response.data;
  },
};

// ============= EXERCISE APIs =============

export const exerciseAPI = {
  async getExercises(): Promise<{ exercises: Exercise[] }> {
    const response = await api.get('/exercises');
    return response.data;
  },
};

// ============= SESSION APIs =============

export const sessionAPI = {
  async startSession(exerciseName: string): Promise<{ session_id: number }> {
    const response = await api.post('/sessions/start', null, {
      params: { exercise_name: exerciseName },
    });
    return response.data;
  },

  async endSession(sessionId: number): Promise<Session> {
    const response = await api.post(`/sessions/${sessionId}/end`);
    return response.data;
  },

  async getMyHistory(limit: number = 20): Promise<{ sessions: Session[] }> {
    const response = await api.get('/sessions/my-history', {
      params: { limit },
    });
    return response.data;
  },

  async getErrorAnalytics(): Promise<ErrorAnalyticsResponse> {
    const response = await api.get('/sessions/error-analytics');
    return response.data;
  },
};

// ============= DOCTOR APIs =============

export const doctorAPI = {
  async getPatients(): Promise<{ patients: Patient[] }> {
    const response = await api.get('/doctor/patients');
    return response.data;
  },

  async getPatientHistory(
    patientId: number,
    limit: number = 20
  ): Promise<{ sessions: Session[] }> {
    const response = await api.get(`/doctor/patient/${patientId}/history`, {
      params: { limit },
    });
    return response.data;
  },

  async getPatientErrorAnalytics(patientId: number): Promise<ErrorAnalyticsResponse> {
    const response = await api.get(`/doctor/patient/${patientId}/error-analytics`);
    return response.data;
  },
};

// ============= AGENT APIs =============

export const agentAPI = {
  // --- Patient chat ---
  async patientChat(message: string, exerciseType?: string): Promise<PatientChatResponse> {
    const response = await api.post('/agent/patient/chat', {
      message,
      exercise_type: exerciseType,
    });
    return response.data;
  },

  async getPatientChatHistory(limit = 40): Promise<ChatHistoryEntry[]> {
    const response = await api.get('/agent/patient/history', {
      params: { limit },
    });
    return response.data;
  },

  async clearPatientChatHistory(): Promise<{ ok: boolean; deleted: number }> {
    const response = await api.delete('/agent/patient/history');
    return response.data;
  },

  // --- Doctor chat ---
  async doctorChat(message: string, patientId?: number): Promise<DoctorChatResponse> {
    const response = await api.post('/agent/doctor/chat', {
      message,
      patient_id: patientId,
    });
    return response.data;
  },

  async getDoctorChatHistory(limit = 40): Promise<ChatHistoryEntry[]> {
    const response = await api.get('/agent/doctor/history', {
      params: { limit },
    });
    return response.data;
  },

  async clearDoctorChatHistory(): Promise<{ ok: boolean; deleted: number }> {
    const response = await api.delete('/agent/doctor/history');
    return response.data;
  },

  // --- Notifications / Schedules ---
  async getPatientNotifications(): Promise<{ notifications: PatientScheduleNotification[] }> {
    const response = await api.get('/agent/patient/notifications');
    return response.data;
  },

  async markPatientNotificationRead(scheduleId: number): Promise<{ ok: boolean }> {
    const response = await api.post(`/agent/patient/notifications/${scheduleId}/read`);
    return response.data;
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
    const response = await api.get('/agent/patient/schedules');
    return response.data;
  },
};

// Export default api instance for custom calls
export default api;
