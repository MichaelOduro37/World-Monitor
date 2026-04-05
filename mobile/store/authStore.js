import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { apiClient, setAuthToken } from '../api/client';

const TOKEN_KEY = 'wm_auth_token';
const USER_KEY = 'wm_auth_user';

export const useAuthStore = create((set, get) => ({
  token: null,
  user: null,
  hydrated: false,

  async loadFromStorage() {
    try {
      const [token, userJson] = await Promise.all([
        SecureStore.getItemAsync(TOKEN_KEY),
        SecureStore.getItemAsync(USER_KEY),
      ]);
      if (token) {
        setAuthToken(token);
        set({
          token,
          user: userJson ? JSON.parse(userJson) : null,
          hydrated: true,
        });
      } else {
        set({ hydrated: true });
      }
    } catch {
      set({ hydrated: true });
    }
  },

  async login(email, password) {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const res = await apiClient.post('/api/v1/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const token = res.data.access_token;
    const user = res.data.user || { email };
    setAuthToken(token);
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
    set({ token, user });
  },

  async register(email, password, fullName) {
    await apiClient.post('/api/v1/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    await get().login(email, password);
  },

  async logout() {
    setAuthToken(null);
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
    set({ token: null, user: null });
  },
}));
