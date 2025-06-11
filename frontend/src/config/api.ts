export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    // Real Market endpoints (correcter paths)
    REAL_ETFS: '/api/v1/real-market/real-etfs',
    AVAILABLE_ETFS: '/api/v1/real-market/available-etfs',
    REAL_INDICES: '/api/v1/real-market/real-indices',
    HISTORICAL: '/api/v1/real-market/real-market-data',
    MARKET_DATA: '/api/v1/market-data',
    INDICES: '/api/v1/indices',
    DASHBOARD_STATS: '/api/v1/real-market/dashboard-stats',
    SECTORS: '/api/v1/real-market/sectors',
    
    // Portfolio endpoints (à implémenter)
    PORTFOLIO_PERFORMANCE: '/api/v1/portfolio/performance',
    PORTFOLIO_POSITIONS: '/api/v1/portfolio/positions',
    PORTFOLIO_SUMMARY: '/api/v1/portfolio/summary',
    
    // Signals endpoints
    ADVANCED_SIGNALS: '/api/v1/signals/advanced',
    
    // Auth endpoints
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    
    // User endpoints
    USER_PROFILE: '/api/v1/user/profile'
  }
};

export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

export const getBaseApiUrl = (): string => {
  return API_CONFIG.BASE_URL;
};