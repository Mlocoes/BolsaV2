import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { PositionWithPrice } from '../types/portfolio';

interface PortfolioDistributionChartProps {
  positions: PositionWithPrice[];
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#06b6d4', '#3b82f6'];

export default function PortfolioDistributionChart({ positions }: PortfolioDistributionChartProps) {
  const data = positions.map((position, index) => ({
    name: position.symbol,
    value: position.current_value,
    percentage: 0,
    color: COLORS[index % COLORS.length]
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);
  data.forEach(item => {
    item.percentage = (item.value / total) * 100;
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-gray-900">{payload[0].name}</p>
          <p className="text-sm text-gray-600">
            Valor: ${payload[0].value.toFixed(2)}
          </p>
          <p className="text-sm text-gray-600">
            {payload[0].payload.percentage.toFixed(2)}% del portfolio
          </p>
        </div>
      );
    }
    return null;
  };

  const renderLabel = (entry: any) => {
    if (entry.percentage < 5) return '';
    return `${entry.name} (${entry.percentage.toFixed(1)}%)`;
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
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderLabel}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
