import axios, { AxiosError } from 'axios';
import { cache, CacheKeys } from '../utils/cache';
import { errorHandler } from '../utils/errorHandler';
import { API_CONFIG } from '../config/api';
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

const API_BASE_URL = API_CONFIG.BASE_URL;


// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
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

// Response interceptor for token refresh and error handling
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    // Enregistrer l'erreur dans notre gestionnaire
    errorHandler.handleApiError(error);
    
    // Gestion du refresh token pour les erreurs 401
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
        // Enregistrer aussi l'erreur de refresh
        errorHandler.handleApiError(refreshError);
        removeAuthToken();
        
        // Redirection plus douce sans rechargement complet
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
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
  
  getRealETFs: async (symbols?: string, useCache: boolean = true): Promise<any> => {
    const cacheKey = symbols ? `${CacheKeys.REAL_ETFS}-${symbols}` : CacheKeys.REAL_ETFS;
    
    // Vérifier le cache d'abord
    if (useCache) {
      const cachedData = cache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }
    
    try {
      // Essayer d'abord l'endpoint avec authentification
      const response = await api.get('/real-market/real-etfs', { params: symbols ? { symbols } : {} });
      
      // Mettre en cache pour 30 secondes
      cache.set(cacheKey, response.data, 30);
      
      return response.data;
    } catch (error: any) {
      // Si échec d'authentification, utiliser l'endpoint public
      if (error.response?.status === 401) {
        console.log('🔄 Fallback vers l\'endpoint public etfs-preview');
        const fallbackResponse = await api.get('/real-market/public/etfs-preview');
        
        // Mettre en cache pour 30 secondes
        cache.set(cacheKey, fallbackResponse.data, 30);
        return fallbackResponse.data;
      }
      throw error;
    }
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

  // Real Market Data API
  getRealMarketData: async (symbol: string, period: string = '1mo'): Promise<any> => {
    const response = await api.get(`/real-market/real-market-data/${symbol}`, { 
      params: { period } 
    });
    return response.data;
  },

  getAvailableETFs: async (): Promise<any> => {
    const response = await api.get('/real-market/available-etfs');
    return response.data;
  },

  getMarketStatus: async (): Promise<any> => {
    const response = await api.get('/real-market/market-status');
    return response.data;
  },

  getEnhancedIndices: async (): Promise<any> => {
    const response = await api.get('/real-market/enhanced-indices');
    return response.data;
  },
};

export const signalsAPI = {
  getSignals: async (filters?: SignalFilters & PaginationParams): Promise<any> => {
    const response = await api.get('/signals', { params: filters });
    return response.data;
  },
  
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

  // Advanced Signals API
  getAdvancedSignals: async (params?: {
    min_confidence?: number;
    signal_types?: string;
    max_risk_score?: number;
    sectors?: string;
    limit?: number;
  }): Promise<any> => {
    const response = await api.get('/signals/advanced', { params });
    return response.data;
  },

  getWatchlistSignals: async (params?: {
    min_confidence?: number;
  }): Promise<any> => {
    const response = await api.get('/advanced-signals/signals/watchlist', { params });
    return response.data;
  },

  getSignalStatistics: async (params?: {
    days_back?: number;
  }): Promise<any> => {
    const response = await api.get('/advanced-signals/signals/statistics', { params });
    return response.data;
  },
};

