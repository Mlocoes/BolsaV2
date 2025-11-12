import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (!user) {
    navigate('/login')
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">BolsaV2 Dashboard</h1>
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
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Welcome to BolsaV2</h2>
          <p className="text-gray-600">Your portfolio management system is ready!</p>
        </div>
      </main>
    </div>
  )
}
