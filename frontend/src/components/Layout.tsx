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
    navigate('/login')
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-gray-900">BolsaV2</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900"
              >
                Dashboard
              </button>
              <button
                onClick={() => navigate('/portfolios')}
                className="text-gray-600 hover:text-gray-900"
              >
                Portfolios
              </button>
              <button
                onClick={() => navigate('/assets')}
                className="text-gray-600 hover:text-gray-900"
              >
                Assets
              </button>
              <button
                onClick={() => navigate('/import')}
                className="text-gray-600 hover:text-gray-900"
              >
                Import/Export
              </button>
              <button
                onClick={() => navigate('/users')}
                className="text-gray-600 hover:text-gray-900"
              >
                Users
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-700">{user.username}</span>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}
