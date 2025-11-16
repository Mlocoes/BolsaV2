import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
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
        <Route path="/" element={<Dashboard />} />
        <Route path="/portfolios" element={<Portfolios />} />
        <Route path="/assets" element={<AssetsCatalog />} />
        <Route path="/quotes" element={<Quotes />} />
        <Route path="/import" element={<ImportData />} />
        <Route path="/users" element={<UsersCatalog />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
