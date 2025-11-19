import { useEffect, useState, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { snapshotService, type PortfolioSnapshot } from '../services/snapshotService';
import type { Portfolio, PositionWithPrice } from '../types/portfolio';
import { Wallet, TrendingUp, TrendingDown, Plus } from 'lucide-react';
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
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
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
      loadAvailableDates(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  useEffect(() => {
    if (selectedDate && selectedPortfolio) {
      loadSnapshotByDate(selectedPortfolio.id, selectedDate);
    }
  }, [selectedDate]);

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

  const loadAvailableDates = async (portfolioId: string) => {
    try {
      const dates = await snapshotService.getAvailableDates(portfolioId);
      setAvailableDates(dates);
      // Seleccionar la fecha más reciente por defecto
      if (dates.length > 0) {
        setSelectedDate(dates[0]);
      } else {
        // Si no hay fechas, intentar crear un snapshot para hoy
        try {
          await snapshotService.createSnapshot(portfolioId);
          // Recargar fechas
          const updatedDates = await snapshotService.getAvailableDates(portfolioId);
          setAvailableDates(updatedDates);
          if (updatedDates.length > 0) {
            setSelectedDate(updatedDates[0]);
          }
        } catch (createErr) {
          console.error('Error creating initial snapshot:', createErr);
        }
      }
    } catch (err: any) {
      console.error('Error loading available dates:', err);
    }
  };

  const loadSnapshotByDate = async (portfolioId: string, date: string) => {
    try {
      const snapshot = await snapshotService.getByDate(portfolioId, date);
      setSelectedSnapshot(snapshot);
    } catch (err: any) {
      console.error('Error loading snapshot by date:', err);
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
          renderer: function(instance: any, td: HTMLTableCellElement, row: number, col: number, prop: any, value: any, cellProperties: any) {
            Handsontable.renderers.NumericRenderer.apply(this, [instance, td, row, col, prop, value, cellProperties]);
            if (value >= 0) {
              td.classList.add('htPositive');
            } else {
              td.classList.add('htNegative');
            }
            return td;
          }
        },
        { 
          data: 'profit_loss_percent', 
          type: 'numeric', 
          readOnly: true, 
          numericFormat: { pattern: '0.00%' },
          renderer: function(instance: any, td: HTMLTableCellElement, row: number, col: number, prop: any, value: any, cellProperties: any) {
            Handsontable.renderers.NumericRenderer.apply(this, [instance, td, row, col, prop, value, cellProperties]);
            if (value >= 0) {
              td.classList.add('htPositive');
            } else {
              td.classList.add('htNegative');
            }
            return td;
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

  const calculateTotals = () => {
    if (selectedSnapshot) {
      return {
        totalValue: selectedSnapshot.total_value || 0,
        totalCost: selectedSnapshot.total_invested || selectedSnapshot.total_cost || 0,
        totalProfitLoss: selectedSnapshot.total_pnl || selectedSnapshot.total_profit_loss || 0,
        totalProfitLossPercent: selectedSnapshot.total_pnl_percent || selectedSnapshot.total_profit_loss_percent || 0
      };
    }
    
    const totalValue = positions.reduce((sum, p) => sum + (p.current_value || 0), 0);
    const totalCost = positions.reduce((sum, p) => sum + (p.cost_basis || 0), 0);
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

  const formatPercent = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) return '0.00%';
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
                positions={selectedSnapshot ? selectedSnapshot.positions.map(p => ({...p, position_id: '', asset_id: '', change_percent: 0})) : positions} 
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
                positions={selectedSnapshot ? selectedSnapshot.positions.map(p => ({...p, position_id: '', asset_id: '', change_percent: 0})) : positions} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Histórico de Posiciones
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Visualiza el estado de tu cartera en diferentes fechas
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {availableDates.length > 0 && (
                <div className="flex flex-col">
                  <label className="text-xs text-gray-500 mb-1">Fecha:</label>
                  <select
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="block rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2"
                  >
                    {availableDates.map(date => (
                      <option key={date} value={date}>
                        {new Date(date).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="p-4">
          {selectedSnapshot ? (
            <div>
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      📸 Visualizando snapshot del {new Date(selectedSnapshot.date || selectedSnapshot.snapshot_date || '').toLocaleDateString('es-ES', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      {selectedSnapshot.positions.length} posiciones | 
                      Valor Total: ${selectedSnapshot.total_value.toLocaleString('es-ES', {minimumFractionDigits: 2})} | 
                      G/P: ${(selectedSnapshot.total_pnl || selectedSnapshot.total_profit_loss || 0).toLocaleString('es-ES', {minimumFractionDigits: 2})} 
                      ({(selectedSnapshot.total_pnl_percent || selectedSnapshot.total_profit_loss_percent || 0) >= 0 ? '+' : ''}{(selectedSnapshot.total_pnl_percent || selectedSnapshot.total_profit_loss_percent || 0).toFixed(2)}%)
                    </p>
                  </div>
                  {selectedSnapshot.created_at && (
                    <div className="text-xs text-blue-600">
                      Creado: {new Date(selectedSnapshot.created_at).toLocaleTimeString('es-ES')}
                    </div>
                  )}
                </div>
              </div>
              <div ref={hotTableRef} />
              <style>{`
                .htPositive { color: #059669; font-weight: 600; }
                .htNegative { color: #DC2626; font-weight: 600; }
              `}</style>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p className="mb-2">No hay datos históricos disponibles para esta cartera.</p>
              <p className="text-sm">El sistema crea automáticamente snapshots diarios de tus posiciones.</p>
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
