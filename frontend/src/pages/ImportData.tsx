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
      alert('Please select a file and enter portfolio ID')
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
      alert(error.response?.data?.detail || 'Import failed')
    } finally {
      setIsImporting(false)
    }
  }

  const handleImportQuotes = async () => {
    if (!file) {
      alert('Please select a file')
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
      alert(error.response?.data?.detail || 'Import failed')
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
      alert('Failed to download template')
    }
  }

  return (
    <Layout>
      <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Import Data</h1>
        <p className="text-gray-600">Import transactions and quotes from CSV files</p>
      </div>

      {/* Tabs */}
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
            Transactions
          </button>
          <button
            onClick={() => setActiveTab('quotes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'quotes'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Quotes
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Template Download */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold mb-2">📄 Download Template</h3>
          <p className="text-sm text-gray-600 mb-3">
            Download a CSV template to see the required format
          </p>
          <button
            onClick={() => handleDownloadTemplate(activeTab)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Download {activeTab} Template
          </button>
        </div>

        {/* Import Form */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Import {activeTab}</h3>

          {activeTab === 'transactions' && (
            <div>
              <label className="block text-sm font-medium mb-1">Portfolio ID *</label>
              <input
                type="text"
                value={portfolioId}
                onChange={(e) => setPortfolioId(e.target.value)}
                placeholder="Enter portfolio UUID"
                className="w-full px-3 py-2 border rounded"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">CSV File *</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border rounded"
            />
            {file && (
              <p className="text-sm text-gray-600 mt-1">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
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
              Skip duplicates (recommended)
            </label>
          </div>

          <button
            onClick={activeTab === 'transactions' ? handleImportTransactions : handleImportQuotes}
            disabled={isImporting || !file || (activeTab === 'transactions' && !portfolioId)}
            className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {isImporting ? 'Importing...' : `Import ${activeTab}`}
          </button>
        </div>

        {/* Import Results */}
        {importResult && (
          <div className="border-t pt-6">
            <h3 className="font-semibold text-lg mb-4">Import Results</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-2xl font-bold text-gray-900">{importResult.total}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-2xl font-bold text-green-600">{importResult.created}</div>
                <div className="text-sm text-gray-600">Created</div>
              </div>
              {importResult.updated > 0 && (
                <div className="bg-blue-50 p-4 rounded">
                  <div className="text-2xl font-bold text-blue-600">{importResult.updated}</div>
                  <div className="text-sm text-gray-600">Updated</div>
                </div>
              )}
              <div className="bg-yellow-50 p-4 rounded">
                <div className="text-2xl font-bold text-yellow-600">{importResult.skipped}</div>
                <div className="text-sm text-gray-600">Skipped</div>
              </div>
            </div>

            {importResult.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-semibold text-red-900 mb-2">Errors ({importResult.errors.length})</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-800">
                  {importResult.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Format Information */}
        <div className="border-t pt-6">
          <h3 className="font-semibold text-lg mb-3">Format Information</h3>
          
          {activeTab === 'transactions' ? (
            <div className="bg-gray-50 p-4 rounded text-sm space-y-2">
              <p><strong>Required columns:</strong> date, type, asset_symbol, quantity, price</p>
              <p><strong>Optional columns:</strong> fees, notes</p>
              <p><strong>Type values:</strong> BUY, SELL</p>
              <p><strong>Date format:</strong> YYYY-MM-DD</p>
              <p className="text-gray-600 italic">
                Example: 2025-01-15,BUY,AAPL,10,150.50,9.99,Initial purchase
              </p>
            </div>
          ) : (
            <div className="bg-gray-50 p-4 rounded text-sm space-y-2">
              <p><strong>Required columns:</strong> symbol, date, open, high, low, close</p>
              <p><strong>Optional columns:</strong> volume, source</p>
              <p><strong>Date format:</strong> YYYY-MM-DD</p>
              <p className="text-gray-600 italic">
                Example: AAPL,2025-01-15,150.00,152.00,149.50,151.50,1000000,manual
              </p>
            </div>
          )}
        </div>
      </div>
      </div>
    </Layout>
  )
}
