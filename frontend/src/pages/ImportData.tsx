import { useState } from 'react'
import api from '../services/api'
import Layout from '../components/Layout'

interface ImportStats {
  total: number
  created: number
  updated: number
  skipped: number
  errors: string[]
}

export default function ImportData() {
  const [activeTab, setActiveTab] = useState<'transactions' | 'quotes'>('transactions')
  const [portfolioId, setPortfolioId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<ImportStats | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setImportResult(null)
    }
  }

  const handleImportTransactions = async () => {
    if (!file || !portfolioId) {
      alert('Por favor selecciona un archivo e introduce el ID de la cartera')
      return
    }

    setIsImporting(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post(
        `/import-export/transactions/${portfolioId}/import?skip_duplicates=${skipDuplicates}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      setImportResult(response.data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al importar')
    } finally {
      setIsImporting(false)
    }
  }

  const handleImportQuotes = async () => {
    if (!file) {
      alert('Por favor selecciona un archivo')
      return
    }

    setIsImporting(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post(
        `/import-export/quotes/import?skip_duplicates=${skipDuplicates}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      setImportResult(response.data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al importar')
    } finally {
      setIsImporting(false)
    }
  }

  const handleDownloadTemplate = async (type: 'transactions' | 'quotes') => {
    try {
      const response = await api.get(`/import-export/templates/${type}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}_template.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      alert('Error al descargar la plantilla')
    }
  }

  return (
    <Layout>
      <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Importar Datos</h1>
        <p className="text-gray-600">Importa transacciones y cotizaciones desde archivos CSV</p>
      </div>

      {/* Pestañas */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('transactions')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'transactions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Transacciones
          </button>
          <button
            onClick={() => setActiveTab('quotes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'quotes'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Cotizaciones
          </button>
        </nav>
      </div>

      {/* Contenido */}
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Descargar Plantilla */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold mb-2">📄 Descargar Plantilla</h3>
          <p className="text-sm text-gray-600 mb-3">
            Descarga una plantilla CSV para ver el formato requerido
          </p>
          <button
            onClick={() => handleDownloadTemplate(activeTab)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Descargar Plantilla de {activeTab === 'transactions' ? 'Transacciones' : 'Cotizaciones'}
          </button>
        </div>

        {/* Formulario de Importación */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Importar {activeTab === 'transactions' ? 'Transacciones' : 'Cotizaciones'}</h3>

          {activeTab === 'transactions' && (
            <div>
              <label className="block text-sm font-medium mb-1">ID de Cartera *</label>
              <input
                type="text"
                value={portfolioId}
                onChange={(e) => setPortfolioId(e.target.value)}
                placeholder="Introduce el UUID de la cartera"
                className="w-full px-3 py-2 border rounded"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Archivo CSV *</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border rounded"
            />
            {file && (
              <p className="text-sm text-gray-600 mt-1">
                Seleccionado: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="skipDuplicates"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <label htmlFor="skipDuplicates" className="ml-2 text-sm">
              Omitir duplicados (recomendado)
            </label>
          </div>

          <button
            onClick={activeTab === 'transactions' ? handleImportTransactions : handleImportQuotes}
            disabled={isImporting || !file || (activeTab === 'transactions' && !portfolioId)}
            className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {isImporting ? 'Importando...' : `Importar ${activeTab === 'transactions' ? 'Transacciones' : 'Cotizaciones'}`}
          </button>
        </div>

        {/* Resultados de la Importación */}
        {importResult && (
          <div className="border-t pt-6">
            <h3 className="font-semibold text-lg mb-4">Resultados de la Importación</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-2xl font-bold text-gray-900">{importResult.total}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-2xl font-bold text-green-600">{importResult.created}</div>
                <div className="text-sm text-gray-600">Creados</div>
              </div>
              {importResult.updated > 0 && (
                <div className="bg-blue-50 p-4 rounded">
                  <div className="text-2xl font-bold text-blue-600">{importResult.updated}</div>
                  <div className="text-sm text-gray-600">Actualizados</div>
                </div>
              )}
              <div className="bg-yellow-50 p-4 rounded">
                <div className="text-2xl font-bold text-yellow-600">{importResult.skipped}</div>
                <div className="text-sm text-gray-600">Omitidos</div>
              </div>
            </div>

            {importResult.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-semibold text-red-900 mb-2">Errores ({importResult.errors.length})</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-800">
                  {importResult.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Información del Formato */}
        <div className="border-t pt-6">
          <h3 className="font-semibold text-lg mb-3">Información del Formato</h3>
          
          {activeTab === 'transactions' ? (
            <div className="bg-gray-50 p-4 rounded text-sm space-y-2">
              <p><strong>Columnas requeridas:</strong> date, type, asset_symbol, quantity, price</p>
              <p><strong>Columnas opcionales:</strong> fees, notes</p>
              <p><strong>Valores de tipo:</strong> BUY, SELL</p>
              <p><strong>Formato de fecha:</strong> YYYY-MM-DD</p>
              <p className="text-gray-600 italic">
                Ejemplo: 2025-01-15,BUY,AAPL,10,150.50,9.99,Compra inicial
              </p>
            </div>
          ) : (
            <div className="bg-gray-50 p-4 rounded text-sm space-y-2">
              <p><strong>Columnas requeridas:</strong> symbol, date, open, high, low, close</p>
              <p><strong>Columnas opcionales:</strong> volume, source</p>
              <p><strong>Formato de fecha:</strong> YYYY-MM-DD</p>
              <p className="text-gray-600 italic">
                Ejemplo: AAPL,2025-01-15,150.00,152.00,149.50,151.50,1000000,manual
              </p>
            </div>
          )}
        </div>
      </div>
      </div>
    </Layout>
  )
}
