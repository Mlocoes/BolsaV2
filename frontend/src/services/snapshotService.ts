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
  async getAvailableDates(portfolioId: string): Promise<string[]> {
    const response = await api.get(`/v1/snapshots/dates/${portfolioId}`);
    return response.data.dates || [];
  },

  async getByDate(portfolioId: string, date: string): Promise<PortfolioSnapshot | null> {
    const response = await api.get(`/v1/snapshots/history/${portfolioId}`, {
      params: {
        from_date: date,
        to_date: date,
        include_positions: true
      }
    });
    const snapshots = response.data.snapshots as PortfolioSnapshot[];
    return snapshots.length > 0 ? snapshots[0] : null;
  },

  async getHistory(portfolioId: string): Promise<PortfolioSnapshot[]> {
    const response = await api.get(`/v1/snapshots/history/${portfolioId}`);
    return response.data;
  },

  async getLatest(portfolioId: string): Promise<PortfolioSnapshot | null> {
    const response = await api.get(`/v1/snapshots/latest/${portfolioId}`);
    return response.data;
  },

  async createSnapshot(portfolioId: string): Promise<PortfolioSnapshot> {
    const response = await api.post(`/v1/snapshots/create/${portfolioId}`);
    return response.data;
  }
};
