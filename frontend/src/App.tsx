import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './stores/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Portfolios from './pages/Portfolios'
import AssetsCatalog from './pages/AssetsCatalog'
import Quotes from './pages/Quotes'
import ImportData from './pages/ImportData'
import UsersCatalog from './pages/UsersCatalog'

function App() {
  const { checkAuth } = useAuthStore()
  const [isInitialized, setIsInitialized] = useState(false)
  
  useEffect(() => {
    console.log('App: Initializing authentication check...')
    // Verificar autenticación una sola vez al montar la app
    checkAuth().finally(() => {
      console.log('App: Authentication check completed')
      setIsInitialized(true)
    })
  }, []) // Solo se ejecuta una vez al montar
  
  // Mostrar loading mientras se inicializa
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-500">Iniciando aplicación...</div>
        </div>
      </div>
    )
  }
  
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/portfolios" 
          element={
            <ProtectedRoute>
              <Portfolios />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/assets" 
          element={
            <ProtectedRoute>
              <AssetsCatalog />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/quotes" 
          element={
            <ProtectedRoute>
              <Quotes />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/import" 
          element={
            <ProtectedRoute>
              <ImportData />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/users" 
          element={
            <ProtectedRoute>
              <UsersCatalog />
            </ProtectedRoute>
          } 
        />
        {/* Redirigir cualquier ruta no encontrada al dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
