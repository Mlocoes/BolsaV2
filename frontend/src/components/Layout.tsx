import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  // ProtectedRoute ya maneja la verificación de usuario
  // Aquí solo renderizamos el layout
  if (!user) {
    return null
  }

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-gray-50">
      <nav className="flex-shrink-0 sticky top-0 z-50 bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-4 md:space-x-8">
            <h1 className="text-xl md:text-2xl font-bold text-gray-900">BolsaV2</h1>
            <div className="flex space-x-2 md:space-x-4 text-sm md:text-base">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                Panel de Control
              </button>
              <button
                onClick={() => navigate('/positions')}
                className="text-gray-600 hover:text-gray-900"
              >
                Posiciones
              </button>
              <button
                onClick={() => navigate('/portfolios')}
                className="text-gray-600 hover:text-gray-900"
              >
                Carteras
              </button>
              <button
                onClick={() => navigate('/assets')}
                className="text-gray-600 hover:text-gray-900"
              >
                Activos
              </button>
              <button
                onClick={() => navigate('/transactions')}
                className="text-gray-600 hover:text-gray-900"
              >
                Transacciones
              </button>
              <button
                onClick={() => navigate('/quotes')}
                className="text-gray-600 hover:text-gray-900"
              >
                Cotizaciones
              </button>
              <button
                onClick={() => navigate('/import')}
                className="text-gray-600 hover:text-gray-900"
              >
                Importar/Exportar
              </button>
              <button
                onClick={() => navigate('/users')}
                className="text-gray-600 hover:text-gray-900"
              >
                Usuarios
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-2 md:space-x-4">
            <span className="text-sm md:text-base text-gray-700">{user.username}</span>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-3 py-1.5 md:px-4 md:py-2 rounded hover:bg-red-700 text-sm md:text-base"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </nav>
      <main className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 flex flex-col h-full max-w-7xl mx-auto px-4 py-4 w-full">
          {children}
        </div>
      </main>
    </div>
  )
}
