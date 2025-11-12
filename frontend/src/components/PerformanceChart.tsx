import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { PositionWithPrice } from '../types/portfolio';

interface PerformanceChartProps {
  positions: PositionWithPrice[];
}

export default function PerformanceChart({ positions }: PerformanceChartProps) {
  const data = positions.map(position => ({
    symbol: position.symbol,
    profitLoss: position.profit_loss,
    profitLossPercent: position.profit_loss_percent
  })).sort((a, b) => b.profitLoss - a.profitLoss);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const value = payload[0].value;
      const percent = payload[0].payload.profitLossPercent;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-gray-900">{payload[0].payload.symbol}</p>
          <p className={`text-sm font-medium ${value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${value.toFixed(2)} ({percent >= 0 ? '+' : ''}{percent.toFixed(2)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  if (positions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No hay posiciones para mostrar
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="symbol" />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="profitLoss" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.profitLoss >= 0 ? '#10b981' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
