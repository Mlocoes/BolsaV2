import { useState, useEffect, useRef } from 'react'
import { HotTable } from '@handsontable/react'
import { registerAllModules } from 'handsontable/registry'
import { registerLanguageDictionary, esMX } from 'handsontable/i18n'
import 'handsontable/dist/handsontable.full.min.css'
import '../styles/handsontable-custom.css'
import api from '../services/api'
import Layout from '../components/Layout'

// Registrar todos los módulos de Handsontable
registerAllModules()
// Registrar idioma español (usando es-MX pero con código es-ES)
const esESDict = { ...esMX, languageCode: 'es-ES' }
registerLanguageDictionary(esESDict)

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
  // Debug: mark component initialization so we can confirm the bundle loaded in the browser
  console.log('🚀 AssetsCatalog INIT - bundle id: ASSETS_BUNDLE_20251128')
  const [assets, setAssets] = useState<Asset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null)
  const [importingAsset, setImportingAsset] = useState<Asset | null>(null)
  const [isImporting, setIsImporting] = useState(false)

  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    asset_type: 'stock',
    market: '',
    currency: 'USD'
  })
  const [importData, setImportData] = useState({
    from_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    to_date: new Date().toISOString().split('T')[0],
    force_refresh: false
  })
  const hotTableRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleMouseDown = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const button = target.closest('button')

      if (button) {
        const actionType = button.getAttribute('data-action')
        const assetId = button.getAttribute('data-asset-id')

        if (actionType && assetId) {
          // Stop propagation immediately
          e.stopPropagation()

          // We don't prevent default here to allow the button visual press state, 
          // but we might need it if HT interferes. Let's try just stopPropagation first.
          // Actually, for mousedown, if we don't prevent default, HT might start selection.
          // But if we do, the button might not 'click'. 
          // Since we trigger action manually, it's fine.

          const asset = assets.find(a => String(a.id) === String(assetId) || a.symbol === assetId)
          if (asset) {
            if (actionType === 'import') openImportModal(asset)
            else if (actionType === 'edit') openEditModal(asset)
            else if (actionType === 'delete') handleDelete(asset.id, asset.symbol)
          }
        }
      }
    }

    // Use capture phase on mousedown to beat Handsontable's selection logic
    container.addEventListener('mousedown', handleMouseDown, { capture: true })

    return () => {
      container.removeEventListener('mousedown', handleMouseDown, { capture: true })
    }
  }, [assets])

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

  const handleDelete = async (assetId: string, symbol: string) => {
    if (!confirm(`¿Eliminar activo ${symbol}?`)) return

    try {
      await api.delete(`/assets/${assetId}`)
      alert('Activo eliminado correctamente')
      loadAssets()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar')
    }
  }

  const openImportModal = (asset: Asset) => {
    setImportingAsset(asset)
    setImportData({
      from_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      to_date: new Date().toISOString().split('T')[0],
      force_refresh: false
    })
    setShowImportModal(true)
  }

  const handleImportHistorical = async () => {
    if (!importingAsset) return

    setIsImporting(true)

    try {
      const response = await api.post(
        `/quotes/import-historical-smart?symbol=${importingAsset.symbol}&start_date=${importData.from_date}&end_date=${importData.to_date}&force_refresh=${importData.force_refresh}`
      )

      if (response.data) {
        alert(`Importados ${response.data.created} registros para ${importingAsset.symbol}`)
        setShowImportModal(false)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error en la importación')
    } finally {
      setIsImporting(false)
    }
  }

  const handleUpdateAllQuotes = async () => {
    if (!confirm('¿Actualizar cotizaciones de todos los activos? Puede tardar varios minutos.')) return

    try {
      const response = await api.post('/quotes/update-all-latest')
      alert(`Actualizados ${response.data.updated} de ${response.data.total_assets} activos`)
    } catch (error: any) {
      alert('Error al actualizar cotizaciones')
    }
  }

  const filteredAssets = assets.filter(
    (asset) =>
      asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getAssetTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      stock: 'Acción',
      etf: 'ETF',
      crypto: 'Cripto',
      bond: 'Bono',
      fund: 'Fondo'
    }
    return labels[type] || type
  }

  // Preparar datos para Handsontable
  const tableData = filteredAssets.map(asset => ({
    id: asset.id,
    symbol: asset.symbol,
    name: asset.name,
    asset_type: getAssetTypeLabel(asset.asset_type),
    market: asset.market || '-',
    currency: asset.currency
  }))

  useEffect(() => {
    // Asegurar que Handsontable se inicialice correctamente
    console.log('AssetsCatalog - tableData:', tableData.length, 'filas')
    console.log('AssetsCatalog - filteredAssets:', filteredAssets.length, 'filas')
    if (hotTableRef.current && tableData.length > 0) {
      console.log('HotTable ref está disponible')
    } else {
      console.log('HotTable ref NO está disponible aún')
    }
  }, [tableData, filteredAssets])

  const columns = [
    {
      data: 'symbol',
      title: 'Símbolo',
      readOnly: true,
      width: 120,
      className: 'htLeft htBold'
    },
    {
      data: 'name',
      title: 'Nombre',
      readOnly: true,
      width: 250
    },
    {
      data: 'asset_type',
      title: 'Tipo',
      readOnly: true,
      width: 100
    },
    {
      data: 'market',
      title: 'Mercado',
      readOnly: true,
      width: 100
    },
    {
      data: 'currency',
      title: 'Moneda',
      readOnly: true,
      width: 80,
      className: 'htCenter'
    },
    {
      data: 'id',
      title: 'Acciones',
      readOnly: true,
      width: 200,
      renderer: function (_instance: any, td: HTMLTableCellElement, _row: number, _col: number, _prop: any, _value: any) {
        td.innerHTML = ''
        td.classList.add('htActionCell')

        // Helper to create button string (no inline events, handled by hook)
        const createBtnHTML = (text: string, className: string, title: string = '', action: string = '', id: string = '', symbol: string = '') => {
          // Add data-action and data-asset-id attributes; avoid inline onclick and rely on global click listener
          const escapedId = String(id).replace(/\"/g, '&quot;')
          const escapedSymbol = String(symbol ?? '').replace(/\"/g, '&quot;')
          return `<button type=\"button\" class=\"${className}\" title=\"${title}\" data-action=\"${action}\" data-asset-id=\"${escapedId}\" data-asset-symbol=\"${escapedSymbol}\">${text}</button>`
        }

        // Attempt to pass symbol to buttons to match asset by symbol when necessary
        const instance: any = (_instance as any)
        const source = instance?.getSourceDataAtRow ? instance.getSourceDataAtRow(instance.toPhysicalRow(_row)) : undefined
        const symbol = source?.symbol || ''
        const importBtn = createBtnHTML('📥', 'action-btn-import text-green-600 hover:text-green-900 mr-2 text-lg cursor-pointer', 'Importar Histórico', 'import', String(_value), String(symbol))
        const editBtn = createBtnHTML('Editar', 'action-btn-edit text-blue-600 hover:text-blue-900 mr-2 text-sm font-medium cursor-pointer', 'Editar activo', 'edit', String(_value), String(symbol))
        const deleteBtn = createBtnHTML('Eliminar', 'action-btn-delete text-red-600 hover:text-red-900 text-sm font-medium cursor-pointer', 'Eliminar activo', 'delete', String(_value), String(symbol))

        td.innerHTML = `${importBtn}${editBtn}${deleteBtn}`
        // Ensure buttons are clickable and accessible (reinforce attributes)
        const btns = td.querySelectorAll('button')
        btns.forEach(b => {
          b.setAttribute('type', 'button')
          b.setAttribute('role', 'button')
          b.setAttribute('tabindex', '0')
          b.setAttribute('style', (b.getAttribute('style') || '') + ';pointer-events:auto;')
          if (!b.getAttribute('aria-label')) b.setAttribute('aria-label', b.textContent?.trim() || 'Acción')
        })
        // (attributes already set above)
        return td
      }
    }
  ]

  if (isLoading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <div className="text-xl text-gray-600">Cargando activos...</div>
          </div>
        </div>
      </Layout>
    )
  }

  console.log('📊 AssetsCatalog render - assets:', assets.length, 'filteredAssets:', filteredAssets.length, 'tableData:', tableData.length)

  return (
    <Layout>
      <div className="flex flex-col h-full space-y-2 md:space-y-3">
        {/* Cabecera - compacta */}
        <div className="flex-shrink-0 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <h1 className="text-xl md:text-2xl font-bold">Catálogo de Activos</h1>
            <p className="text-xs md:text-sm text-gray-600">Gestiona acciones, ETFs y otros activos</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleUpdateAllQuotes}
              className="px-2 py-1 md:px-4 md:py-2 bg-green-600 text-white rounded hover:bg-green-700 text-xs md:text-sm"
            >
              📈 Actualizar Cotizaciones
            </button>
            <button
              onClick={openCreateModal}
              className="px-2 py-1 md:px-4 md:py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs md:text-sm"
            >
              + Añadir Activo
            </button>
          </div>
        </div>

        {/* Búsqueda - compacta */}
        <div className="flex-shrink-0 bg-white p-2 md:p-4 rounded-lg shadow">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Buscar por símbolo o nombre..."
              className="flex-1 px-2 py-1 md:px-4 md:py-2 border rounded text-xs md:text-sm"
            />
            <button
              onClick={handleSearch}
              className="px-3 py-1 md:px-6 md:py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-xs md:text-sm"
            >
              Buscar
            </button>
          </div>
        </div>

        {/* Tabla con Handsontable - altura fija con scroll interno */}
        <div
          ref={containerRef}
          className="bg-white rounded-lg shadow p-2 md:p-4"
        >
            {filteredAssets.length === 0 ? (
              <div className="flex items-center justify-center text-gray-500 h-96">
                No se encontraron activos
              </div>
            ) : (
              <div style={{ height: '500px', width: '100%' }}>
              <HotTable
                ref={hotTableRef}
                data={tableData}
                columns={columns}
                colHeaders={true}
                rowHeaders={false}
                height={500}
                licenseKey="non-commercial-and-evaluation"
                stretchH="all"
                autoWrapRow={true}
                autoWrapCol={true}
                filters={true}
                dropdownMenu={[
                  'filter_by_condition',
                  'filter_by_value',
                  'filter_action_bar',
                  '---------',
                  'alignment'
                ]}
                columnSorting={true}
                manualColumnResize={true}
                contextMenu={[
                  'row_above',
                  'row_below',
                  '---------',
                  'col_left',
                  'col_right',
                  '---------',
                  'remove_row',
                  'remove_col',
                  '---------',
                  'undo',
                  'redo',
                  '---------',
                  'make_read_only',
                  '---------',
                  'alignment'
                ]}
                afterContextMenuShow={() => {
                  const mainContainer = document.querySelector('main.overflow-hidden') as HTMLElement;
                  if (mainContainer) {
                    mainContainer.style.overflow = 'visible';
                  }
                }}
                afterContextMenuHide={() => {
                  const mainContainer = document.querySelector('main.overflow-hidden') as HTMLElement;
                  if (mainContainer) {
                    mainContainer.style.overflow = 'hidden';
                  }
                }}
                afterDropdownMenuShow={() => {
                  const mainContainer = document.querySelector('main.overflow-hidden') as HTMLElement;
                  if (mainContainer) {
                    mainContainer.style.overflow = 'visible';
                  }
                }}
                afterDropdownMenuHide={() => {
                  const mainContainer = document.querySelector('main.overflow-hidden') as HTMLElement;
                  if (mainContainer) {
                    mainContainer.style.overflow = 'hidden';
                  }
                }}
                language="es-ES"
                width="100%"
              />
              </div>
            )}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[2000]">
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

        {/* Modal de Importación Histórica */}
        {showImportModal && importingAsset && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[2000]">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold mb-4">Importar Datos Históricos</h2>
              <p className="text-gray-600 mb-4">
                Activo: <span className="font-semibold">{importingAsset.symbol}</span>
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Fecha Inicio</label>
                  <input
                    type="date"
                    value={importData.from_date}
                    onChange={(e) => setImportData({ ...importData, from_date: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                    max={importData.to_date}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Fecha Fin</label>
                  <input
                    type="date"
                    value={importData.to_date}
                    onChange={(e) => setImportData({ ...importData, to_date: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                    min={importData.from_date}
                    max={new Date().toISOString().split('T')[0]}
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="force_refresh"
                    checked={importData.force_refresh}
                    onChange={(e) => setImportData({ ...importData, force_refresh: e.target.checked })}
                    className="mr-2"
                  />
                  <label htmlFor="force_refresh" className="text-sm">
                    Forzar re-importación (sobrescribir existentes)
                  </label>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
                  <p className="text-yellow-800">
                    ℹ️ Máximo: 2 años por solicitud. La importación inteligente solo descarga datos faltantes.
                  </p>
                </div>

                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowImportModal(false)}
                    className="px-4 py-2 border rounded hover:bg-gray-50"
                    disabled={isImporting}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleImportHistorical}
                    disabled={isImporting}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                  >
                    {isImporting ? 'Importando...' : 'Importar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Debug helper: show last click action */}

      </div>
    </Layout>
  )
}
