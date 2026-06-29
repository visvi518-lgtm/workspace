import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ─── Auth ───
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: {
    email: string;
    password: string;
    nickname: string;
    name?: string;
  }) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  meWithToken: (token: string) =>
    api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } }),
  updateProfile: (data: object) => api.put('/auth/profile', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.put('/auth/password', data),
  googleLogin: (code: string) => api.post('/auth/google', { code }),
  naverLogin: (code: string) => api.post('/auth/naver', { code }),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post('/auth/reset-password', { token, new_password }),
};

// ─── Board ───
export const boardApi = {
  getPosts: (params: {
    board_type: string;
    page?: number;
    per_page?: number;
    search?: string;
    tag?: string;
  }) => api.get('/board/posts', { params }),
  getPost: (id: number) => api.get(`/board/posts/${id}`),
  createPost: (data: object) => api.post('/board/posts', data),
  updatePost: (id: number, data: object) => api.put(`/board/posts/${id}`, data),
  deletePost: (id: number) => api.delete(`/board/posts/${id}`),
  getComments: (postId: number) => api.get(`/board/posts/${postId}/comments`),
  createComment: (postId: number, content: string) =>
    api.post(`/board/posts/${postId}/comments`, { content }),
  deleteComment: (postId: number, commentId: number) =>
    api.delete(`/board/posts/${postId}/comments/${commentId}`),
};

// ─── Health Management ───
export const healthApi = {
  getExerciseLogs: (params?: { month?: string }) =>
    api.get('/health/exercise', { params }),
  createExerciseLog: (data: object) => api.post('/health/exercise', data),
  updateExerciseLog: (id: number, data: object) =>
    api.put(`/health/exercise/${id}`, data),
  getDietLogs: (params?: { month?: string }) =>
    api.get('/health/diet', { params }),
  createDietLog: (data: object) => api.post('/health/diet', data),
  updateDietLog: (id: number, data: object) =>
    api.put(`/health/diet/${id}`, data),
  getWeightRecords: () => api.get('/health/weight'),
  addWeightRecord: (data: { date: string; weight: number }) =>
    api.post('/health/weight', data),
  analyzeCalories: (formData: FormData) =>
    api.post('/health/analyze-calories', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getCalendarData: (month: string) =>
    api.get('/health/calendar', { params: { month } }),
  updateUserHealthProfile: (data: object) => api.put('/health/profile', data),
};

// ─── Chat ───
export const chatApi = {
  getSessions: () => api.get('/chat/sessions'),
  createSession: () => api.post('/chat/sessions'),
  getMessages: (sessionId: number) =>
    api.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: number, content: string) =>
    api.post(`/chat/sessions/${sessionId}/messages`, { content }),
  deleteSession: (sessionId: number) =>
    api.delete(`/chat/sessions/${sessionId}`),
};

// ─── Admin ───
export const adminApi = {
  getUsers: (params?: { page?: number; search?: string }) =>
    api.get('/admin/users', { params }),
  banUser: (data: { user_id: number; duration: string; reason: string }) =>
    api.post('/admin/users/ban', data),
  unbanUser: (userId: number) => api.post(`/admin/users/${userId}/unban`),
  deletePost: (postId: number) => api.delete(`/admin/posts/${postId}`),
  getStats: () => api.get('/admin/stats'),
  // 콘텐츠 관리
  getContent: (params?: { board_type?: string; crawl_status?: string; page?: number }) =>
    api.get('/admin/content', { params }),
  publishContent: (postId: number) => api.post(`/admin/content/${postId}/publish`),
  rejectContent: (postId: number) => api.post(`/admin/content/${postId}/reject`),
  seedContent: () => api.post('/admin/content/seed'),
  triggerCrawl: (boardType: 'health' | 'exercise') => api.post(`/admin/crawl/${boardType}`),
  getCrawlStatus: () => api.get('/admin/crawl/status'),
  stopCrawl: () => api.post('/admin/crawl/stop'),
};

export default api;
