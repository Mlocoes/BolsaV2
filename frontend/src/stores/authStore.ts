import { create } from 'zustand'
import { authAPI } from '../services/api'

interface AuthState {
  user: any
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading true to prevent premature redirects

  login: async (username: string, password: string) => {
    console.log('authStore.login called with username:', username)
    try {
      const response = await authAPI.login(username, password)
      console.log('authAPI.login response:', response)
      // La cookie se setea automáticamente por el servidor
      set({ user: response.user, isAuthenticated: true, isLoading: false })
      console.log('authStore state updated successfully')
    } catch (error) {
      console.error('authStore.login error:', error)
      throw error
    }
  },

  logout: async () => {
    await authAPI.logout()
    // La cookie se elimina automáticamente por el servidor
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  checkAuth: async () => {
    set({ isLoading: true })
    try {
      const user = await authAPI.me()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
