import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { User } from '../types';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => Promise<void>;
  updateUser: (user: User) => void;
  logout: () => Promise<void>;
  loadToken: () => Promise<string | null>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  setAuth: async (token, user) => {
    await AsyncStorage.setItem('auth_token', token);
    set({ token, user, isAuthenticated: true });
  },

  updateUser: (user) => set({ user }),

  logout: async () => {
    await AsyncStorage.removeItem('auth_token');
    set({ token: null, user: null, isAuthenticated: false });
  },

  loadToken: async () => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) set({ token, isAuthenticated: true });
    return token;
  },
}));
