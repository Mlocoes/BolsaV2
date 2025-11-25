import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { toast } from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const { user, login } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  console.log('Página de inicio de sesión renderizando')

  // Redirigir a dashboard después del login exitoso
  useEffect(() => {
    if (user) {
      console.log('Usuario autenticado, redirigiendo al dashboard')
      navigate('/dashboard', { replace: true })
    }
  }, [user, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (isSubmitting) return

    setIsSubmitting(true)
    try {
      const trimmedUsername = username.trim()
      const trimmedPassword = password.trim()
      console.log('Intentando iniciar sesión con el usuario:', trimmedUsername)
      await login(trimmedUsername, trimmedPassword)
      console.log('Inicio de sesión exitoso, navegando al panel de control')
      toast.success('¡Inicio de sesión exitoso!')
      // La redirección se hará automáticamente por el useEffect
    } catch (error: any) {
      console.error('Error de inicio de sesión:', error)
      const message = error.response?.data?.detail || error.message || 'Error al iniciar sesión'
      toast.error(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-blue-600 p-4">
      <div className="bg-white p-6 md:p-8 rounded-lg shadow-xl w-full max-w-sm md:max-w-md">
        <h1 className="text-2xl md:text-3xl font-bold text-center mb-4 md:mb-6 text-gray-900">BolsaV2</h1>
        <form onSubmit={handleSubmit} className="space-y-3 md:space-y-4">
          <div>
            <label className="block text-xs md:text-sm font-medium text-gray-700">Usuario</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm md:text-base"
              required
            />
          </div>
          <div>
            <label className="block text-xs md:text-sm font-medium text-gray-700">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm md:text-base"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm md:text-base"
          >
            {isSubmitting ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>
      </div>
    </div>
  )
}
