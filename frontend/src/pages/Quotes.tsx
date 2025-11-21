import { useState, useEffect, useRef } from 'react'
import { HotTable } from '@handsontable/react-wrapper'
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

  useEffect(() => {
    loadAssets()
  }, [])

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

  const loadLatestQuotes = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/quotes', {
        params: { limit: 1000 }
      })
      
      const quotesBySymbol = new Map<string, Quote>()
      response.data.forEach((quote: Quote) => {
        const existing = quotesBySymbol.get(quote.symbol)
        if (!existing || new Date(quote.date) > new Date(existing.date)) {
          quotesBySymbol.set(quote.symbol, quote)
        }
      })
      
      const latestQuotes = Array.from(quotesBySymbol.values()).sort((a, b) => 
        a.symbol.localeCompare(b.symbol)
      )
      
      setQuotes(latestQuotes)
    } catch (error) {
      console.error('Error al cargar cotizaciones:', error)
      alert('Error al cargar cotizaciones')
    } finally {
      setIsLoading(false)
    }
  }

  const loadFilteredQuotes = async () => {
    if (selectedAsset === 'all') {
      loadLatestQuotes()
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

      const sortedQuotes = response.data.sort((a: Quote, b: Quote) => 
        new Date(b.date).getTime() - new Date(a.date).getTime()
      )
      
      setQuotes(sortedQuotes)
    } catch (error) {
      console.error('Error al cargar cotizaciones:', error)
      alert('Error al cargar cotizaciones')
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
    minimo: quote.low || null,
    volumen: quote.volume || null
  }))

  const columns = [
    { data: 'fecha', title: 'Fecha', readOnly: true, width: 120 },
    { data: 'activo', title: 'Activo', readOnly: true, width: 200 },
    { 
      data: 'cotizacion', 
      title: 'Cotización', 
      type: 'numeric',
      numericFormat: { pattern: '$0,0.00' },
      readOnly: true,
      width: 120,
      className: 'htRight htBold'
    },
    { 
      data: 'apertura', 
      title: 'Apertura', 
      type: 'numeric',
      numericFormat: { pattern: '$0,0.00' },
      readOnly: true,
      width: 120,
      className: 'htRight'
    },
    { 
      data: 'maximo', 
      title: 'Máximo', 
      type: 'numeric',
      numericFormat: { pattern: '$0,0.00' },
      readOnly: true,
      width: 120,
      className: 'htRight'
    },
    { 
      data: 'minimo', 
      title: 'Mínimo', 
      type: 'numeric',
      numericFormat: { pattern: '$0,0.00' },
      readOnly: true,
      width: 120,
      className: 'htRight'
    },
    { 
      data: 'volumen', 
      title: 'Volumen', 
      type: 'numeric',
      numericFormat: { pattern: '0,0' },
      readOnly: true,
      width: 150,
      className: 'htRight'
    }
  ]

  return (
    <Layout>
      <div className="container mx-auto p-6 space-y-6">
        {/* Cabecera */}
        <div>
          <h1 className="text-3xl font-bold">Cotizaciones</h1>
          <p className="text-gray-600">Consulta el histórico de cotizaciones de los activos</p>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow p-6">
          <h5 className="text-lg font-semibold mb-4">Filtros</h5>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Selector de Activo */}
            <div>
              <label className="block text-sm font-medium mb-1">Activo</label>
              <select
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
              <label className="block text-sm font-medium mb-1">Fecha Inicio</label>
              <input
                type="date"
                className="w-full px-3 py-2 border rounded"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={datesDisabled}
              />
            </div>

            {/* Fecha Fin */}
            <div>
              <label className="block text-sm font-medium mb-1">Fecha Fin</label>
              <input
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
        <div className="bg-white rounded-lg shadow p-6">
          <h5 className="text-lg font-semibold mb-4">
            Resultados {quotes.length > 0 && `(${quotes.length})`}
          </h5>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Cargando...</p>
            </div>
          ) : quotes.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              <p>No se encontraron cotizaciones</p>
              <small className="text-gray-400">
                {selectedAsset === 'all' 
                  ? 'Presiona "Buscar" para cargar las últimas cotizaciones de todos los activos'
                  : 'Selecciona un rango de fechas y presiona "Buscar"'
                }
              </small>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <HotTable
                ref={hotTableRef}
                data={tableData}
                columns={columns}
                colHeaders={true}
                rowHeaders={true}
                height="500"
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
