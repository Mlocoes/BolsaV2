import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { portfolioService } from '../services/portfolioService';
import CreatePortfolioModal from '../components/CreatePortfolioModal';
import Layout from '../components/Layout';
import type { Portfolio } from '../types/portfolio';
import { Plus, Wallet, Trash2 } from 'lucide-react';

export default function Portfolios() {
  const { user, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/login');
      return;
    }
    if (user) {
      loadPortfolios();
    }
  }, [user, isLoading, navigate]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getPortfolios();
      setPortfolios(data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar portfolios');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePortfolio = async (data: { name: string; description?: string }) => {
    await portfolioService.createPortfolio(data);
    await loadPortfolios();
  };

  const handleDeletePortfolio = async (id: string) => {
    if (!confirm('¿Estás seguro de eliminar esta cartera?')) return;

    try {
      await portfolioService.deletePortfolio(id);
      await loadPortfolios();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al eliminar cartera');
    }
  };

  if (isLoading || !user) return null;

  return (
    <Layout>
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Mis Carteras</h2>
          <p className="mt-2 text-sm text-gray-600">
            Gestiona tus carteras de inversión
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="h-5 w-5 mr-2" />
          Nueva Cartera
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Cargando...</div>
        </div>
      ) : portfolios.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <Wallet className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No hay carteras</h3>
          <p className="mt-1 text-sm text-gray-500">
            Crea tu primera cartera para comenzar a gestionar tus inversiones.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Crear Primera Cartera
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {portfolios.map((portfolio) => (
            <div
              key={portfolio.id}
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <Wallet className="h-8 w-8 text-indigo-600" />
                    <h3 className="ml-3 text-lg font-medium text-gray-900">
                      {portfolio.name}
                    </h3>
                  </div>
                </div>

                {portfolio.description && (
                  <p className="text-sm text-gray-600 mb-4">
                    {portfolio.description}
                  </p>
                )}

                <div className="text-xs text-gray-500 mb-4">
                  Creado: {new Date(portfolio.created_at).toLocaleDateString('es-ES')}
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => navigate(`/?portfolio=${portfolio.id}`)}
                    className="flex-1 px-3 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded hover:bg-indigo-100"
                  >
                    Ver Detalles
                  </button>
                  <button
                    onClick={() => handleDeletePortfolio(portfolio.id)}
                    className="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded hover:bg-red-100"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <CreatePortfolioModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreatePortfolio}
      />
    </Layout>
  );
}
