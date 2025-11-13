import { useState, useEffect } from 'react'
import api from '../services/api'
import Layout from '../components/Layout'

interface Asset {
  id: string
  symbol: string
  name: string
  asset_type: string
  market?: string
  currency: string
  created_at: string
}

export default function AssetsCatalog() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null)
  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    asset_type: 'stock',
    market: '',
    currency: 'USD'
  })

  useEffect(() => {
    loadAssets()
  }, [])

  const loadAssets = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/assets')
      setAssets(response.data)
    } catch (error) {
      console.error('Failed to load assets:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      loadAssets()
      return
    }

    try {
      const response = await api.get(`/assets/search?q=${searchTerm}`)
      setAssets(response.data)
    } catch (error) {
      console.error('Búsqueda fallida:', error)
    }
  }

  const openCreateModal = () => {
    setEditingAsset(null)
    setFormData({ symbol: '', name: '', asset_type: 'stock', market: '', currency: 'USD' })
    setShowModal(true)
  }

  const openEditModal = (asset: Asset) => {
    setEditingAsset(asset)
    setFormData({
      symbol: asset.symbol,
      name: asset.name,
      asset_type: asset.asset_type,
      market: asset.market || '',
      currency: asset.currency
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.symbol || !formData.name) {
      alert('El símbolo y el nombre son obligatorios')
      return
    }

    try {
      if (editingAsset) {
        await api.put(`/assets/${editingAsset.id}`, formData)
        alert('Activo actualizado correctamente')
      } else {
        await api.post('/assets', formData)
        alert('Activo creado correctamente')
      }
      setShowModal(false)
      loadAssets()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Operación fallida')
    }
  }

  const handleDelete = async (asset: Asset) => {
    if (!confirm(`¿Eliminar activo ${asset.symbol}?`)) return

    try {
      await api.delete(`/assets/${asset.id}`)
      alert('Activo eliminado correctamente')
      loadAssets()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar')
    }
  }

  const filteredAssets = assets.filter(
    (asset) =>
      asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="text-xl">Cargando activos...</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="container mx-auto p-6 space-y-6">
      {/* Cabecera */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Catálogo de Activos</h1>
          <p className="text-gray-600">Gestiona acciones, ETFs y otros activos</p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Añadir Activo
        </button>
      </div>

      {/* Búsqueda */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Buscar por símbolo o nombre..."
            className="flex-1 px-4 py-2 border rounded"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Buscar
          </button>
        </div>
      </div>

      {/* Tabla de Activos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Símbolo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mercado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAssets.map((asset) => (
              <tr key={asset.id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">{asset.symbol}</td>
                <td className="px-6 py-4">{asset.name}</td>
                <td className="px-6 py-4">{asset.asset_type}</td>
                <td className="px-6 py-4">{asset.market || '-'}</td>
                <td className="px-6 py-4">{asset.currency}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => openEditModal(asset)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(asset)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAssets.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron activos
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4">
              {editingAsset ? 'Editar Activo' : 'Crear Activo'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Símbolo *</label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border rounded"
                  required
                  disabled={!!editingAsset}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Nombre *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tipo</label>
                <select
                  value={formData.asset_type}
                  onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="stock">Acción</option>
                  <option value="etf">ETF</option>
                  <option value="crypto">Criptomoneda</option>
                  <option value="bond">Bono</option>
                  <option value="fund">Fondo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Mercado</label>
                <input
                  type="text"
                  value={formData.market}
                  onChange={(e) => setFormData({ ...formData, market: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="NASDAQ, NYSE, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Moneda</label>
                <input
                  type="text"
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {editingAsset ? 'Actualizar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </Layout>
  )
}
