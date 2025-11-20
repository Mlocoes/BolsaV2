import { useState, useEffect } from 'react'
import api from '../services/api'
import Layout from '../components/Layout'

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
      // Obtener la última cotización de cada activo
      const response = await api.get('/quotes', {
        params: { limit: 1000 }
      })

      // Agrupar por símbolo y mantener solo la cotización más reciente de cada uno
      const quotesBySymbol = new Map<string, Quote>()
      response.data.forEach((quote: Quote) => {
        const existing = quotesBySymbol.get(quote.symbol)
        if (!existing || new Date(quote.date) > new Date(existing.date)) {
          quotesBySymbol.set(quote.symbol, quote)
        }
      })

      // Convertir a array y ordenar por símbolo
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
      const response = await api.get('/quotes', {
        params: {
          symbol: selectedAsset,
          start_date: startDate,
          end_date: endDate,
          limit: 1000
        }
      })

      // Ordenar por fecha descendente (más reciente primero)
      const sortedQuotes = response.data.sort((a: Quote, b: Quote) =>
        new Date(b.date).getTime() - new Date(a.date).getTime()
      )

      setQuotes(sortedQuotes)
    } catch (error) {
      console.error('Error al cargar cotizaciones:', error)
      alert('Error al cargar cotizaciones filtradas')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    loadFilteredQuotes()
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(value)
  }

  const getAssetName = (symbol: string) => {
    const asset = assets.find(a => a.symbol === symbol)
    return asset ? `${asset.name} (${symbol})` : symbol
  }

  return (
    <Layout>
      <div className="container-fluid">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h2>📊 Cotizaciones</h2>
        </div>

        {/* Filtros */}
        <div className="card mb-4">
          <div className="card-body">
            <div className="row g-3">
              {/* Selector de Activos */}
              <div className="col-md-4">
                <label htmlFor="assetSelect" className="form-label">Activo</label>
                <select
                  id="assetSelect"
                  className="form-select"
                  value={selectedAsset}
                  onChange={(e) => setSelectedAsset(e.target.value)}
                >
                  <option value="all">Todos los activos</option>
                  {assets.map(asset => (
                    <option key={asset.id} value={asset.symbol}>
                      {asset.name} ({asset.symbol})
                    </option>
                  ))}
                </select>
              </div>

              {/* Fecha Inicio */}
              <div className="col-md-3">
                <label htmlFor="startDate" className="form-label">Fecha Inicio</label>
                <input
                  type="date"
                  id="startDate"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  disabled={datesDisabled}
                />
              </div>

              {/* Fecha Fin */}
              <div className="col-md-3">
                <label htmlFor="endDate" className="form-label">Fecha Fin</label>
                <input
                  type="date"
                  id="endDate"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  disabled={datesDisabled}
                />
              </div>

              {/* Botón Buscar */}
              <div className="col-md-2 d-flex align-items-end">
                <button
                  className="btn btn-primary w-100"
                  onClick={handleSearch}
                  disabled={isLoading}
                >
                  {isLoading ? '🔄 Buscando...' : '🔍 Buscar'}
                </button>
              </div>
            </div>

            {selectedAsset === 'all' && (
              <div className="alert alert-info mt-3 mb-0">
                <small>
                  ℹ️ Mostrando las últimas cotizaciones registradas para todos los activos
                </small>
              </div>
            )}
          </div>
        </div>

        {/* Tabla de Cotizaciones */}
        <div className="card">
          <div className="card-body">
            <h5 className="card-title">
              Resultados {quotes.length > 0 && `(${quotes.length})`}
            </h5>

            {isLoading ? (
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Cargando...</span>
                </div>
              </div>
            ) : quotes.length === 0 ? (
              <div className="text-center text-muted py-5">
                <p>No se encontraron cotizaciones</p>
                <small>
                  {selectedAsset === 'all'
                    ? 'Presiona "Buscar" para cargar las últimas cotizaciones de todos los activos'
                    : 'Selecciona un rango de fechas y presiona "Buscar"'
                  }
                </small>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover table-striped">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Activo</th>
                      <th className="text-end">Cotización</th>
                      <th className="text-end">Apertura</th>
                      <th className="text-end">Máximo</th>
                      <th className="text-end">Mínimo</th>
                      <th className="text-end">Volumen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {quotes.map((quote, index) => (
                      <tr key={`${quote.symbol}-${quote.date}-${index}`}>
                        <td>{formatDate(quote.date)}</td>
                        <td>
                          <strong>{getAssetName(quote.symbol)}</strong>
                        </td>
                        <td className="text-end">
                          <strong>{formatCurrency(quote.close)}</strong>
                        </td>
                        <td className="text-end">
                          {quote.open ? formatCurrency(quote.open) : '-'}
                        </td>
                        <td className="text-end">
                          {quote.high ? formatCurrency(quote.high) : '-'}
                        </td>
                        <td className="text-end">
                          {quote.low ? formatCurrency(quote.low) : '-'}
                        </td>
                        <td className="text-end">
                          {quote.volume
                            ? new Intl.NumberFormat('es-ES').format(quote.volume)
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
