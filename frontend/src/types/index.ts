// User types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  user_id: string;
  risk_tolerance: number;
  min_signal_confidence: number;
  notification_settings: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  trading_preferences: {
    max_position_size: number;
    stop_loss_pct: number;
  };
  created_at: string;
  updated_at: string;
}

// ETF types
export interface ETF {
  isin: string;
  name: string;
  sector?: string;
  currency: string;
  ter?: number;
  aum?: number;
  exchange?: string;
  created_at: string;
  updated_at: string;
}

export interface MarketData {
  time: string;
  etf_isin: string;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  close_price?: number;
  volume?: number;
  nav?: number;
}

export interface TechnicalIndicators {
  time: string;
  etf_isin: string;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_20?: number;
  ema_50?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  atr?: number;
  obv?: number;
  vwap?: number;
}

// Signal types
export type SignalType = 'BUY' | 'SELL' | 'HOLD' | 'WAIT';

export interface Signal {
  id: string;
  etf_isin: string;
  signal_type: SignalType;
  confidence: number;
  price_target?: number;
  stop_loss?: number;
  technical_score?: number;
  fundamental_score?: number;
  risk_score?: number;
  created_at: string;
  expires_at?: string;
  is_active: boolean;
}

// Portfolio types
export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Position {
  id: string;
  portfolio_id: string;
  etf_isin: string;
  quantity: number;
  average_price: number;
  created_at: string;
  updated_at: string;
}

export type TransactionType = 'BUY' | 'SELL';

export interface Transaction {
  id: string;
  portfolio_id: string;
  etf_isin: string;
  transaction_type: TransactionType;
  quantity: number;
  price: number;
  fees: number;
  created_at: string;
}

// Alert types
export type AlertType = 'SIGNAL' | 'EVENT' | 'RISK' | 'NEWS';

export interface Alert {
  id: string;
  user_id: string;
  alert_type: AlertType;
  title: string;
  message: string;
  etf_isin?: string;
  is_read: boolean;
  created_at: string;
}

// Watchlist types
export interface WatchlistItem {
  id: string;
  user_id: string;
  etf_isin: string;
  created_at: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Chart data types
export interface ChartDataPoint {
  x: string | number;
  y: number;
}

export interface OHLCData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Dashboard data types
export interface DashboardData {
  markets: {
    name: string;
    value: number;
    change: number;
  }[];
  activeSignals: Signal[];
  portfolioSummary: {
    total_value: number;
    total_gain_loss: number;
    total_gain_loss_percent: number;
    day_change: number;
    day_change_percent: number;
    positions_count: number;
    cash_balance: number;
  };
  watchlistItems: WatchlistItem[];
}

// Filter and sort types
export interface SignalFilters {
  signal_type?: SignalType;
  min_confidence?: number;
  etf_isin?: string;
  start_date?: string;
  end_date?: string;
}

export interface PaginationParams {
  skip: number;
  limit: number;
}

// Loading and error states
export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

export interface AsyncState<T> extends LoadingState {
  data?: T;
}

// Navigation types
export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  current: boolean;
}