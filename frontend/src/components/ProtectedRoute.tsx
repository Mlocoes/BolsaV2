import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuthStore()
  const location = useLocation()

  // Mostrar loading mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-500">Verificando autenticación...</div>
        </div>
      </div>
    )
  }

  // Redirigir a login si no hay usuario autenticado
  if (!user) {
    console.log('ProtectedRoute: No user found, redirecting to login from:', location.pathname)
    return <Navigate to="/login" replace />
  }

  // Renderizar el contenido protegido
  return <>{children}</>
}
