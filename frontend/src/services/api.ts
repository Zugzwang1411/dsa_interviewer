import axios from 'axios';
import { StartSessionResponse, MessageResponse, SessionState, InterviewSummary } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  async startSession(candidateName: string): Promise<StartSessionResponse> {
    const response = await api.post('/api/session/start', {
      candidate_name: candidateName,
    });
    return response.data;
  },

  async sendMessage(sessionId: string, message: string): Promise<MessageResponse> {
    const response = await api.post(`/api/session/${sessionId}/message`, {
      message,
    });
    return response.data;
  },

  async getSessionState(sessionId: string): Promise<SessionState> {
    const response = await api.get(`/api/session/${sessionId}/state`);
    return response.data.data;
  },

  async endSession(sessionId: string): Promise<InterviewSummary> {
    const response = await api.post(`/api/session/${sessionId}/end`);
    return response.data;
  },

  async exportSession(sessionId: string): Promise<any> {
    console.log('API: Exporting session:', sessionId);
    console.log('API: Base URL:', API_BASE_URL);
    console.log('API: Full URL:', `${API_BASE_URL}/api/session/${sessionId}/export`);
    
    try {
      const response = await api.get(`/api/session/${sessionId}/export`);
      console.log('API: Response received:', response.status, response.data);
      return response.data.data;
    } catch (error) {
      console.error('API: Export error:', error);
      throw error;
    }
  },
};
