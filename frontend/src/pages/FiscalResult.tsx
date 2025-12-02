import { useState, useEffect, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { fiscalService, FiscalResultResponse } from '../services/fiscalService';
import type { Portfolio } from '../types/portfolio';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.min.css';
import { registerLanguageDictionary, esMX } from 'handsontable/i18n';
import numbro from 'numbro';
import esES from 'numbro/dist/languages/es-ES.min.js';
import { Calculator, Calendar, Wallet } from 'lucide-react';
import Layout from '../components/Layout';

// Registrar idioma en numbro
numbro.registerLanguage(esES);
numbro.setLanguage('es-ES');

// Crear diccionario para es-ES basado en es-MX
const esESDictionary = { ...esMX, languageCode: 'es-ES' };
registerLanguageDictionary(esESDictionary);

export default function FiscalResult() {
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');
    const [results, setResults] = useState<FiscalResultResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const hotTableRef = useRef<HTMLDivElement>(null);
    const hotInstance = useRef<Handsontable | null>(null);

    useEffect(() => {
        loadPortfolios();
    }, []);

    useEffect(() => {
        if (results && hotTableRef.current && !hotInstance.current) {
            initializeHandsontable();
        }
        if (results && hotInstance.current) {
            updateHandsontableData();
        }
    }, [results]);

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
            const data = await portfolioService.getPortfolios();
            setPortfolios(data);
            if (data.length > 0) {
                setSelectedPortfolio(data[0]);
            }
        } catch (err: any) {
            setError(err.message || 'Error al cargar carteras');
        }
    };

    const calculateResults = async () => {
        if (!selectedPortfolio) return;

        setLoading(true);
        setError(null);
        try {
            const data = await fiscalService.getFiscalResults(
                selectedPortfolio.id,
                startDate || undefined,
                endDate || undefined
            );
            setResults(data);
        } catch (err: any) {
            setError(err.message || 'Error al calcular resultados fiscales');
            setResults(null);
        } finally {
            setLoading(false);
        }
    };

    const initializeHandsontable = () => {
        if (!hotTableRef.current || !results) return;

        hotInstance.current = new Handsontable(hotTableRef.current, {
            data: results.items,
            language: 'es-ES',
            colHeaders: [
                'Símbolo',
                'Fecha Venta',
                'Fecha Compra',
                'Cantidad',
                'Precio Venta',
                'Precio Compra',
                'Resultado'
            ],
            columns: [
                {
                    data: 'symbol',
                    type: 'text',
                    readOnly: true,
                    width: 80
                },
                {
                    data: 'date_sell',
                    type: 'date',
                    dateFormat: 'DD/MM/YYYY',
                    readOnly: true,
                    width: 100
                },
                {
                    data: 'date_buy',
                    type: 'date',
                    dateFormat: 'DD/MM/YYYY',
                    readOnly: true,
                    width: 100
                },
                {
                    data: 'quantity',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    readOnly: true,
                    width: 90
                },
                {
                    data: 'price_sell',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    readOnly: true,
                    width: 100
                },
                {
                    data: 'price_buy',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    readOnly: true,
                    width: 100
                },
                {
                    data: 'result',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    readOnly: true,
                    width: 110,
                    renderer: function (instance: any, td: HTMLTableCellElement, row: number, col: number, prop: any, value: any, cellProperties: any) {
                        Handsontable.renderers.NumericRenderer.apply(this, [instance, td, row, col, prop, value, cellProperties]);
                        if (value > 0) {
                            td.classList.add('htPositive');
                        } else if (value < 0) {
                            td.classList.add('htNegative');
                        }
                        return td;
                    }
                }
            ],
            rowHeaders: false,
            width: '100%',
            height: 450,
            licenseKey: 'non-commercial-and-evaluation',
            stretchH: 'none',
            autoColumnSize: false,
            filters: true,
            dropdownMenu: true,
            columnSorting: true,
            manualColumnResize: true
        });
    };

    const updateHandsontableData = () => {
        if (!hotInstance.current || !results) return;
        hotInstance.current.loadData(results.items);
    };

    if (portfolios.length === 0 && !loading) {
        return (
            <Layout>
                <div className="text-center py-12">
                    <Wallet className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No hay carteras</h3>
                    <p className="mt-1 text-sm text-gray-500">Crea una cartera desde el Panel de Control para comenzar.</p>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="h-full flex flex-col space-y-4">
                <div className="flex-shrink-0">
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Calculator className="h-6 w-6" />
                        Resultado Fiscal (FIFO)
                    </h1>
                    <p className="text-sm text-gray-600">
                        Calcula tus ganancias y pérdidas realizadas según el método FIFO.
                    </p>
                </div>

            <div className="bg-white p-4 rounded-lg shadow space-y-4 md:space-y-0 md:flex md:items-end md:space-x-4">
                <div className="flex-1">
                    <label htmlFor="portfolio" className="block text-sm font-medium text-gray-700 mb-1">
                        Cartera
                    </label>
                    <select
                        id="portfolio"
                        value={selectedPortfolio?.id || ''}
                        onChange={(e) => {
                            const portfolio = portfolios.find(p => p.id === e.target.value);
                            setSelectedPortfolio(portfolio || null);
                        }}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    >
                        {portfolios.map(portfolio => (
                            <option key={portfolio.id} value={portfolio.id}>
                                {portfolio.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
                        Fecha Inicio
                    </label>
                    <div className="relative rounded-md shadow-sm">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <Calendar className="h-4 w-4 text-gray-400" />
                        </div>
                        <input
                            type="date"
                            id="startDate"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="block w-full rounded-md border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                </div>

                <div>
                    <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
                        Fecha Fin
                    </label>
                    <div className="relative rounded-md shadow-sm">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <Calendar className="h-4 w-4 text-gray-400" />
                        </div>
                        <input
                            type="date"
                            id="endDate"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="block w-full rounded-md border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                </div>

                <button
                    onClick={calculateResults}
                    disabled={loading || !selectedPortfolio}
                    className="w-full md:w-auto bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {loading ? 'Calculando...' : 'Calcular'}
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            )}

            {results && results.items.length > 0 ? (
                <div className="flex-1 bg-white shadow rounded-lg p-4" style={{ minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
                    <div className="flex-shrink-0 pb-4 border-b border-gray-200 flex justify-between items-center">
                        <h3 className="text-lg font-medium text-gray-900">Detalle de Operaciones</h3>
                        <div className={`text-lg font-bold ${results.total_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            Resultado Total: {results.total_result.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                    <div className="flex-1 pt-4 overflow-auto">
                        <div style={{ height: '450px', width: '100%' }} ref={hotTableRef} />
                        <style>{`
                .htPositive { color: #059669; font-weight: 600; }
                .htNegative { color: #DC2626; font-weight: 600; }
              `}</style>
                    </div>
                </div>
            ) : results ? (
                <div className="flex-1 flex items-center justify-center bg-white shadow rounded-lg p-12 text-center text-gray-500">
                    <div>
                        <Calculator className="mx-auto h-12 w-12 text-gray-300" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay resultados fiscales</h3>
                        <p className="mt-1 text-sm text-gray-500">No se encontraron operaciones cerradas en el período seleccionado.</p>
                    </div>
                </div>
            ) : null}
            </div>
        </Layout>
    );
}
