import { useState, useEffect } from 'react'
import { snapshotService } from '../services/snapshotService'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Calendar, BarChart3, RefreshCw } from 'lucide-react'
import { toast } from 'react-hot-toast'

interface PortfolioHistoryProps {
  portfolioId: string
}

interface Snapshot {
  date: string
  total_value: number
  total_invested: number
  total_pnl: number
  total_pnl_percent: number
  daily_pnl_percent: number
  number_of_positions: number
}

interface PerformanceMetrics {
  period_return: number
  current_value: number
  total_pnl: number
  total_pnl_percent: number
  best_day: {
    date: string
    return_percent: number
  }
  worst_day: {
    date: string
    return_percent: number
  }
  volatility: number
  number_of_days: number
}

export default function PortfolioHistory({ portfolioId }: PortfolioHistoryProps) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | '1y' | 'ytd' | 'all'>('30d')
  const [chartType, setChartType] = useState<'value' | 'pnl'>('value')
  const [isBackfilling, setIsBackfilling] = useState(false)

  useEffect(() => {
    loadHistory()
  }, [portfolioId, period])

  const loadHistory = async () => {
    setIsLoading(true)
    try {
      // Load snapshots
      const historyResponse = await snapshotService.getHistory(portfolioId);

      // Mapear PortfolioSnapshot a Snapshot
      const mappedSnapshots: Snapshot[] = historyResponse.map(s => ({
        date: s.date || s.snapshot_date || '',
        total_value: s.total_value || 0,
        total_invested: s.total_invested || s.total_cost || 0,
        total_pnl: s.total_pnl || s.total_profit_loss || 0,
        total_pnl_percent: s.total_pnl_percent || s.total_profit_loss_percent || 0,
        daily_pnl_percent: 0, // Calcular si es necesario
        number_of_positions: s.positions?.length || 0
      }));

      setSnapshots(mappedSnapshots);

      // Calcular métricas básicas
      if (mappedSnapshots.length > 0) {
        const latest = mappedSnapshots[0];

        setMetrics({
          period_return: latest.total_pnl_percent || 0,
          current_value: latest.total_value || 0,
          total_pnl: latest.total_pnl || 0,
          total_pnl_percent: latest.total_pnl_percent || 0,
          best_day: { date: '', return_percent: 0 },
          worst_day: { date: '', return_percent: 0 },
          volatility: 0,
          number_of_days: mappedSnapshots.length
        });
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        toast.error('No historical data available. Create a snapshot first.')
      } else {
        toast.error('Failed to load portfolio history')
      }
    } finally {
      setIsLoading(false)
    }
  }

  /* const calculateFromDate = (period: string): Date => {
    const today = new Date()
    switch (period) {
      case '7d':
        return new Date(today.setDate(today.getDate() - 7))
      case '30d':
        return new Date(today.setDate(today.getDate() - 30))
      case '90d':
        return new Date(today.setDate(today.getDate() - 90))
      case '1y':
        return new Date(today.setFullYear(today.getFullYear() - 1))
      case 'ytd':
        return new Date(today.getFullYear(), 0, 1)
      default:
        return new Date(today.setFullYear(today.getFullYear() - 3))
    }
  } */

  const handleBackfill = async () => {
    setIsBackfilling(true);
    toast.error('Backfill feature coming soon');
    setIsBackfilling(false);
    return;
    /*
    const fromDate = calculateFromDate(period).toISOString().split('T')[0]
    const toDate = new Date().toISOString().split('T')[0]

    if (!confirm(`Backfill snapshots from ${fromDate} to ${toDate}?`)) return

    setIsBackfilling(true)
    const toastId = toast.loading('Creating historical snapshots...')

    try {
      const response = await snapshotService.createSnapshot(portfolioId)

      toast.success(
        `Snapshot created`,
        { id: toastId, duration: 5000 }
      )

      // Reload history
      await loadHistory()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Backfill failed', { id: toastId })
    } finally {
      setIsBackfilling(false)
    }
    */
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Prepare chart data
  const chartData = snapshots.map((s) => ({
    date: formatDate(s.date),
    fullDate: s.date,
    'Portfolio Value': s.total_value,
    'Total Invested': s.total_invested,
    'P&L': s.total_pnl,
    'P&L %': s.total_pnl_percent,
  }))

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="rounded-lg border border-secondary-200 bg-white p-3 shadow-lg">
          <p className="mb-2 font-medium text-secondary-900">{data.fullDate}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {
                entry.name.includes('%')
                  ? formatPercent(entry.value)
                  : formatCurrency(entry.value)
              }
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-secondary-600">Loading history...</div>
      </div>
    )
  }

  if (snapshots.length === 0) {
    return (
      <div className="rounded-lg bg-white p-8 text-center shadow">
        <Calendar className="mx-auto mb-4 h-16 w-16 text-secondary-400" />
        <h3 className="mb-2 text-xl font-bold text-secondary-900">No Historical Data</h3>
        <p className="mb-6 text-secondary-600">
          Historical snapshots haven't been created yet for this portfolio.
        </p>
        <button
          onClick={handleBackfill}
          disabled={isBackfilling}
          className="inline-flex items-center space-x-2 rounded-lg bg-primary-600 px-6 py-3 font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {isBackfilling ? (
            <>
              <RefreshCw className="h-5 w-5 animate-spin" />
              <span>Creating Snapshots...</span>
            </>
          ) : (
            <>
              <BarChart3 className="h-5 w-5" />
              <span>Generate Historical Data</span>
            </>
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          {(['7d', '30d', '90d', '1y', 'ytd', 'all'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                period === p
                  ? 'bg-primary-600 text-white'
                  : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              {p.toUpperCase()}
            </button>
          ))}
        </div>

        <button
          onClick={handleBackfill}
          disabled={isBackfilling}
          className="flex items-center space-x-2 rounded-lg border border-secondary-300 px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isBackfilling ? 'animate-spin' : ''}`} />
          <span>Backfill</span>
        </button>
      </div>

      {/* Performance Metrics Cards */}
      {metrics && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg bg-white p-4 shadow">
            <p className="text-sm text-secondary-600">Period Return</p>
            <p className={`text-2xl font-bold ${
              metrics.period_return >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}>
              {formatPercent(metrics.period_return)}
            </p>
          </div>

          <div className="rounded-lg bg-white p-4 shadow">
            <p className="text-sm text-secondary-600">Best Day</p>
            <p className="text-2xl font-bold text-success-600">
              {formatPercent(metrics.best_day.return_percent)}
            </p>
            <p className="text-xs text-secondary-500">{metrics.best_day.date}</p>
          </div>

          <div className="rounded-lg bg-white p-4 shadow">
            <p className="text-sm text-secondary-600">Worst Day</p>
            <p className="text-2xl font-bold text-danger-600">
              {formatPercent(metrics.worst_day.return_percent)}
            </p>
            <p className="text-xs text-secondary-500">{metrics.worst_day.date}</p>
          </div>

          <div className="rounded-lg bg-white p-4 shadow">
            <p className="text-sm text-secondary-600">Volatility</p>
            <p className="text-2xl font-bold text-secondary-900">
              {metrics.volatility.toFixed(2)}%
            </p>
            <p className="text-xs text-secondary-500">{metrics.number_of_days} days</p>
          </div>
        </div>
      )}

      {/* Chart Type Selector */}
      <div className="flex justify-end space-x-2">
        <button
          onClick={() => setChartType('value')}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            chartType === 'value'
              ? 'bg-primary-600 text-white'
              : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
          }`}
        >
          Portfolio Value
        </button>
        <button
          onClick={() => setChartType('pnl')}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            chartType === 'pnl'
              ? 'bg-primary-600 text-white'
              : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
          }`}
        >
          P&L
        </button>
      </div>

      {/* Chart */}
      <div className="rounded-lg bg-white p-6 shadow">
        <ResponsiveContainer width="100%" height={400}>
          {chartType === 'value' ? (
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="Total Invested"
                stroke="#94a3b8"
                fill="#cbd5e1"
                fillOpacity={0.3}
              />
              <Area
                type="monotone"
                dataKey="Portfolio Value"
                stroke="#0ea5e9"
                fill="#0ea5e9"
                fillOpacity={0.5}
              />
            </AreaChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="P&L"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="P&L %"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Daily Performance Table */}
      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-secondary-200 px-6 py-4">
          <h3 className="font-bold text-secondary-900">Daily Performance</h3>
        </div>
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full">
            <thead className="sticky top-0 bg-secondary-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-secondary-700">
                  Date
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-secondary-700">
                  Value
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-secondary-700">
                  Daily Change
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-secondary-700">
                  Total P&L
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-secondary-700">
                  Positions
                </th>
              </tr>
            </thead>
            <tbody>
              {[...snapshots].reverse().map((snapshot, index) => (
                <tr
                  key={index}
                  className="border-b border-secondary-100 hover:bg-secondary-50"
                >
                  <td className="px-6 py-3 text-sm text-secondary-900">
                    {new Date(snapshot.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3 text-right text-sm text-secondary-900">
                    {formatCurrency(snapshot.total_value)}
                  </td>
                  <td className={`px-6 py-3 text-right text-sm font-medium ${
                    snapshot.daily_pnl_percent >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    {snapshot.daily_pnl_percent >= 0 ? <TrendingUp className="inline h-4 w-4 mr-1" /> : <TrendingDown className="inline h-4 w-4 mr-1" />}
                    {formatPercent(snapshot.daily_pnl_percent)}
                  </td>
                  <td className={`px-6 py-3 text-right text-sm font-medium ${
                    snapshot.total_pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    {formatCurrency(snapshot.total_pnl)} ({formatPercent(snapshot.total_pnl_percent)})
                  </td>
                  <td className="px-6 py-3 text-right text-sm text-secondary-600">
                    {snapshot.number_of_positions}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}