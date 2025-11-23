import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';
import Layout from '../components/Layout';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.min.css';
import { Save, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

import { registerLanguageDictionary, esMX } from 'handsontable/i18n';
import { registerAllModules } from 'handsontable/registry';
import numbro from 'numbro';
import esES from 'numbro/dist/languages/es-ES.min.js';

// Registrar idioma en numbro
numbro.registerLanguage(esES);
numbro.setLanguage('es-ES');

// Registrar módulos de Handsontable
registerAllModules();
// Crear diccionario para es-ES basado en es-MX
const esESDictionary = { ...esMX, languageCode: 'es-ES' };
registerLanguageDictionary(esESDictionary);

export default function BulkEditTransactions() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const hotTableRef = useRef<HTMLDivElement>(null);
    const hotInstance = useRef<Handsontable | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [assets, setAssets] = useState<any[]>([]);

    useEffect(() => {
        if (id) {
            loadData();
        }
    }, [id]);

    useEffect(() => {
        if (!loading && hotTableRef.current && !hotInstance.current) {
            initializeHandsontable();
        }
    }, [loading]);

    useEffect(() => {
        return () => {
            if (hotInstance.current) {
                hotInstance.current.destroy();
                hotInstance.current = null;
            }
        };
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [txs, assetsData] = await Promise.all([
                portfolioService.getTransactions(id!),
                portfolioService.getAssets()
            ]);

            // Map transactions for grid
            const gridData = txs.map(t => {
                let dateStr = '';
                if (t.transaction_date) {
                    const datePart = new Date(t.transaction_date).toISOString().split('T')[0];
                    const [y, m, d] = datePart.split('-');
                    dateStr = `${d}/${m}/${y}`;
                }
                return {
                    id: t.id,
                    date: dateStr,
                    type: t.transaction_type,
                    asset_symbol: t.asset?.symbol || '',
                    quantity: t.quantity,
                    price: t.price,
                    fees: t.fees,
                    notes: t.notes,
                    asset_id: t.asset_id // Hidden for reference
                };
            });

            setTransactions(gridData);
            setAssets(assetsData);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Error al cargar datos');
        } finally {
            setLoading(false);
        }
    };

    const initializeHandsontable = () => {
        if (!hotTableRef.current) return;

        const assetSymbols = assets.map(a => a.symbol);

        hotInstance.current = new Handsontable(hotTableRef.current, {
            data: transactions,
            language: 'es-ES',
            colHeaders: [
                'Fecha',
                'Tipo',
                'Activo',
                'Cantidad',
                'Precio',
                'Comisiones',
                'Notas'
            ],
            columns: [
                {
                    data: 'date',
                    type: 'date',
                    dateFormat: 'DD/MM/YYYY',
                    correctFormat: true
                },
                {
                    data: 'type',
                    type: 'dropdown',
                    source: ['buy', 'sell', 'dividend', 'deposit', 'withdrawal']
                },
                {
                    data: 'asset_symbol',
                    type: 'dropdown',
                    source: assetSymbols
                },
                {
                    data: 'quantity',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' }
                },
                {
                    data: 'price',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' }
                },
                {
                    data: 'fees',
                    type: 'numeric',
                    numericFormat: { pattern: '0,0.00', culture: 'es-ES' }
                },
                {
                    data: 'notes',
                    type: 'text'
                }
            ],
            rowHeaders: true,
            width: '100%',
            height: 600,
            licenseKey: 'non-commercial-and-evaluation',
            stretchH: 'all',
            autoColumnSize: true,
            filters: true,
            dropdownMenu: true,
            columnSorting: true,
            contextMenu: true,
            minSpareRows: 0, // No new rows for now, only edit
            afterChange: () => {
                // Handle local updates if needed
            }
        });
    };

    const handleSave = async () => {
        if (!hotInstance.current || !id) return;

        setSaving(true);
        try {
            const currentData = hotInstance.current.getSourceData();

            // Prepare batch update payload
            const updates = currentData.map((row: any) => {
                // Find asset_id from symbol if changed
                let assetId = row.asset_id;
                const asset = assets.find(a => a.symbol === row.asset_symbol);
                if (asset) {
                    assetId = asset.id;
                }

                // Convertir fecha DD/MM/YYYY a YYYY-MM-DD
                let isoDate = row.date;
                if (row.date && row.date.includes('/')) {
                    const [d, m, y] = row.date.split('/');
                    isoDate = `${y}-${m}-${d}`;
                }

                return {
                    id: row.id,
                    asset_id: assetId,
                    transaction_type: row.type,
                    quantity: parseFloat(row.quantity),
                    price: parseFloat(row.price),
                    fees: parseFloat(row.fees || 0),
                    notes: row.notes,
                    transaction_date: isoDate
                };
            });

            await portfolioService.updateTransactionsBatch(id, updates);
            toast.success('Cambios guardados correctamente');
            navigate(`/?portfolio=${id}`); // Go back to dashboard
        } catch (error) {
            console.error('Error saving:', error);
            toast.error('Error al guardar cambios');
        } finally {
            setSaving(false);
        }
    };

    return (
        <Layout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => navigate(`/?portfolio=${id}`)}
                            className="p-2 rounded-full hover:bg-gray-100"
                        >
                            <ArrowLeft className="h-6 w-6 text-gray-600" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Edición Masiva de Transacciones</h1>
                            <p className="text-sm text-gray-500">Edita tus transacciones como en una hoja de cálculo</p>
                        </div>
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={saving || loading}
                        className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                    >
                        <Save className="h-5 w-5 mr-2" />
                        {saving ? 'Guardando...' : 'Guardar Cambios'}
                    </button>
                </div>

                {loading ? (
                    <div className="flex justify-center py-12">
                        <div className="text-gray-500">Cargando transacciones...</div>
                    </div>
                ) : (
                    <div className="bg-white shadow rounded-lg overflow-hidden p-4">
                        <div ref={hotTableRef} />
                    </div>
                )}
            </div>
        </Layout>
    );
}
