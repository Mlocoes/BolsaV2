import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';
import type { Portfolio, PositionWithPrice } from '../types/portfolio';
import { Wallet, TrendingUp, TrendingDown, List } from 'lucide-react';
import CreatePortfolioModal from './CreatePortfolioModal';
import PortfolioDistributionChart from './PortfolioDistributionChart';
import PerformanceChart from './PerformanceChart';



export default function Dashboard() {
  const navigate = useNavigate();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<PositionWithPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreatePortfolioModal, setShowCreatePortfolioModal] = useState(false);

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPositions(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getPortfolios();
      setPortfolios(data);
      if (data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Error al cargar carteras');
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



  /**
   * Calcula los totales de la cartera
   */
  const calculateTotals = () => {
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
    // Usar formato español (España)
    return new Intl.NumberFormat('es-ES', {
      style: 'decimal', // Usamos decimal para evitar el símbolo de moneda si no es deseado, o 'currency' con 'EUR'
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) return '0,00%';
    // Reemplazar punto por coma para decimales
    return value.toFixed(2).replace('.', ',') + '%';
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
        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay carteras</h3>
        <p className="mt-1 text-sm text-gray-500">Crea tu primera cartera para comenzar.</p>
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setShowCreatePortfolioModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Crear Cartera
          </button>
        </div>
      </div>
    );
  }

  const totals = calculateTotals();

  return (
    <div className="h-full flex flex-col space-y-2 md:space-y-3">
      {/* Header - compacto */}
      <div className="flex-shrink-0">
        <h1 className="text-xl md:text-2xl font-bold text-gray-900">Panel de Control</h1>
        <p className="text-xs md:text-sm text-gray-600">
          Resumen de tus inversiones
        </p>
      </div>

      {/* Portfolio Selector and Actions - compacto */}
      <div className="flex-shrink-0 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div className="flex items-center space-x-2 md:space-x-4">
          <label htmlFor="portfolio" className="text-xs md:text-sm font-medium text-gray-700">
            Cartera:
          </label>
          <select
            id="portfolio"
            value={selectedPortfolio?.id || ''}
            onChange={(e) => {
              const portfolio = portfolios.find(p => p.id === e.target.value);
              setSelectedPortfolio(portfolio || null);
            }}
            className="block w-40 md:w-64 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs md:text-sm"
          >
            {portfolios.map(portfolio => (
              <option key={portfolio.id} value={portfolio.id}>
                {portfolio.name}
              </option>
            ))}
          </select>
        </div>

        {selectedPortfolio && (
          <div className="flex space-x-2">
            <button
              onClick={() => navigate(`/portfolio/${selectedPortfolio.id}/bulk-edit`)}
              className="inline-flex items-center px-2 py-1 md:px-4 md:py-2 border border-gray-300 shadow-sm text-xs md:text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <TrendingUp className="h-4 w-4 md:h-5 md:w-5 md:mr-2" />
              <span className="hidden md:inline">Edición Masiva</span>
            </button>
            <button
              onClick={() => navigate(`/portfolio/${selectedPortfolio.id}/transactions`)}
              className="inline-flex items-center px-2 py-1 md:px-4 md:py-2 border border-transparent shadow-sm text-xs md:text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <List className="h-4 w-4 md:h-5 md:w-5 md:mr-2" />
              <span className="hidden md:inline">Gestionar Transacciones</span>
            </button>
          </div>
        )}
      </div>

      {/* Summary Cards - altura fija */}
      <div className="flex-shrink-0 grid grid-cols-2 lg:grid-cols-4 gap-2 md:gap-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-2 md:p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Wallet className="h-4 w-4 md:h-6 md:w-6 text-gray-400" />
              </div>
              <div className="ml-2 md:ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs md:text-sm font-medium text-gray-500 truncate">
                    Valor Total
                  </dt>
                  <dd className="text-sm md:text-lg font-semibold text-gray-900">
                    {formatCurrency(totals.totalValue)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-2 md:p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Wallet className="h-4 w-4 md:h-6 md:w-6 text-gray-400" />
              </div>
              <div className="ml-2 md:ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs md:text-sm font-medium text-gray-500 truncate">
                    Costo Base
                  </dt>
                  <dd className="text-sm md:text-lg font-semibold text-gray-900">
                    {formatCurrency(totals.totalCost)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-2 md:p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {totals.totalProfitLoss >= 0 ? (
                  <TrendingUp className="h-4 w-4 md:h-6 md:w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 md:h-6 md:w-6 text-red-500" />
                )}
              </div>
              <div className="ml-2 md:ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs md:text-sm font-medium text-gray-500 truncate">
                    Ganancia/Pérdida
                  </dt>
                  <dd className={`text-sm md:text-lg font-semibold ${totals.totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(totals.totalProfitLoss)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-2 md:p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {totals.totalProfitLossPercent >= 0 ? (
                  <TrendingUp className="h-4 w-4 md:h-6 md:w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 md:h-6 md:w-6 text-red-500" />
                )}
              </div>
              <div className="ml-2 md:ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs md:text-sm font-medium text-gray-500 truncate">
                    Rendimiento %
                  </dt>
                  <dd className={`text-sm md:text-lg font-semibold ${totals.totalProfitLossPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(totals.totalProfitLossPercent)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts - altura flexible */}
      {positions.length > 0 && (
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-2 md:gap-3">
          <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
            <div className="flex-shrink-0 px-2 py-2 md:px-4 md:py-3 border-b border-gray-200">
              <h3 className="text-sm md:text-base font-medium text-gray-900">
                Distribución de la Cartera
              </h3>
            </div>
            <div className="flex-1 min-h-0 p-2 md:p-4">
              <PortfolioDistributionChart positions={positions} />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
            <div className="flex-shrink-0 px-2 py-2 md:px-4 md:py-3 border-b border-gray-200">
              <h3 className="text-sm md:text-base font-medium text-gray-900">
                Rendimiento por Activo
              </h3>
            </div>
            <div className="flex-1 min-h-0 p-2 md:p-4">
              <PerformanceChart positions={positions} />
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
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
