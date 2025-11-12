import { useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router-dom'
import DashboardComponent from '../components/Dashboard'

export default function Dashboard() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  console.log('Dashboard rendering, user:', user)

  useEffect(() => {
    console.log('Dashboard useEffect, checking user:', user)
    if (!user) {
      console.log('No user found, redirecting to login')
      navigate('/login')
    }
  }, [user, navigate])

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
          <h1 className="text-2xl font-bold text-gray-900">BolsaV2</h1>
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
        <DashboardComponent />
      </main>
    </div>
  )
}
