export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  user_id: number;
}

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_type: 'stock' | 'crypto' | 'etf' | 'bond' | 'commodity' | 'cash';
  currency: string;
}

export interface Position {
  id: number;
  portfolio_id: number;
  asset_id: number;
  quantity: number;
  average_price: number;
  asset?: Asset;
}

export interface Transaction {
  id: number;
  portfolio_id: number;
  asset_id: number;
  transaction_type: 'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal';
  quantity: number;
  price: number;
  fee?: number;
  notes?: string;
  transaction_date: string;
  asset?: Asset;
}

export interface AssetPrice {
  id: number;
  symbol: string;
  name: string;
  asset_type: string;
  currency: string;
  current_price: number;
  high: number;
  low: number;
  open: number;
  previous_close: number;
  change: number;
  change_percent: number;
}

export interface PositionWithPrice {
  position_id: number;
  asset_id: number;
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
  change_percent: number;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
}

export interface CreateTransactionRequest {
  asset_id: number;
  transaction_type: 'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal';
  quantity: number;
  price: number;
  fee?: number;
  notes?: string;
  transaction_date?: string;
}
