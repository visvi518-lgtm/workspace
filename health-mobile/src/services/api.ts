import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://doctornote-backend.onrender.com/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; password: string; nickname: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  updateProfile: (data: object) => api.put('/auth/profile', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.put('/auth/password', data),
};

export const healthApi = {
  getExerciseLogs: (params?: { month?: string }) =>
    api.get('/health/exercise', { params }),
  createExerciseLog: (data: object) => api.post('/health/exercise', data),
  getDietLogs: (params?: { month?: string }) =>
    api.get('/health/diet', { params }),
  createDietLog: (data: object) => api.post('/health/diet', data),
  getWeightRecords: () => api.get('/health/weight'),
  addWeightRecord: (data: { date: string; weight: number }) =>
    api.post('/health/weight', data),
  updateUserHealthProfile: (data: object) => api.put('/health/profile', data),
};

export const recommendationApi = {
  getExercise: (purpose?: string) =>
    api.get('/recommendations/exercise', { params: purpose ? { purpose } : {} }),
  getDiet: (purpose?: string) =>
    api.get('/recommendations/diet', { params: purpose ? { purpose } : {} }),
  getExerciseCalories: (category?: string) =>
    api.get('/exercise-calories', { params: category ? { category } : {} }),
};

export const boardApi = {
  getPosts: (params: { board_type: string; page?: number; search?: string }) =>
    api.get('/board/posts', { params }),
  getPost: (id: number) => api.get(`/board/posts/${id}`),
  createPost: (data: object) => api.post('/board/posts', data),
  getComments: (postId: number) => api.get(`/board/posts/${postId}/comments`),
  createComment: (postId: number, content: string) =>
    api.post(`/board/posts/${postId}/comments`, { content }),
};

export default api;
