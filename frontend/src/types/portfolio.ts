export interface Portfolio {
  id: string;  // UUID
  name: string;
  description?: string;
  created_at: string;
  user_id: string;  // UUID
}

export interface Asset {
  id: string;  // UUID
  symbol: string;
  name: string;
  asset_type: 'stock' | 'crypto' | 'etf' | 'bond' | 'commodity' | 'cash';
  market?: string;
  currency: string;
  created_at: string;
  updated_at?: string;
}

export interface Position {
  id: string;  // UUID
  portfolio_id: string;  // UUID
  asset_id: string;  // UUID
  quantity: number;
  average_price: number;
  asset?: Asset;
}

export interface Transaction {
  id: string;  // UUID
  portfolio_id: string;  // UUID
  asset_id: string;  // UUID
  transaction_type: 'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal';
  quantity: number;
  price: number;
  fee?: number;
  currency: string;
  notes?: string;
  transaction_date: string;
  asset?: Asset;
}

export interface AssetPrice {
  id: string;  // UUID
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
  position_id: string;  // UUID
  asset_id: string;  // UUID
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
  asset_id: string;  // UUID
  transaction_type: 'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal';
  quantity: number;
  price: number;
  fee?: number;
  currency?: string;
  notes?: string;
  transaction_date?: string;
}
