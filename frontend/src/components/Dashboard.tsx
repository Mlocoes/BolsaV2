import { useEffect, useState, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { snapshotService, type PortfolioSnapshot } from '../services/snapshotService';
import type { Portfolio, PositionWithPrice } from '../types/portfolio';
import { Wallet, TrendingUp, TrendingDown, Plus, Camera } from 'lucide-react';
import AddTransactionModal from './AddTransactionModal';
import CreatePortfolioModal from './CreatePortfolioModal';
import PortfolioDistributionChart from './PortfolioDistributionChart';
import PerformanceChart from './PerformanceChart';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.min.css';

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<PositionWithPrice[]>([]);
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showCreatePortfolioModal, setShowCreatePortfolioModal] = useState(false);
  const hotTableRef = useRef<HTMLDivElement>(null);
  const hotInstance = useRef<Handsontable | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPositions(selectedPortfolio.id);
      loadSnapshots(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  useEffect(() => {
    if (selectedSnapshot && hotTableRef.current && !hotInstance.current) {
      initializeHandsontable();
    }
    if (selectedSnapshot && hotInstance.current) {
      updateHandsontableData();
    }
  }, [selectedSnapshot]);

  useEffect(() => {
    return () => {
      if (hotInstance.current) {
        hotInstance.current.destroy();
        hotInstance.current = null;
      }
    };
  }, []);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getPortfolios();
      setPortfolios(data);
      if (data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Error al cargar portfolios');
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async (portfolioId: string) => {
    try {
      const data = await portfolioService.getPortfolioPrices(portfolioId);
      setPositions(data);
    } catch (err: any) {
      console.error('Error loading positions:', err);
    }
  };

  const loadSnapshots = async (portfolioId: string) => {
    try {
      const history = await snapshotService.getHistory(portfolioId);
      setSnapshots(history);
      // Seleccionar el snapshot más reciente por defecto
      if (history.length > 0) {
        setSelectedSnapshot(history[0]);
      }
    } catch (err: any) {
      console.error('Error loading snapshots:', err);
      // Si no hay snapshots, intentar crear uno
      try {
        const newSnapshot = await snapshotService.createSnapshot(portfolioId);
        setSnapshots([newSnapshot]);
        setSelectedSnapshot(newSnapshot);
      } catch (createErr) {
        console.error('Error creating snapshot:', createErr);
      }
    }
  };

  const initializeHandsontable = () => {
    if (!hotTableRef.current || !selectedSnapshot) return;

    const data = selectedSnapshot.positions.map(p => ({
      symbol: p.symbol,
      name: p.name,
      asset_type: p.asset_type,
      quantity: p.quantity,
      average_price: p.average_price,
      current_price: p.current_price,
      current_value: p.current_value,
      cost_basis: p.cost_basis,
      profit_loss: p.profit_loss,
      profit_loss_percent: p.profit_loss_percent
    }));

    hotInstance.current = new Handsontable(hotTableRef.current, {
      data,
      colHeaders: [
        'Símbolo',
        'Nombre',
        'Tipo',
        'Cantidad',
        'Precio Promedio',
        'Precio Actual',
        'Valor Actual',
        'Costo Base',
        'Ganancia/Pérdida',
        'G/P %'
      ],
      columns: [
        { data: 'symbol', type: 'text', readOnly: true },
        { data: 'name', type: 'text', readOnly: true },
        { data: 'asset_type', type: 'text', readOnly: true },
        { data: 'quantity', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00' } },
        { data: 'average_price', type: 'numeric', readOnly: true, numericFormat: { pattern: '$0,0.00' } },
        { data: 'current_price', type: 'numeric', readOnly: true, numericFormat: { pattern: '$0,0.00' } },
        { data: 'current_value', type: 'numeric', readOnly: true, numericFormat: { pattern: '$0,0.00' } },
        { data: 'cost_basis', type: 'numeric', readOnly: true, numericFormat: { pattern: '$0,0.00' } },
        { 
          data: 'profit_loss', 
          type: 'numeric', 
          readOnly: true, 
          numericFormat: { pattern: '$0,0.00' },
          className: (row: number, col: number) => {
            const value = data[row]?.profit_loss || 0;
            return value >= 0 ? 'htPositive' : 'htNegative';
          }
        },
        { 
          data: 'profit_loss_percent', 
          type: 'numeric', 
          readOnly: true, 
          numericFormat: { pattern: '0.00%' },
          className: (row: number, col: number) => {
            const value = data[row]?.profit_loss_percent || 0;
            return value >= 0 ? 'htPositive' : 'htNegative';
          }
        }
      ],
      rowHeaders: true,
      width: '100%',
      height: 400,
      licenseKey: 'non-commercial-and-evaluation',
      stretchH: 'all',
      autoColumnSize: true,
      filters: true,
      dropdownMenu: true,
      columnSorting: true
    });
  };

  const updateHandsontableData = () => {
    if (!hotInstance.current || !selectedSnapshot) return;

    const data = selectedSnapshot.positions.map(p => ({
      symbol: p.symbol,
      name: p.name,
      asset_type: p.asset_type,
      quantity: p.quantity,
      average_price: p.average_price,
      current_price: p.current_price,
      current_value: p.current_value,
      cost_basis: p.cost_basis,
      profit_loss: p.profit_loss,
      profit_loss_percent: p.profit_loss_percent
    }));

    hotInstance.current.loadData(data);
  };

  const handleCreateSnapshot = async () => {
    if (!selectedPortfolio) return;
    try {
      const newSnapshot = await snapshotService.createSnapshot(selectedPortfolio.id);
      await loadSnapshots(selectedPortfolio.id);
      setSelectedSnapshot(newSnapshot);
    } catch (err: any) {
      console.error('Error creating snapshot:', err);
      alert('Error al crear snapshot: ' + err.message);
    }
  };

  const calculateTotals = () => {
    if (selectedSnapshot) {
      return {
        totalValue: selectedSnapshot.total_value,
        totalCost: selectedSnapshot.total_cost,
        totalProfitLoss: selectedSnapshot.total_profit_loss,
        totalProfitLossPercent: selectedSnapshot.total_profit_loss_percent
      };
    }
    
    const totalValue = positions.reduce((sum, p) => sum + p.current_value, 0);
    const totalCost = positions.reduce((sum, p) => sum + p.cost_basis, 0);
    const totalProfitLoss = totalValue - totalCost;
    const totalProfitLossPercent = totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0;

    return {
      totalValue,
      totalCost,
      totalProfitLoss,
      totalProfitLossPercent
    };
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return value.toFixed(2) + '%';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (portfolios.length === 0) {
    return (
      <div className="text-center py-12">
        <Wallet className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay portfolios</h3>
        <p className="mt-1 text-sm text-gray-500">Crea tu primer portfolio para comenzar.</p>
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setShowCreatePortfolioModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Crear Portfolio
          </button>
        </div>
      </div>
    );
  }

  const totals = calculateTotals();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Resumen de tus inversiones
        </p>
      </div>

      {/* Portfolio Selector and Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <label htmlFor="portfolio" className="text-sm font-medium text-gray-700">
            Portfolio:
          </label>
          <select
            id="portfolio"
            value={selectedPortfolio?.id || ''}
            onChange={(e) => {
              const portfolio = portfolios.find(p => p.id === e.target.value);
              setSelectedPortfolio(portfolio || null);
            }}
            className="block w-64 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            {portfolios.map(portfolio => (
              <option key={portfolio.id} value={portfolio.id}>
                {portfolio.name}
              </option>
            ))}
          </select>
        </div>
        
        {selectedPortfolio && (
          <button
            onClick={() => setShowTransactionModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <Plus className="h-5 w-5 mr-2" />
            Nueva Transacción
          </button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Wallet className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Valor Total
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {formatCurrency(totals.totalValue)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Wallet className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Costo Base
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {formatCurrency(totals.totalCost)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {totals.totalProfitLoss >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-500" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Ganancia/Pérdida
                  </dt>
                  <dd className={`text-lg font-semibold ${totals.totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(totals.totalProfitLoss)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {totals.totalProfitLossPercent >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-500" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Rendimiento %
                  </dt>
                  <dd className={`text-lg font-semibold ${totals.totalProfitLossPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(totals.totalProfitLossPercent)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      {(selectedSnapshot?.positions.length || positions.length) > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Distribución del Portfolio
              </h3>
            </div>
            <div className="p-6">
              <PortfolioDistributionChart 
                positions={selectedSnapshot ? selectedSnapshot.positions : positions} 
              />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Rendimiento por Activo
              </h3>
            </div>
            <div className="p-6">
              <PerformanceChart 
                positions={selectedSnapshot ? selectedSnapshot.positions : positions} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Posiciones - Snapshot
            </h3>
            <div className="flex items-center space-x-4">
              {snapshots.length > 0 && (
                <select
                  value={selectedSnapshot?.snapshot_date || ''}
                  onChange={(e) => {
                    const snapshot = snapshots.find(s => s.snapshot_date === e.target.value);
                    setSelectedSnapshot(snapshot || null);
                  }}
                  className="block rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  {snapshots.map(snapshot => (
                    <option key={snapshot.id} value={snapshot.snapshot_date}>
                      {new Date(snapshot.snapshot_date).toLocaleDateString('es-ES')}
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={handleCreateSnapshot}
                className="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
              >
                <Camera className="h-4 w-4 mr-1.5" />
                Crear Snapshot
              </button>
            </div>
          </div>
        </div>
        <div className="p-4">
          {selectedSnapshot ? (
            <div>
              <div ref={hotTableRef} />
              <style>{`
                .htPositive { color: #059669; font-weight: 600; }
                .htNegative { color: #DC2626; font-weight: 600; }
              `}</style>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No hay snapshots disponibles. Crea uno para ver el historial.
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {selectedPortfolio && (
        <AddTransactionModal
          isOpen={showTransactionModal}
          onClose={() => setShowTransactionModal(false)}
          portfolioId={selectedPortfolio.id}
          onSuccess={() => {
            loadPositions(selectedPortfolio.id);
          }}
        />
      )}

      <CreatePortfolioModal
        isOpen={showCreatePortfolioModal}
        onClose={() => setShowCreatePortfolioModal(false)}
        onSubmit={async (data) => {
          await portfolioService.createPortfolio(data);
          await loadPortfolios();
        }}
      />
    </div>
  );
}
