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
    console.log('authStore.login called with username:', username)
    try {
      const response = await authAPI.login(username, password)
      console.log('authAPI.login response:', response)
      sessionStorage.setItem('auth_token', response.token)
      set({ user: response.user, token: response.token, isAuthenticated: true })
      console.log('authStore state updated successfully')
    } catch (error) {
      console.error('authStore.login error:', error)
      throw error
    }
  },

  logout: async () => {
    await authAPI.logout()
    sessionStorage.removeItem('auth_token')
    set({ user: null, token: null, isAuthenticated: false })
  },
}))
