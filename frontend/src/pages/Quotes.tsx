import { useState, useEffect, useRef } from 'react'
import { HotTable } from '@handsontable/react'
import { registerAllModules } from 'handsontable/registry'
import { registerLanguageDictionary, esMX } from 'handsontable/i18n'
import 'handsontable/dist/handsontable.full.min.css'
import '../styles/handsontable-custom.css'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'
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
}

interface Quote {
  symbol: string
  date: string
  close: number
  open?: number
  high?: number
  low?: number
  volume?: number
}

export default function Quotes() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [quotes, setQuotes] = useState<Quote[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState<string>('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [datesDisabled, setDatesDisabled] = useState(true)
  const hotTableRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadAssets()
  }, [])

  // Auto-load latest quotes when assets are available and currently showing 'all'
  useEffect(() => {
    if (assets.length > 0 && selectedAsset === 'all') {
      loadLatestQuotes(assets)
    }
  }, [assets, selectedAsset])

  useEffect(() => {
    if (selectedAsset === 'all') {
      setDatesDisabled(true)
      setStartDate('')
      setEndDate('')
    } else {
      setDatesDisabled(false)
    }
  }, [selectedAsset])

  const loadAssets = async () => {
    try {
      const response = await api.get('/assets')
      setAssets(response.data)
    } catch (error) {
      console.error('Error al cargar activos:', error)
      alert('Error al cargar activos')
    }
  }

  const loadLatestQuotes = async (currentAssets: Asset[]) => {
    setIsLoading(true)
    try {
      const response = await api.get('/quotes', {
        params: { limit: 1000 }
      })

      // Mapear respuesta del backend al formato interno
      // El backend devuelve: { asset_id, timestamp, close, ... }
      // Necesitamos: { symbol, date, close, ... }
      const mappedQuotes: Quote[] = response.data.map((q: any) => {
        const asset = currentAssets.find(a => a.id === q.asset_id)
        return {
          symbol: asset ? asset.symbol : 'UNKNOWN',
          date: q.timestamp,
          close: q.close,
          open: q.open,
          high: q.high,
          low: q.low,
          volume: q.volume
        }
      })

      const quotesBySymbol = new Map<string, Quote>()
      mappedQuotes.forEach((quote) => {
        const existing = quotesBySymbol.get(quote.symbol)
        if (!existing || new Date(quote.date) > new Date(existing.date)) {
          quotesBySymbol.set(quote.symbol, quote)
        }
      })

      const latestQuotes = Array.from(quotesBySymbol.values()).sort((a, b) =>
        a.symbol.localeCompare(b.symbol)
      )

      setQuotes(latestQuotes)
    } catch (error: any) {
      console.error('Error al cargar cotizaciones:', error)
      if (error.response?.status === 401) {
        alert('Sesión expirada. Por favor inicia sesión de nuevo.')
        navigate('/login', { replace: true })
      } else {
        alert('Error al cargar cotizaciones')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const loadFilteredQuotes = async () => {
    if (selectedAsset === 'all') {
      loadLatestQuotes(assets)
      return
    }

    if (!startDate || !endDate) {
      alert('Por favor, selecciona las fechas de inicio y fin')
      return
    }

    if (new Date(startDate) > new Date(endDate)) {
      alert('La fecha de inicio debe ser anterior a la fecha de fin')
      return
    }

    setIsLoading(true)
    try {
      const asset = assets.find(a => a.id === selectedAsset)
      if (!asset) return

      const response = await api.get('/quotes', {
        params: {
          symbol: asset.symbol,
          start_date: startDate,
          end_date: endDate,
          limit: 10000
        }
      })

      // Mapear respuesta del backend
      const mappedQuotes: Quote[] = response.data.map((q: any) => ({
        symbol: asset.symbol, // Ya conocemos el símbolo porque filtramos por él
        date: q.timestamp,
        close: q.close,
        open: q.open,
        high: q.high,
        low: q.low,
        volume: q.volume
      }))

      const sortedQuotes = mappedQuotes.sort((a, b) =>
        new Date(b.date).getTime() - new Date(a.date).getTime()
      )

      setQuotes(sortedQuotes)
    } catch (error: any) {
      console.error('Error al cargar cotizaciones:', error)
      if (error.response?.status === 401) {
        alert('Sesión expirada. Por favor inicia sesión de nuevo.')
        navigate('/login', { replace: true })
      } else {
        alert('Error al cargar cotizaciones')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    loadFilteredQuotes()
  }

  const getAssetName = (symbol: string) => {
    const asset = assets.find(a => a.symbol === symbol)
    return asset ? `${asset.symbol} - ${asset.name}` : symbol
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }

  // Preparar datos para Handsontable
  const tableData = quotes.map(quote => ({
    fecha: formatDate(quote.date),
    activo: getAssetName(quote.symbol),
    cotizacion: quote.close,
    apertura: quote.open || null,
    maximo: quote.high || null,
    minimo: quote.low || null
  }))

  const columns = [
    { data: 'fecha', title: 'Fecha', readOnly: true, width: 120 },
    { data: 'activo', title: 'Activo', readOnly: true, width: 200 },
    {
      data: 'cotizacion',
      title: 'Cotización',
      type: 'numeric',
      readOnly: true,
      width: 120,
      className: 'htRight htBold'
    },
    {
      data: 'apertura',
      title: 'Apertura',
      type: 'numeric',
      readOnly: true,
      width: 120,
      className: 'htRight'
    },
    {
      data: 'maximo',
      title: 'Máximo',
      type: 'numeric',
      readOnly: true,
      width: 120,
      className: 'htRight'
    },
    {
      data: 'minimo',
      title: 'Mínimo',
      type: 'numeric',
      readOnly: true,
      width: 120,
      className: 'htRight'
    }
  ]

  return (
    <Layout>
      <div className="flex flex-col h-full overflow-hidden space-y-4">
        {/* Cabecera */}
        <div className="flex-shrink-0">
          <h1 className="text-3xl font-bold">Cotizaciones</h1>
          <p className="text-gray-600">Consulta el histórico de cotizaciones de los activos</p>
        </div>

        {/* Filtros */}
        <div className="flex-shrink-0 bg-white rounded-lg shadow p-6">
          <h5 className="text-lg font-semibold mb-4">Filtros</h5>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Selector de Activo */}
            <div>
              <label htmlFor="quotes-asset-select" className="block text-sm font-medium mb-1">Activo</label>
              <select
                id="quotes-asset-select"
                name="asset"
                className="w-full px-3 py-2 border rounded"
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
              >
                <option value="all">📊 Todas las Cotizaciones Actuales</option>
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.symbol} - {asset.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Fecha Inicio */}
            <div>
              <label htmlFor="quotes-start-date" className="block text-sm font-medium mb-1">Fecha Inicio</label>
              <input
                id="quotes-start-date"
                name="startDate"
                type="date"
                className="w-full px-3 py-2 border rounded"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={datesDisabled}
              />
            </div>

            {/* Fecha Fin */}
            <div>
              <label htmlFor="quotes-end-date" className="block text-sm font-medium mb-1">Fecha Fin</label>
              <input
                id="quotes-end-date"
                name="endDate"
                type="date"
                className="w-full px-3 py-2 border rounded"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={datesDisabled}
              />
            </div>

            {/* Botón Buscar */}
            <div className="md:col-span-2 flex items-end">
              <button
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                onClick={handleSearch}
                disabled={isLoading}
              >
                {isLoading ? '🔄 Buscando...' : '🔍 Buscar'}
              </button>
            </div>
          </div>

          {selectedAsset === 'all' && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
              ℹ️ Mostrando las últimas cotizaciones registradas para todos los activos
            </div>
          )}
        </div>

        {/* Tabla con Handsontable */}
        <div className="flex-1 bg-white rounded-lg shadow p-4" style={{ minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Cargando...</p>
              </div>
            </div>
          ) : quotes.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p>No se encontraron cotizaciones</p>
                <small className="text-gray-400">
                  {selectedAsset === 'all'
                    ? 'Las cotizaciones se cargan automáticamente'
                    : 'Selecciona un rango de fechas y presiona "Buscar"'
                  }
                </small>
              </div>
            </div>
          ) : (
            <div style={{ height: '350px', width: '100%' }}>
              <HotTable
                ref={hotTableRef}
                data={tableData}
                columns={columns}
                colHeaders={true}
                rowHeaders={true}
                height={350}
                licenseKey="non-commercial-and-evaluation"
                stretchH="all"
                autoWrapRow={true}
                autoWrapCol={true}
                filters={true}
                dropdownMenu={true}
                columnSorting={true}
                manualColumnResize={true}
                contextMenu={true}
                language="es-ES"
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
