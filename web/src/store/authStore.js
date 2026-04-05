import { create } from 'zustand'
import * as api from '../api/client'

const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,

  loadFromStorage: async () => {
    const token = localStorage.getItem('access_token')
    const refresh = localStorage.getItem('refresh_token')
    if (token) {
      set({ token, refreshToken: refresh, isAuthenticated: true })
      try {
        const user = await api.getMe()
        set({ user })
      } catch {
        // token invalid, leave as-is; interceptor will handle refresh
      }
    }
  },

  login: async (email, password) => {
    const data = await api.login(email, password)
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
    set({ token: data.access_token, refreshToken: data.refresh_token, isAuthenticated: true })
    try {
      const user = await api.getMe()
      set({ user })
    } catch {
      set({ user: { email } })
    }
  },

  register: async (email, password, full_name) => {
    const data = await api.register(email, password, full_name)
    // Some APIs return tokens on register; if not, trigger login
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
      set({ token: data.access_token, refreshToken: data.refresh_token, isAuthenticated: true })
      try {
        const user = await api.getMe()
        set({ user })
      } catch {
        set({ user: { email, full_name } })
      }
    } else {
      // Auto-login after registration
      await get().login(email, password)
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false })
  }
}))

export default useAuthStore
