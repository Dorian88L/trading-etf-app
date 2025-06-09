import React from 'react';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

class SimpleCache {
  private cache = new Map<string, CacheItem<any>>();

  set<T>(key: string, data: T, ttlSeconds: number = 300): void {
    const now = Date.now();
    this.cache.set(key, {
      data,
      timestamp: now,
      expiry: now + (ttlSeconds * 1000)
    });
  }

  get<T>(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }

    const now = Date.now();
    if (now > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    return item.data as T;
  }

  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) return false;
    
    const now = Date.now();
    if (now > item.expiry) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    // Nettoyer les entrées expirées
    const now = Date.now();
    for (const [key, item] of Array.from(this.cache.entries())) {
      if (now > item.expiry) {
        this.cache.delete(key);
      }
    }
    return this.cache.size;
  }

  // Obtenir les statistiques du cache
  getStats() {
    const now = Date.now();
    let validEntries = 0;
    let expiredEntries = 0;

    for (const [, item] of Array.from(this.cache.entries())) {
      if (now > item.expiry) {
        expiredEntries++;
      } else {
        validEntries++;
      }
    }

    return {
      total: this.cache.size,
      valid: validEntries,
      expired: expiredEntries
    };
  }
}

// Instance globale du cache
export const cache = new SimpleCache();

// Hook React pour utiliser le cache
export const useCache = <T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds: number = 300
) => {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchData = React.useCallback(async (force = false) => {
    // Vérifier le cache d'abord
    if (!force) {
      const cachedData = cache.get<T>(key);
      if (cachedData) {
        setData(cachedData);
        return cachedData;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetcher();
      cache.set(key, result, ttlSeconds);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [key, fetcher, ttlSeconds]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchData(true),
    invalidate: () => cache.delete(key)
  };
};

// Utilitaires pour les clés de cache
export const CacheKeys = {
  REAL_ETFS: 'real-etfs',
  SIGNALS: 'signals',
  PORTFOLIO: 'portfolio',
  ALERTS: 'alerts',
  USER_PREFERENCES: 'user-preferences',
  
  // Constructeurs de clés dynamiques
  etfData: (symbol: string) => `etf-${symbol}`,
  marketData: (symbol: string, period: string) => `market-${symbol}-${period}`,
  technicalIndicators: (symbol: string) => `technical-${symbol}`,
} as const;

export default cache;