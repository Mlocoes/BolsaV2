import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './stores/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Portfolios from './pages/Portfolios'
import AssetsCatalog from './pages/AssetsCatalogHandsontable'
import Quotes from './pages/QuotesHandsontable'
import ImportData from './pages/ImportData'
import UsersCatalog from './pages/UsersCatalogHandsontable'

function App() {
  const { logout } = useAuthStore()
  
  useEffect(() => {
    // SIEMPRE hacer logout al cargar/recargar (F5)
    // Esto fuerza que el usuario tenga que hacer login cada vez
    logout().catch(() => {
      // Ignorar errores si no hay sesión
    })
  }, [])
  
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        {/* Ruta raíz siempre redirige a login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route 
          path="/dashboard" 
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
        {/* Redirigir cualquier ruta no encontrada a login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
