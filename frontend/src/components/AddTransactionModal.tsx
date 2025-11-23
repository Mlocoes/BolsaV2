import { useState, useEffect } from 'react';
import { X, Search } from 'lucide-react';
import { portfolioService } from '../services/portfolioService';
import type { Asset, Transaction } from '../types/portfolio';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;  // UUID
  onSuccess: () => void;
  transaction?: Transaction | null;
}

export default function AddTransactionModal({ isOpen, onClose, portfolioId, onSuccess, transaction }: AddTransactionModalProps) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [transactionType, setTransactionType] = useState<'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal'>('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [fee, setFee] = useState('');
  const [notes, setNotes] = useState('');
  const [transactionDate, setTransactionDate] = useState(() => {
    // Por defecto hoy en formato yyyy-mm-dd
    const today = new Date();
    return today.toISOString().slice(0, 10);
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadAssets();
      if (transaction) {
        // Pre-fill form for editing
        if (transaction.asset) {
          setSelectedAsset(transaction.asset);
        }
        setTransactionType(transaction.transaction_type as any);
        setQuantity(transaction.quantity.toString());
        setPrice(transaction.price.toString());
        setFee(transaction.fees ? transaction.fees.toString() : '');
        setNotes(transaction.notes || '');
        // Handle date format
        const date = new Date(transaction.transaction_date);
        setTransactionDate(date.toISOString().slice(0, 10));
      } else {
        // Reset for new transaction
        resetForm();
      }
    }
  }, [isOpen, transaction]);

  const resetForm = () => {
    setSelectedAsset(null);
    setSearchTerm('');
    setTransactionType('buy');
    setQuantity('');
    setPrice('');
    setFee('');
    setNotes('');
    setTransactionDate(new Date().toISOString().slice(0, 10));
    setError(null);
  };

  const loadAssets = async () => {
    try {
      const data = await portfolioService.getAssets();
      setAssets(data);
    } catch (err) {
      console.error('Error loading assets:', err);
    }
  };

  const filteredAssets = assets.filter(asset =>
    asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset) return;

    setError(null);
    setLoading(true);

    try {
      const data: any = {
        asset_id: selectedAsset.id,
        transaction_type: transactionType,
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        fees: fee ? parseFloat(fee) : 0,
        notes: notes || undefined,
        transaction_date: transactionDate,
      };

      if (transaction) {
        // Update existing transaction
        await portfolioService.updateTransaction(portfolioId, { ...data, id: transaction.id });
      } else {
        // Create new transaction
        // Map fees to fee for create endpoint if needed, but schema says fees usually
        // Checking create schema: CreateTransactionRequest uses 'fee' (singular) in frontend types but backend might expect 'fees'.
        // Let's check backend schema. TransactionCreate has 'fees'. Frontend type has 'fee'.
        // Let's stick to 'fee' for create if that's what worked before, or fix it.
        // Previous code used 'fee: fee ? parseFloat(fee) : undefined'.
        // Backend TransactionCreate has 'fees: float = Field(default=0, ge=0)'.
        // It seems previous code might have been sending 'fee' and backend ignoring it or mapping it?
        // Wait, let's look at previous file content.
        // Line 63: fee: fee ? parseFloat(fee) : undefined,
        // Backend TransactionCreate (line 81 in schemas/portfolio.py): fees: float = Field(default=0, ge=0)
        // If frontend sends 'fee', pydantic might ignore it if not in schema.
        // I should probably send 'fees'.
        // However, to be safe and consistent with previous working code, I will send what matches the backend schema.
        // Backend schema `TransactionCreate` has `fees`.
        // Let's send `fees`.
        await portfolioService.createTransaction(portfolioId, { ...data, fees: data.fees });
      }

      onSuccess();
      onClose();
      resetForm();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error al guardar transacción');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-25" onClick={onClose} />

        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {transaction ? 'Editar Transacción' : 'Agregar Transacción'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* Fecha de la transacción */}
              <div>
                <label htmlFor="transaction_date" className="block text-sm font-medium text-gray-700">
                  Fecha de la Transacción *
                </label>
                <input
                  type="date"
                  id="transaction_date"
                  value={transactionDate}
                  onChange={e => setTransactionDate(e.target.value)}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              {/* Asset Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Buscar Activo *
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Buscar por símbolo o nombre..."
                    disabled={!!transaction} // Disable asset change on edit for simplicity, or allow it? Batch update supports it. Let's allow it but maybe warn?
                  // Actually, let's allow it.
                  />
                </div>

                {searchTerm && !transaction && (
                  <div className="mt-2 max-h-48 overflow-y-auto border border-gray-200 rounded-md">
                    {filteredAssets.length === 0 ? (
                      <div className="p-3 text-sm text-gray-500">No se encontraron activos</div>
                    ) : (
                      filteredAssets.map(asset => (
                        <button
                          key={asset.id}
                          type="button"
                          onClick={() => {
                            setSelectedAsset(asset);
                            setSearchTerm('');
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center justify-between"
                        >
                          <div>
                            <div className="font-medium text-sm">{asset.symbol}</div>
                            <div className="text-xs text-gray-500">{asset.name}</div>
                          </div>
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            {asset.asset_type}
                          </span>
                        </button>
                      ))
                    )}
                  </div>
                )}

                {selectedAsset && (
                  <div className="mt-2 p-3 bg-indigo-50 border border-indigo-200 rounded-md flex items-center justify-between">
                    <div>
                      <div className="font-medium">{selectedAsset.symbol}</div>
                      <div className="text-sm text-gray-600">{selectedAsset.name}</div>
                    </div>
                    {!transaction && (
                      <button
                        type="button"
                        onClick={() => setSelectedAsset(null)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm"
                      >
                        Cambiar
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Transaction Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Transacción *
                </label>
                <div className="flex space-x-4 flex-wrap gap-y-2">
                  {['buy', 'sell', 'dividend', 'deposit', 'withdrawal'].map((type) => (
                    <label key={type} className="flex items-center mr-4">
                      <input
                        type="radio"
                        value={type}
                        checked={transactionType === type}
                        onChange={(e) => setTransactionType(e.target.value as any)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">
                        {type === 'buy' ? 'Compra' :
                          type === 'sell' ? 'Venta' :
                            type === 'dividend' ? 'Dividendo' :
                              type === 'deposit' ? 'Depósito' : 'Retiro'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Quantity and Price */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">
                    Cantidad *
                  </label>
                  <input
                    type="number"
                    id="quantity"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    required
                    step="0.00000001"
                    min="0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label htmlFor="price" className="block text-sm font-medium text-gray-700">
                    Precio Unitario *
                  </label>
                  <input
                    type="number"
                    id="price"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    required
                    step="0.01"
                    min="0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="0.00"
                  />
                </div>
              </div>

              {/* Fee */}
              <div>
                <label htmlFor="fee" className="block text-sm font-medium text-gray-700">
                  Comisión (opcional)
                </label>
                <input
                  type="number"
                  id="fee"
                  value={fee}
                  onChange={(e) => setFee(e.target.value)}
                  step="0.01"
                  min="0"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="0.00"
                />
              </div>

              {/* Total */}
              {quantity && price && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Total:</span>
                    <span className="text-lg font-bold text-gray-900">
                      ${(parseFloat(quantity) * parseFloat(price) + (fee ? parseFloat(fee) : 0)).toFixed(2)}
                    </span>
                  </div>
                </div>
              )}

              {/* Notes */}
              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                  Notas (opcional)
                </label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Información adicional sobre la transacción"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading || !selectedAsset}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Guardando...' : (transaction ? 'Actualizar Transacción' : 'Agregar Transacción')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