export const portfolioAPI = {
  getPortfolios: async (): Promise<any> => {
    const response = await api.get('/portfolio');
    return response.data;
  },
  
  getPortfolioPositions: async (portfolioId: string): Promise<any> => {
    const response = await api.get(`/portfolio/${portfolioId}/positions`);
    return response.data;
  },
  
  getPortfolioTransactions: async (portfolioId: string): Promise<any> => {
    const response = await api.get(`/portfolio/${portfolioId}/transactions`);
    return response.data;
  },
  
  getPortfolioSummary: async (portfolioId: string): Promise<any> => {
    const response = await api.get(`/portfolio/${portfolioId}/summary`);
    return response.data;
  },
  
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
  
  createPortfolio: async (name: string): Promise<Portfolio> => {
    const response = await api.post('/portfolio/portfolios', { name });
    return response.data;
  },
  
  getTransactions: async (params?: PaginationParams): Promise<Transaction[]> => {
    const response = await api.get('/portfolio/transactions', { params });
    return response.data;
  },

  // Portfolio Management API
  getPortfolioManagement: {
    getPortfolios: async (): Promise<any> => {
      const response = await api.get('/portfolio-management/portfolios');
      return response.data;
    },
    
    getPortfolioDetails: async (portfolioId: string): Promise<any> => {
      const response = await api.get(`/portfolio-management/portfolios/${portfolioId}`);
      return response.data;
    },
    
    getPortfolioTransactions: async (portfolioId: string, params?: { limit?: number; offset?: number }): Promise<any> => {
      const response = await api.get(`/portfolio-management/portfolios/${portfolioId}/transactions`, { params });
      return response.data;
    },
    
    getPortfolioPerformance: async (portfolioId: string, period: string = '1M'): Promise<any> => {
      const response = await api.get(`/portfolio-management/portfolios/${portfolioId}/performance`, { 
        params: { period } 
      });
      return response.data;
    },
    
    createPortfolio: async (name: string, description?: string, isDefault?: boolean): Promise<any> => {
      const response = await api.post('/portfolio-management/portfolios', { 
        name, 
        description, 
        is_default: isDefault 
      });
      return response.data;
    },
    
    addPosition: async (portfolioId: string, position: {
      etf_isin: string;
      etf_symbol: string;
      quantity: number;
      price: number;
      fees?: number;
      notes?: string;
    }): Promise<any> => {
      const response = await api.post(`/portfolio-management/portfolios/${portfolioId}/positions`, position);
      return response.data;
    },
    
    sellPosition: async (portfolioId: string, positionId: string, sale: {
      quantity: number;
      price: number;
      fees?: number;
      notes?: string;
    }): Promise<any> => {
      const response = await api.post(`/portfolio-management/portfolios/${portfolioId}/positions/${positionId}/sell`, sale);
      return response.data;
    }
  }
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
    await api.patch(`/alerts/${alertId}/read`);
  },
  
  markAllAsRead: async (): Promise<void> => {
    await api.patch('/alerts/mark-all-read');
  },
  
  deleteAlert: async (alertId: string): Promise<void> => {
    await api.delete(`/alerts/${alertId}`);
  },
  
  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get('/alerts/unread-count');
    return response.data;
  },

  // Price Alerts API
  getPriceAlerts: async (): Promise<any[]> => {
    const response = await api.get('/alerts/price-alerts');
    return response.data;
  },

  createPriceAlert: async (alert: {
    etf_symbol: string;
    target_price: number;
    alert_type: 'above' | 'below';
    message?: string;
    is_active: boolean;
  }): Promise<any> => {
    const response = await api.post('/alerts/price-alerts', alert);
    return response.data;
  },

  updatePriceAlert: async (alertId: string, update: {
    target_price?: number;
    alert_type?: 'above' | 'below';
    message?: string;
    is_active?: boolean;
  }): Promise<any> => {
    const response = await api.patch(`/alerts/price-alerts/${alertId}`, update);
    return response.data;
  },

  deletePriceAlert: async (alertId: string): Promise<void> => {
    await api.delete(`/alerts/price-alerts/${alertId}`);
  },

  getActivePriceAlerts: async (): Promise<any[]> => {
    const response = await api.get('/alerts/price-alerts/active');
    return response.data;
  },
};

// Real-time Market Data API
export const realtimeMarketAPI = {
  getRealtimeQuote: async (symbol: string): Promise<any> => {
    const response = await api.get(`/realtime-market/realtime/${symbol}`);
    return response.data;
  },

  getMultipleQuotes: async (symbols: string[]): Promise<any> => {
    const symbolsParam = symbols.join(',');
    const response = await api.get(`/realtime-market/realtime/multiple?symbols=${symbolsParam}`);
    return response.data;
  },

  getIntradayData: async (symbol: string, hours: number = 24): Promise<any> => {
    const response = await api.get(`/realtime-market/intraday/${symbol}?hours=${hours}`);
    return response.data;
  },

  getMarketOverview: async (): Promise<any> => {
    const response = await api.get('/realtime-market/market-overview');
    return response.data;
  },

  getWatchlistData: async (): Promise<any> => {
    const response = await api.get('/realtime-market/watchlist');
    return response.data;
  },

  getMarketStatus: async (): Promise<any> => {
    const response = await api.get('/realtime-market/market-status');
    return response.data;
  },

  startDataCollection: async (): Promise<any> => {
    const response = await api.post('/realtime-market/data-collection/start');
    return response.data;
  },

  getRealtimeStats: async (): Promise<any> => {
    const response = await api.get('/realtime-market/stats');
    return response.data;
  },

  // WebSocket URL helper
  getWebSocketUrl: (): string => {
    const isSecure = API_CONFIG.BASE_URL.startsWith('https://');
    const protocol = isSecure ? 'wss:' : 'ws:';
    const apiHost = API_CONFIG.BASE_URL.replace('http://', '').replace('https://', '');
    return `${protocol}//${apiHost}/api/v1/ws/market-data`;
  }
};

// Export utilities
export { setAuthToken, removeAuthToken, getAuthToken };

export default api;