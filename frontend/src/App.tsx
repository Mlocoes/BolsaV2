import { useEffect } from 'react'
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
  const { logout } = useAuthStore()
  
  useEffect(() => {
    console.log('App: Forzando logout al iniciar (F5 o inicio)')
    // Siempre hacer logout al montar/recargar
    // Esto limpia cualquier sesión previa
    logout().catch(() => {
      // Ignorar errores de logout (puede no haber sesión)
      console.log('App: No había sesión previa para limpiar')
    })
  }, []) // Solo se ejecuta una vez al montar
  
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        {/* Siempre redirigir raíz a login */}
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
