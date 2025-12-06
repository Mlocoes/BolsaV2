import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';
import type { Transaction } from '../types/portfolio';
import Layout from '../components/Layout';
import { ArrowLeft, Save, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.min.css';
import '../styles/handsontable-custom.css';
import { registerLanguageDictionary, esMX } from 'handsontable/i18n';
import { registerAllModules } from 'handsontable/registry';

// Registrar módulos de Handsontable
registerAllModules();
// Crear diccionario para es-ES basado en es-MX (ya que esES no se exporta directamente)
const esESDictionary = { ...esMX, languageCode: 'es-ES' };
registerLanguageDictionary(esESDictionary);

export default function PortfolioTransactions() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const containerRef = useRef<HTMLDivElement>(null);
    const hotRef = useRef<Handsontable | null>(null);

    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [portfolioName, setPortfolioName] = useState('');

    // Mapeos para dropdowns
    const [assetMap, setAssetMap] = useState<Record<string, string>>({}); // symbol -> id
    const [idToSymbolMap, setIdToSymbolMap] = useState<Record<string, string>>({}); // id -> symbol

    useEffect(() => {
        if (id) {
            loadData();
        }
    }, [id]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [portfolioData, transactionsData, assetsData] = await Promise.all([
                portfolioService.getPortfolio(id!),
                portfolioService.getTransactions(id!),
                portfolioService.getAssets()
            ]);

            setPortfolioName(portfolioData.name);
            setTransactions(transactionsData);

            // Crear mapas de activos
            const aMap: Record<string, string> = {};
            const idMap: Record<string, string> = {};
            assetsData.forEach(a => {
                aMap[a.symbol] = a.id;
                idMap[a.id] = a.symbol;
            });
            setAssetMap(aMap);
            setIdToSymbolMap(idMap);

        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Error al cargar los datos');
        } finally {
            setLoading(false);
        }
    };

    const hotData = useMemo(() => {
        return transactions.map(t => {
            let dateStr = '';
            if (t.transaction_date) {
                const datePart = new Date(t.transaction_date).toISOString().split('T')[0];
                const [y, m, d] = datePart.split('-');
                dateStr = `${d}/${m}/${y}`;
            }
            return {
                id: t.id,
                date: dateStr,
                asset: t.asset?.symbol || idToSymbolMap[t.asset_id] || '',
                type: t.transaction_type,
                quantity: t.quantity,
                price: t.price,
                fees: t.fees || 0,
                notes: t.notes || ''
            };
        });
    }, [transactions, idToSymbolMap]);

    // Inicializar Handsontable
    useEffect(() => {
        if (loading || !containerRef.current || Object.keys(assetMap).length === 0) return;

        // Si ya existe instancia, solo actualizar datos si es necesario (manejado por useEffect aparte)
        if (hotRef.current) return;

        console.log('🚀 Inicializando Handsontable en PortfolioTransactions');

        hotRef.current = new Handsontable(containerRef.current, {
            data: hotData,
            licenseKey: "non-commercial-and-evaluation",
            language: "es-ES",
            colHeaders: [
                'Fecha', 'Activo', 'Tipo', 'Cantidad', 'Precio', 'Comisiones', 'Notas'
            ],
            columns: [
                { data: 'date', type: 'date', dateFormat: 'DD/MM/YYYY', correctFormat: true, width: 100 },
                {
                    data: 'asset',
                    type: 'dropdown',
                    source: Object.keys(assetMap).sort(),
                    width: 100
                },
                {
                    data: 'type',
                    type: 'dropdown',
                    source: ['buy', 'sell', 'dividend', 'deposit', 'withdrawal'],
                    width: 100
                },
                {
                    data: 'quantity',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.000000', culture: 'es-ES' },
                    width: 120
                },
                {
                    data: 'price',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    width: 100
                },
                {
                    data: 'fees',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
                    width: 100
                },
                { data: 'notes', type: 'text', width: 200 }
            ],
            minSpareRows: 1,
            rowHeaders: true,
            width: '100%',
            height: '100%',
            stretchH: 'all',
            contextMenu: {
                items: {
                    'remove_row': {
                        name: 'Eliminar fila(s)',
                        callback: function () {
                            handleDeleteSelected();
                        }
                    },
                    'sep1': '---------',
                    'row_above': {},
                    'row_below': {},
                    'sep2': '---------',
                    'undo': {},
                    'redo': {}
                }
            },
            manualColumnResize: true,
            manualRowResize: true,
            filters: true,
            dropdownMenu: true,
            columnSorting: true,
            autoColumnSize: false
        });

        return () => {
            if (hotRef.current) {
                hotRef.current.destroy();
                hotRef.current = null;
            }
        };
    }, [loading, assetMap]); // Re-init si loading termina o assetMap cambia

    // Actualizar datos cuando cambian
    useEffect(() => {
        if (hotRef.current && hotData) {
            hotRef.current.loadData(hotData);
        }
    }, [hotData]);

    const handleDeleteSelected = async () => {
        if (!hotRef.current) return;

        const hot = hotRef.current; // Instancia directa
        const selected = hot.getSelected();

        if (!selected || selected.length === 0) {
            toast.error('Selecciona celdas o filas para eliminar');
            return;
        }

        // Obtener índices de filas únicas seleccionadas
        const selectedRowIndices = new Set<number>();
        for (const [r1, _c1, r2, _c2] of selected) {
            const start = Math.min(r1, r2);
            const end = Math.max(r1, r2);
            for (let i = start; i <= end; i++) {
                selectedRowIndices.add(hot.toPhysicalRow(i));
            }
        }

        const toDeleteIds: string[] = [];
        // Mapeamos los índices físicos a los datos originales
        // Nota: hotData se mantiene sincronizado via useState, así que los índices deberían coincidir
        // si no hay filtrado/ordenamiento activo que desincronice el sourceData visual

        // Mejor aproximación: Usar getSourceDataAtRow para obtener el objeto row real

        selectedRowIndices.forEach(rowIndex => {
            // getSourceDataAtRow de Handsontable devuelve la referencia al objeto en el array original
            const rowSource = hot.getSourceDataAtRow(rowIndex) as any;
            if (rowSource && rowSource.id) {
                toDeleteIds.push(rowSource.id);
            }
        });

        if (toDeleteIds.length === 0) {
            toast.error('Las filas seleccionadas no contienen transacciones guardadas para eliminar');
            return;
        }

        if (!confirm(`¿Estás seguro de eliminar ${toDeleteIds.length} transaccion(es)?`)) return;

        try {
            setSaving(true);

            // Eliminar secuencialmente para evitar sobrecarga del backend
            for (const tid of toDeleteIds) {
                await portfolioService.deleteTransaction(id!, tid);
            }

            toast.success(`${toDeleteIds.length} transaccion(es) eliminadas correctamente`);

            hot.deselectCell();
            await loadData();
        } catch (error) {
            console.error('Error deleting:', error);
            toast.error('Error al eliminar transacciones');
        } finally {
            setSaving(false);
        }
    };

    const handleSaveWithCreate = async () => {
        if (!hotRef.current) return;
        const hot = hotRef.current;
        const sourceData = hot.getSourceData();

        try {
            setSaving(true);

            const updates: any[] = [];
            const creates: any[] = [];

            // data includes minSpareRow potentially empty, filter valid rows
            for (const row of sourceData as any[]) {
                // Validar datos mínimos
                if (!row.asset || !row.type || !row.quantity || !row.price || !row.date) continue;

                const assetId = assetMap[row.asset];
                if (!assetId) continue;

                // Convertir fecha DD/MM/YYYY a YYYY-MM-DD
                let isoDate = row.date;
                if (row.date && row.date.includes('/')) {
                    const [d, m, y] = row.date.split('/');
                    isoDate = `${y}-${m}-${d}`;
                }

                const payload = {
                    id: row.id,
                    portfolio_id: id,
                    asset_id: assetId,
                    transaction_type: row.type,
                    quantity: parseFloat(row.quantity),
                    price: parseFloat(row.price),
                    fees: parseFloat(row.fees || 0),
                    notes: row.notes,
                    transaction_date: isoDate
                };

                if (row.id) {
                    updates.push(payload);
                } else {
                    creates.push(payload);
                }
            }

            const promises = [];
            if (updates.length > 0) {
                promises.push(portfolioService.updateTransactionsBatch(id!, updates));
            }

            for (const createPayload of creates) {
                promises.push(portfolioService.createTransaction(id!, createPayload));
            }

            await Promise.all(promises);
            toast.success('Cambios guardados correctamente');
            loadData();

        } catch (error) {
            console.error('Error saving:', error);
            toast.error('Error al guardar cambios. Verifica los datos.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="flex flex-col h-full space-y-4 min-h-0">
                <div className="flex-shrink-0 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => navigate('/transactions')}
                            className="p-2 rounded-full hover:bg-gray-100 text-gray-500"
                        >
                            <ArrowLeft className="h-6 w-6" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                Transacciones: {portfolioName}
                            </h1>
                            <p className="text-sm text-gray-500">
                                Edita las transacciones como en una hoja de cálculo.
                            </p>
                        </div>
                    </div>
                    <div className="flex space-x-3">
                        <button
                            onClick={loadData}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Recargar
                        </button>
                        <button
                            onClick={handleDeleteSelected}
                            disabled={saving}
                            className="inline-flex items-center px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Eliminar Selección
                        </button>
                        <button
                            onClick={handleSaveWithCreate}
                            disabled={saving}
                            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                        >
                            <Save className="h-4 w-4 mr-2" />
                            {saving ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </div>


                <div className="flex-1 bg-white shadow rounded-lg overflow-hidden flex flex-col">
                    <div className="flex-1 min-h-0 p-4">
                        {Object.keys(assetMap).length === 0 ? (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                                    <p>Cargando activos...</p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 min-h-0 w-full relative h-full">
                                <div ref={containerRef} className="h-full w-full" />
                            </div>
                        )}
                    </div>
                    <div className="p-2 text-xs text-gray-500 bg-gray-50 border-t flex-shrink-0">
                        * Escribe en la última fila vacía para agregar una nueva transacción.
                    </div>
                </div>
            </div>
        </Layout>
    );
}
