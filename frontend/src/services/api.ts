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
  withCredentials: true, // Habilitar cookies
})

// Interceptor para agregar el session_id como header
// Solo lo enviamos cuando estamos en desarrollo cross-port
// (diferentes puertos = cookies no se comparten automáticamente)
api.interceptors.request.use(
  (config) => {
    // Detectar si estamos en cross-origin (diferentes puertos)
    const apiUrl = new URL(config.baseURL || API_BASE_URL)
    const isCrossPort = window.location.port !== apiUrl.port
    
    // Solo enviar X-Session-ID si es cross-port y tenemos session_id
    if (isCrossPort) {
      const sessionId = localStorage.getItem('session_id')
      if (sessionId) {
        config.headers['X-Session-ID'] = sessionId
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Ya no necesitamos el interceptor de tokens
// Las cookies se envían automáticamente

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
      
      // Guardar session_id en localStorage para desarrollo cross-port
      if (response.data.session_id) {
        localStorage.setItem('session_id', response.data.session_id)
        console.log('Session ID saved to localStorage:', response.data.session_id)
      }
      
      // Ya no retornamos token, solo mensaje y user
      return {
        message: response.data.message,
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
    // Limpiar session_id del localStorage
    localStorage.removeItem('session_id')
    return response.data
  },
  
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export default api
