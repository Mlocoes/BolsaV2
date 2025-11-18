import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Portfolios from './pages/Portfolios'
import AssetsCatalog from './pages/AssetsCatalog'
import Quotes from './pages/Quotes'
import ImportData from './pages/ImportData'
import UsersCatalog from './pages/UsersCatalog'

function App() {
  console.log('App component rendering...')
  
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
