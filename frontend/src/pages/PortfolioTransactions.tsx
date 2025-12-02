import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';
import type { Transaction } from '../types/portfolio';
import Layout from '../components/Layout';
import { ArrowLeft, Save, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { HotTable } from '@handsontable/react';
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
    const hotRef = useRef<any>(null);

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

    const handleDeleteSelected = async () => {
        if (!hotRef.current) return;
        const hot = hotRef.current.hotInstance;
        const selected = hot.getSelected();

        if (!selected || selected.length === 0) {
            toast.error('Selecciona celdas o filas para eliminar');
            return;
        }

        // Obtener índices de filas únicas seleccionadas
        const selectedRowIndices = new Set<number>();
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        for (const [r1, _c1, r2, _c2] of selected) {
            const start = Math.min(r1, r2);
            const end = Math.max(r1, r2);
            for (let i = start; i <= end; i++) {
                selectedRowIndices.add(i);
            }
        }

        const sourceData = hot.getSourceData();
        const toDeleteIds: string[] = [];

        selectedRowIndices.forEach(rowIndex => {
            const physicalRow = hot.toPhysicalRow(rowIndex);
            const rowData = sourceData[physicalRow];
            if (rowData && rowData.id) {
                toDeleteIds.push(rowData.id);
            }
        });

        if (toDeleteIds.length === 0) {
            toast.error('Las filas seleccionadas no contienen transacciones válidas para eliminar');
            return;
        }

        if (!confirm(`¿Estás seguro de eliminar ${toDeleteIds.length} transaccion(es)?`)) return;

        try {
            setSaving(true);
            await Promise.all(toDeleteIds.map(tid => portfolioService.deleteTransaction(id!, tid)));
            toast.success(`${toDeleteIds.length} transaccion(es) eliminadas correctamente`);
            loadData();
        } catch (error) {
            console.error('Error deleting:', error);
            toast.error('Error al eliminar transacciones');
        } finally {
            setSaving(false);
        }
    };

    const handleSaveWithCreate = async () => {
        if (!hotRef.current) return;
        const hot = hotRef.current.hotInstance;
        const sourceData = hot.getSourceData();

        try {
            setSaving(true);

            const updates: any[] = [];
            const creates: any[] = [];

            for (const row of sourceData) {
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
                            Eliminar
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


                <div className="flex-1 bg-white shadow rounded-lg relative overflow-hidden flex flex-col">
                    <div className="flex-1 relative" style={{ minHeight: '400px' }}>
                        {Object.keys(assetMap).length === 0 ? (
                            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                                <div className="text-center">
                                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                                    <p>Cargando activos...</p>
                                </div>
                            </div>
                        ) : (
                            <div style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
                                <HotTable
                                    ref={hotRef}
                                    data={hotData}
                                    licenseKey="non-commercial-and-evaluation"
                                    language="es-ES"
                                    colHeaders={[
                                        'Fecha', 'Activo', 'Tipo', 'Cantidad', 'Precio', 'Comisiones', 'Notas'
                                    ]}
                                    columns={[
                                        { data: 'date', type: 'date', dateFormat: 'DD/MM/YYYY', correctFormat: true },
                                        {
                                            data: 'asset',
                                            type: 'dropdown',
                                            source: Object.keys(assetMap).sort()
                                        },
                                        {
                                            data: 'type',
                                            type: 'dropdown',
                                            source: ['buy', 'sell', 'dividend', 'deposit', 'withdrawal']
                                        },
                                        {
                                            data: 'quantity',
                                            type: 'numeric',
                                            numericFormat: { pattern: '0,0.000000' }
                                        },
                                        {
                                            data: 'price',
                                            type: 'numeric',
                                            numericFormat: { pattern: '0,0.00' }
                                        },
                                        {
                                            data: 'fees',
                                            type: 'numeric',
                                            numericFormat: { pattern: '0,0.00' }
                                        },
                                        { data: 'notes', type: 'text' }
                                    ]}
                                    minSpareRows={1}
                                    rowHeaders={false}
                                    width="100%"
                                    height={500}
                                    stretchH="all"
                                    contextMenu={true}
                                    manualColumnResize={true}
                                    manualRowResize={true}
                                    filters={true}
                                    dropdownMenu={true}
                                    columnSorting={true}
                                    afterInit={() => {
                                        console.log('✅ HotTable inicializado correctamente');
                                    }}
                                />
                            </div>
                        )}
                    </div>
                    <div className="p-2 text-xs text-gray-500 bg-gray-50 border-t">
                        * Escribe en la última fila vacía para agregar una nueva transacción.
                    </div>
                </div>
            </div>
        </Layout>
    );
}
