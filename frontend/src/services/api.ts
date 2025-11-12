import axios from 'axios'

// Detectar dinámicamente la URL del API basándose en el host actual
const getApiBaseUrl = () => {
  // Si estamos en desarrollo con Vite, usar la variable de entorno
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  }
  
  // En producción, usar el mismo host que está sirviendo el frontend
  const host = window.location.hostname
  const protocol = window.location.protocol
  return `${protocol}//${host}:8000/api`
}

const API_BASE_URL = getApiBaseUrl()

console.log('API_BASE_URL configured as:', API_BASE_URL)

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authAPI = {
  login: async (username: string, password: string) => {
    console.log('authAPI.login called with username:', username)
    console.log('API_BASE_URL:', API_BASE_URL)
    
    // El endpoint espera application/x-www-form-urlencoded
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    console.log('Sending POST request to:', `${API_BASE_URL}/auth/login`)
    
    try {
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      
      console.log('Login response received:', response.data)
      
      return {
        token: response.data.access_token,
        user: response.data.user,
      }
    } catch (error: any) {
      console.error('authAPI.login error:', error)
      console.error('Error response:', error.response?.data)
      throw error
    }
  },
  logout: async () => {
    const response = await api.post('/auth/logout')
    return response.data
  },
}

export default api
