import { useState, useEffect } from 'react';
import { X, Search } from 'lucide-react';
import { portfolioService } from '../services/portfolioService';
import type { Asset, CreateTransactionRequest } from '../types/portfolio';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;  // UUID
  onSuccess: () => void;
}

export default function AddTransactionModal({ isOpen, onClose, portfolioId, onSuccess }: AddTransactionModalProps) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [transactionType, setTransactionType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [fee, setFee] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadAssets();
    }
  }, [isOpen]);

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
      const data: CreateTransactionRequest = {
        asset_id: selectedAsset.id,
        transaction_type: transactionType,
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        fee: fee ? parseFloat(fee) : undefined,
        notes: notes || undefined,
      };

      await portfolioService.createTransaction(portfolioId, data);
      
      // Reset form
      setSelectedAsset(null);
      setSearchTerm('');
      setQuantity('');
      setPrice('');
      setFee('');
      setNotes('');
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear transacción');
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
              Agregar Transacción
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
                  />
                </div>
                
                {searchTerm && (
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
                    <button
                      type="button"
                      onClick={() => setSelectedAsset(null)}
                      className="text-indigo-600 hover:text-indigo-800 text-sm"
                    >
                      Cambiar
                    </button>
                  </div>
                )}
              </div>

              {/* Transaction Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Transacción *
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="buy"
                      checked={transactionType === 'buy'}
                      onChange={(e) => setTransactionType(e.target.value as 'buy')}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Compra</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="sell"
                      checked={transactionType === 'sell'}
                      onChange={(e) => setTransactionType(e.target.value as 'sell')}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Venta</span>
                  </label>
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
                {loading ? 'Guardando...' : 'Agregar Transacción'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
