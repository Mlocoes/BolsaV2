import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';
import type { Portfolio } from '../types/portfolio';
import Layout from '../components/Layout';
import { ArrowRight, Wallet } from 'lucide-react';

export default function TransactionsPortfolioSelection() {
    const navigate = useNavigate();
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadPortfolios();
    }, []);

    const loadPortfolios = async () => {
        try {
            const data = await portfolioService.getPortfolios();
            setPortfolios(data);
        } catch (error) {
            console.error('Error loading portfolios:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout>
            <div className="max-w-3xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">Gestionar Transacciones</h1>
                <p className="text-gray-600 mb-8">Selecciona un portafolio para gestionar sus transacciones.</p>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="text-gray-500">Cargando portafolios...</div>
                    </div>
                ) : portfolios.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-lg shadow">
                        <Wallet className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay portafolios</h3>
                        <p className="mt-1 text-sm text-gray-500">Crea un portafolio en el Panel de Control para comenzar.</p>
                    </div>
                ) : (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {portfolios.map((portfolio) => (
                            <button
                                key={portfolio.id}
                                onClick={() => navigate(`/portfolio/${portfolio.id}/transactions`)}
                                className="flex items-center justify-between p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left border border-transparent hover:border-indigo-500 group"
                            >
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900 group-hover:text-indigo-600">
                                        {portfolio.name}
                                    </h3>
                                    {portfolio.description && (
                                        <p className="mt-1 text-sm text-gray-500">{portfolio.description}</p>
                                    )}
                                </div>
                                <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-indigo-500" />
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    );
}
