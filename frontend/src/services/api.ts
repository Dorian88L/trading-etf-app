import axios, { AxiosResponse, AxiosError } from 'axios';
import { 
  User, 
  UserPreferences, 
  ETF, 
  MarketData, 
  TechnicalIndicators,
  Signal, 
  Portfolio, 
  Position, 
  Transaction, 
  Alert, 
  WatchlistItem,
  LoginCredentials,
  RegisterData,
  AuthTokens,
  SignalFilters,
  PaginationParams
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth token management
const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const setAuthToken = (token: string): void => {
  localStorage.setItem('access_token', token);
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

const removeAuthToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  delete api.defaults.headers.common['Authorization'];
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await api.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          setAuthToken(access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          return api(originalRequest);
        }
      } catch (refreshError) {
        removeAuthToken();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  register: async (userData: RegisterData): Promise<User> => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
};

export const userAPI = {
  getProfile: async (): Promise<User> => {
    const response = await api.get('/user/profile');
    return response.data;
  },
  
  getPreferences: async (): Promise<UserPreferences> => {
    const response = await api.get('/user/preferences');
    return response.data;
  },
  
  updatePreferences: async (preferences: Partial<UserPreferences>): Promise<UserPreferences> => {
    const response = await api.put('/user/preferences', preferences);
    return response.data;
  },
  
  getWatchlist: async (): Promise<WatchlistItem[]> => {
    const response = await api.get('/user/watchlist');
    return response.data;
  },
  
  addToWatchlist: async (etfIsin: string): Promise<void> => {
    await api.post('/user/watchlist', { etf_isin: etfIsin });
  },
  
  removeFromWatchlist: async (etfIsin: string): Promise<void> => {
    await api.delete(`/user/watchlist/${etfIsin}`);
  },
};

export const marketAPI = {
  getETFs: async (params?: { 
    skip?: number; 
    limit?: number; 
    sector?: string; 
    currency?: string 
  }): Promise<ETF[]> => {
    const response = await api.get('/market/etfs', { params });
    return response.data;
  },
  
  getETF: async (isin: string): Promise<ETF> => {
    const response = await api.get(`/market/etf/${isin}`);
    return response.data;
  },
  
  getMarketData: async (
    isin: string, 
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<MarketData[]> => {
    const response = await api.get(`/market/etf/${isin}/market-data`, { params });
    return response.data;
  },
  
  getTechnicalIndicators: async (
    isin: string,
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<TechnicalIndicators[]> => {
    const response = await api.get(`/market/etf/${isin}/technical-indicators`, { params });
    return response.data;
  },
  
  getSectors: async (): Promise<string[]> => {
    const response = await api.get('/market/sectors');
    return response.data;
  },
  
  getIndices: async (): Promise<any[]> => {
    const response = await api.get('/market/indices');
    return response.data;
  },
};

export const signalsAPI = {
  getActiveSignals: async (filters?: SignalFilters & PaginationParams): Promise<Signal[]> => {
    const response = await api.get('/signals/active', { params: filters });
    return response.data;
  },
  
  getSignalHistory: async (filters?: SignalFilters & PaginationParams): Promise<Signal[]> => {
    const response = await api.get('/signals/history', { params: filters });
    return response.data;
  },
  
  getSignal: async (signalId: string): Promise<Signal> => {
    const response = await api.get(`/signals/${signalId}`);
    return response.data;
  },
  
  getLatestSignalsForETF: async (isin: string, limit?: number): Promise<Signal[]> => {
    const response = await api.get(`/signals/etf/${isin}/latest`, { 
      params: { limit } 
    });
    return response.data;
  },
  
  getTopPerformingSignals: async (params?: { limit?: number; days?: number }): Promise<any[]> => {
    const response = await api.get('/signals/top-performers', { params });
    return response.data;
  },
};

export const portfolioAPI = {
  getPositions: async (): Promise<Position[]> => {
    const response = await api.get('/portfolio/positions');
    return response.data;
  },
  
  createTransaction: async (transaction: {
    portfolio_id: string;
    etf_isin: string;
    transaction_type: 'BUY' | 'SELL';
    quantity: number;
    price: number;
    fees?: number;
  }): Promise<Transaction> => {
    const response = await api.post('/portfolio/transaction', transaction);
    return response.data;
  },
  
  getPerformance: async (): Promise<any> => {
    const response = await api.get('/portfolio/performance');
    return response.data;
  },
  
  getPortfolios: async (): Promise<Portfolio[]> => {
    const response = await api.get('/portfolio/portfolios');
    return response.data;
  },
  
  createPortfolio: async (name: string): Promise<Portfolio> => {
    const response = await api.post('/portfolio/portfolios', { name });
    return response.data;
  },
  
  getTransactions: async (params?: PaginationParams): Promise<Transaction[]> => {
    const response = await api.get('/portfolio/transactions', { params });
    return response.data;
  },
};

export const alertsAPI = {
  getAlerts: async (params?: {
    skip?: number;
    limit?: number;
    alert_type?: string;
    is_read?: boolean;
  }): Promise<Alert[]> => {
    const response = await api.get('/alerts/', { params });
    return response.data;
  },
  
  createAlert: async (alert: {
    alert_type: string;
    title: string;
    message: string;
    etf_isin?: string;
  }): Promise<Alert> => {
    const response = await api.post('/alerts/', alert);
    return response.data;
  },
  
  markAsRead: async (alertId: string): Promise<void> => {
    await api.put(`/alerts/${alertId}/read`);
  },
  
  markAllAsRead: async (): Promise<void> => {
    await api.put('/alerts/mark-all-read');
  },
  
  deleteAlert: async (alertId: string): Promise<void> => {
    await api.delete(`/alerts/${alertId}`);
  },
  
  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get('/alerts/unread-count');
    return response.data;
  },
};

// Export utilities
export { setAuthToken, removeAuthToken, getAuthToken };

export default api;