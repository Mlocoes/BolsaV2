import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
// import { useAuthStore } from './stores/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Positions from './pages/Positions'
import Portfolios from './pages/Portfolios'
import AssetsCatalog from './pages/AssetsCatalog'
import Quotes from './pages/Quotes'
import ImportData from './pages/ImportData'
import UsersCatalog from './pages/UsersCatalog'
import BulkEditTransactions from './pages/BulkEditTransactions'
import PortfolioTransactions from './pages/PortfolioTransactions'
import TransactionsPortfolioSelection from './pages/TransactionsPortfolioSelection'
import FiscalResult from './pages/FiscalResult'

function App() {
  // const { checkAuth } = useAuthStore() // Ya no se usa checkAuth al inicio

  /* 
   * NOTA: Eliminado checkAuth() para cumplir el requisito de que "F5" cierra la sesión.
   * Al no verificar la sesión al inicio, el estado isAuthenticated es false por defecto,
   * y el ProtectedRoute redirigirá a /login automáticamente.
   */
  useEffect(() => {
    // Limpiar cualquier estado residual si fuera necesario, aunque el store se reinicia en F5
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
          path="/positions"
          element={
            <ProtectedRoute>
              <Positions />
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
        <Route
          path="/portfolio/:id/bulk-edit"
          element={
            <ProtectedRoute>
              <BulkEditTransactions />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolio/:id/transactions"
          element={
            <ProtectedRoute>
              <PortfolioTransactions />
            </ProtectedRoute>
          }
        />
        <Route
          path="/transactions"
          element={
            <ProtectedRoute>
              <TransactionsPortfolioSelection />
            </ProtectedRoute>
          }
        />
        <Route
          path="/fiscal-result"
          element={
            <ProtectedRoute>
              <FiscalResult />
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
