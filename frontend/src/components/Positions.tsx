import { useEffect, useState, useRef } from 'react';
import { portfolioService } from '../services/portfolioService';
import { snapshotService, type PortfolioSnapshot } from '../services/snapshotService';
import type { Portfolio } from '../types/portfolio';
import { Wallet } from 'lucide-react';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.min.css';
import { registerLanguageDictionary, esMX } from 'handsontable/i18n';
import numbro from 'numbro';
import esES from 'numbro/dist/languages/es-ES.min.js';

// Registrar idioma en numbro
numbro.registerLanguage(esES);
numbro.setLanguage('es-ES');

// Crear diccionario para es-ES basado en es-MX
const esESDictionary = { ...esMX, languageCode: 'es-ES' };
registerLanguageDictionary(esESDictionary);

/**
 * Componente para visualizar el histórico de posiciones de las carteras
 * Permite seleccionar una cartera y una fecha para ver el snapshot de posiciones
 */
export default function Positions() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedSnapshot, setSelectedSnapshot] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hotTableRef = useRef<HTMLDivElement>(null);
  const hotInstance = useRef<Handsontable | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
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

  /**
   * Carga la lista de carteras del usuario
   */
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

  /**
   * Carga las fechas disponibles de snapshots para una cartera
   */
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

  /**
   * Carga un snapshot específico por fecha
   */
  const loadSnapshotByDate = async (portfolioId: string, date: string) => {
    try {
      const snapshot = await snapshotService.getByDate(portfolioId, date);
      setSelectedSnapshot(snapshot);
    } catch (err: any) {
      console.error('Error loading snapshot by date:', err);
    }
  };

  /**
   * Inicializa la tabla Handsontable con la configuración
   */
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
      // Convert percentage value to decimal for Handsontable's '0.00%' format
      // G/P% = (Valor Actual - Costo Base) / Costo Base
      profit_loss_percent: p.profit_loss_percent / 100
    }));

    hotInstance.current = new Handsontable(hotTableRef.current, {
      data,
      language: 'es-ES',
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
        { data: 'symbol', type: 'text', readOnly: true, width: 90 },
        { data: 'name', type: 'text', readOnly: true, width: 200 },
        { data: 'asset_type', type: 'text', readOnly: true, width: 90 },
        { data: 'quantity', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00', culture: 'es-ES' }, width: 100 },
        { data: 'average_price', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00', culture: 'es-ES' }, width: 115 },
        { data: 'current_price', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00', culture: 'es-ES' }, width: 115 },
        { data: 'current_value', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00', culture: 'es-ES' }, width: 120 },
        { data: 'cost_basis', type: 'numeric', readOnly: true, numericFormat: { pattern: '0,0.00', culture: 'es-ES' }, width: 115 },
        {
          data: 'profit_loss',
          type: 'numeric',
          readOnly: true,
          width: 120,
          numericFormat: { pattern: '0,0.00', culture: 'es-ES' },
          renderer: function (instance: any, td: HTMLTableCellElement, row: number, col: number, prop: any, value: any, cellProperties: any) {
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
          width: 90,
          numericFormat: { pattern: '0.00%', culture: 'es-ES' },
          renderer: function (instance: any, td: HTMLTableCellElement, row: number, col: number, prop: any, value: any, cellProperties: any) {
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
      rowHeaders: false,
      width: '100%',
      height: '100%',
      licenseKey: 'non-commercial-and-evaluation',
      stretchH: 'none',
      autoColumnSize: false,
      filters: true,
      dropdownMenu: true,
      columnSorting: true
    });
  };

  /**
   * Actualiza los datos de la tabla Handsontable
   */
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
      // Convert percentage value to decimal for Handsontable's '0.00%' format
      // G/P% = (Valor Actual - Costo Base) / Costo Base
      profit_loss_percent: p.profit_loss_percent / 100
    }));

    hotInstance.current.loadData(data);
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
        <p className="mt-1 text-sm text-gray-500">Crea una cartera desde el Panel de Control para comenzar.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col space-y-2 md:space-y-3">
      {/* Header - compacto */}
      <div className="flex-shrink-0">
        <h1 className="text-xl md:text-2xl font-bold text-gray-900">Posiciones</h1>
        <p className="text-xs md:text-sm text-gray-600">
          Histórico de posiciones de tus carteras
        </p>
      </div>

      {/* Portfolio Selector - compacto */}
      <div className="flex-shrink-0 flex items-center space-x-2 md:space-x-4">
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

      {/* Positions Table - altura flexible */}
      <div className="flex-1 min-h-0 bg-white shadow rounded-lg overflow-hidden flex flex-col">
        <div className="flex-shrink-0 px-2 py-2 md:px-4 md:py-3 border-b border-gray-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div>
              <h3 className="text-sm md:text-base font-medium text-gray-900">
                Histórico de Posiciones
              </h3>
              <p className="text-xs md:text-sm text-gray-500">
                Visualiza el estado de tu cartera en diferentes fechas
              </p>
            </div>
            <div className="flex items-center space-x-2 md:space-x-4">
              {availableDates.length > 0 && (
                <div className="flex flex-col">
                  <label className="text-xs text-gray-500 mb-1">Fecha:</label>
                  <select
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="block rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs md:text-sm px-2 py-1 md:px-3 md:py-2"
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
        <div className="flex-1 min-h-0 p-2 md:p-4 overflow-auto">
          {selectedSnapshot ? (
            <div className="h-full flex flex-col space-y-2">
              <div className="flex-shrink-0 p-2 md:p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <p className="text-xs md:text-sm font-medium text-blue-900">
                      📸 Visualizando snapshot del {new Date(selectedSnapshot.date || selectedSnapshot.snapshot_date || '').toLocaleDateString('es-ES', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      {selectedSnapshot.positions.length} posiciones |
                      Valor Total: {selectedSnapshot.total_value.toLocaleString('es-ES', { minimumFractionDigits: 2 })} |
                      G/P: {(selectedSnapshot.total_pnl || selectedSnapshot.total_profit_loss || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                      ({(selectedSnapshot.total_pnl_percent || selectedSnapshot.total_profit_loss_percent || 0) >= 0 ? '+' : ''}{(selectedSnapshot.total_pnl_percent || selectedSnapshot.total_profit_loss_percent || 0).toFixed(2).replace('.', ',')}%)
                    </p>
                  </div>
                  {selectedSnapshot.created_at && (
                    <div className="text-xs text-blue-600">
                      Creado: {new Date(selectedSnapshot.created_at).toLocaleTimeString('es-ES')}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex-1 min-h-0" ref={hotTableRef} />
              <style>{`
                .htPositive { color: #059669; font-weight: 600; }
                .htNegative { color: #DC2626; font-weight: 600; }
              `}</style>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center text-gray-500">
              <div>
                <p className="mb-2">No hay datos históricos disponibles para esta cartera.</p>
                <p className="text-sm">El sistema crea automáticamente snapshots diarios de tus posiciones.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
