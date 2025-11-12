import { create } from 'zustand'
import { authAPI } from '../services/api'

interface AuthState {
  user: any
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (username: string, password: string) => {
    const response = await authAPI.login(username, password)
    sessionStorage.setItem('auth_token', response.token)
    set({ user: response.user, token: response.token, isAuthenticated: true })
  },

  logout: async () => {
    await authAPI.logout()
    sessionStorage.removeItem('auth_token')
    set({ user: null, token: null, isAuthenticated: false })
  },
}))
