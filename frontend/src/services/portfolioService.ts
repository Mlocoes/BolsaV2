import api from './api';
import type {
  Portfolio,
  Asset,
  Position,
  Transaction,
  AssetPrice,
  PositionWithPrice,
  CreatePortfolioRequest,
  CreateTransactionRequest
} from '../types/portfolio';

export const portfolioService = {
  // Portfolios
  async getPortfolios(): Promise<Portfolio[]> {
    const response = await api.get('/portfolios');
    return response.data;
  },

  async getPortfolio(id: string): Promise<Portfolio> {
    const response = await api.get(`/portfolios/${id}`);
    return response.data;
  },

  async createPortfolio(data: CreatePortfolioRequest): Promise<Portfolio> {
    const response = await api.post('/portfolios', data);
    return response.data;
  },

  async updatePortfolio(id: string, data: Partial<CreatePortfolioRequest>): Promise<Portfolio> {
    const response = await api.put(`/portfolios/${id}`, data);
    return response.data;
  },

  async deletePortfolio(id: string): Promise<void> {
    await api.delete(`/portfolios/${id}`);
  },

  // Positions
  async getPositions(portfolioId: string): Promise<Position[]> {
    const response = await api.get(`/portfolios/${portfolioId}/positions`);
    return response.data;
  },

  // Transactions
  async getTransactions(portfolioId: string): Promise<Transaction[]> {
    const response = await api.get(`/portfolios/${portfolioId}/transactions`);
    return response.data;
  },

  async createTransaction(portfolioId: string, data: CreateTransactionRequest): Promise<Transaction> {
    const response = await api.post(`/portfolios/${portfolioId}/transactions`, data);
    return response.data;
  },

  async updateTransactionsBatch(portfolioId: string, transactions: any[]): Promise<void> {
    await api.put(`/portfolios/${portfolioId}/transactions/batch`, { transactions });
  },

  // Assets
  async getAssets(): Promise<Asset[]> {
    const response = await api.get('/assets');
    return response.data;
  },

  async searchAssets(search: string): Promise<Asset[]> {
    const response = await api.get(`/assets?search=${encodeURIComponent(search)}`);
    return response.data;
  },

  async getAsset(id: string): Promise<Asset> {
    const response = await api.get(`/assets/${id}`);
    return response.data;
  },

  // Prices
  async getAssetPrice(symbol: string): Promise<AssetPrice> {
    const response = await api.get(`/prices/${symbol}`);
    return response.data;
  },

  async getMultiplePrices(symbols: string[]): Promise<AssetPrice[]> {
    const response = await api.get(`/prices?symbols=${symbols.join(',')}`);
    return response.data;
  },

  async getPortfolioPrices(portfolioId: string): Promise<PositionWithPrice[]> {
    const response = await api.get(`/prices/portfolio/${portfolioId}`);
    return response.data;
  }
};
