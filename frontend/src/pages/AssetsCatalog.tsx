import { useState, useEffect } from 'react'
import api from '../services/api'

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
      console.error('Search failed:', error)
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
      alert('Symbol and name are required')
      return
    }

    try {
      if (editingAsset) {
        await api.put(`/assets/${editingAsset.id}`, formData)
        alert('Asset updated successfully')
      } else {
        await api.post('/assets', formData)
        alert('Asset created successfully')
      }
      setShowModal(false)
      loadAssets()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Operation failed')
    }
  }

  const handleDelete = async (asset: Asset) => {
    if (!confirm(`Delete asset ${asset.symbol}?`)) return

    try {
      await api.delete(`/assets/${asset.id}`)
      alert('Asset deleted successfully')
      loadAssets()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Delete failed')
    }
  }

  const filteredAssets = assets.filter(
    (asset) =>
      asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-xl">Loading assets...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Assets Catalog</h1>
          <p className="text-gray-600">Manage stocks, ETFs, and other assets</p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Add Asset
        </button>
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search by symbol or name..."
            className="flex-1 px-4 py-2 border rounded"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Search
          </button>
        </div>
      </div>

      {/* Assets Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Currency</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
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
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(asset)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAssets.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No assets found
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4">
              {editingAsset ? 'Edit Asset' : 'Create Asset'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Symbol *</label>
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
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={formData.asset_type}
                  onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="stock">Stock</option>
                  <option value="etf">ETF</option>
                  <option value="crypto">Crypto</option>
                  <option value="bond">Bond</option>
                  <option value="fund">Fund</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Market</label>
                <input
                  type="text"
                  value={formData.market}
                  onChange={(e) => setFormData({ ...formData, market: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="NASDAQ, NYSE, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Currency</label>
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
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {editingAsset ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
