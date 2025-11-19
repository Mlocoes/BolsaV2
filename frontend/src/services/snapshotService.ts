import api from './api';

export interface SnapshotPosition {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  average_price: number;
  current_price: number;
  current_value: number;
  cost_basis: number;
  profit_loss: number;
  profit_loss_percent: number;
}

export interface PortfolioSnapshot {
  id: string;
  portfolio_id: string;
  snapshot_date: string;
  total_value: number;
  total_cost: number;
  total_profit_loss: number;
  total_profit_loss_percent: number;
  positions: SnapshotPosition[];
  created_at: string;
}

export const snapshotService = {
  async getHistory(portfolioId: string): Promise<PortfolioSnapshot[]> {
    const response = await api.get(`/v1/snapshots/history/${portfolioId}`);
    return response.data;
  },

  async getLatest(portfolioId: string): Promise<PortfolioSnapshot | null> {
    const response = await api.get(`/v1/snapshots/latest/${portfolioId}`);
    return response.data;
  },

  async createSnapshot(portfolioId: string): Promise<PortfolioSnapshot> {
    const response = await api.post('/v1/snapshots/create', { portfolio_id: portfolioId });
    return response.data;
  },

  async getByDate(portfolioId: string, date: string): Promise<PortfolioSnapshot | null> {
    const response = await api.get(`/v1/snapshots/history/${portfolioId}`);
    const snapshots = response.data as PortfolioSnapshot[];
    return snapshots.find(s => s.snapshot_date === date) || null;
  }
};
