import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
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

// ─── Banner ───
export const bannerApi = {
  getBanners: () => api.get('/banners/'),
};

// ─── Recommendations ───
export const recommendationApi = {
  getExercise: (purpose?: string) =>
    api.get('/recommendations/exercise', { params: purpose ? { purpose } : {} }),
  getDiet: (purpose?: string) =>
    api.get('/recommendations/diet', { params: purpose ? { purpose } : {} }),
  getExerciseCalories: (category?: string) =>
    api.get('/exercise-calories', { params: category ? { category } : {} }),
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
  // 추천
  getAdminExercise: () => api.get('/admin/recommendations/exercise'),
  createExercise: (data: object) => api.post('/admin/recommendations/exercise', data),
  updateExercise: (id: number, data: object) => api.put(`/admin/recommendations/exercise/${id}`, data),
  toggleExercise: (id: number, is_active: boolean) =>
    api.patch(`/admin/recommendations/exercise/${id}`, { is_active }),
  deleteExercise: (id: number) => api.delete(`/admin/recommendations/exercise/${id}`),
  getAdminDiet: () => api.get('/admin/recommendations/diet'),
  createDiet: (data: object) => api.post('/admin/recommendations/diet', data),
  updateDiet: (id: number, data: object) => api.put(`/admin/recommendations/diet/${id}`, data),
  toggleDiet: (id: number, is_active: boolean) =>
    api.patch(`/admin/recommendations/diet/${id}`, { is_active }),
  deleteDiet: (id: number) => api.delete(`/admin/recommendations/diet/${id}`),
  seedRecommendations: () => api.post('/admin/recommendations/seed'),
  // 칼로리 데이터
  getAdminExerciseCalories: () => api.get('/admin/exercise-calories'),
  createExerciseCalorie: (data: object) => api.post('/admin/exercise-calories', data),
  updateExerciseCalorie: (id: number, data: object) => api.put(`/admin/exercise-calories/${id}`, data),
  toggleExerciseCalorie: (id: number, is_active: boolean) =>
    api.patch(`/admin/exercise-calories/${id}`, { is_active }),
  deleteExerciseCalorie: (id: number) => api.delete(`/admin/exercise-calories/${id}`),
  seedExerciseCalories: () => api.post('/admin/exercise-calories/seed'),
  // 배너
  getAdminBanners: () => api.get('/admin/banners/'),
  createBanner: (formData: FormData) =>
    api.post('/admin/banners/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  toggleBanner: (id: number, is_active: boolean) =>
    api.patch(`/admin/banners/${id}`, { is_active }),
  deleteBanner: (id: number) => api.delete(`/admin/banners/${id}`),
};

export default api;
