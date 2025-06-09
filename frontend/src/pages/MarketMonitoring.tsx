import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ServerIcon, 
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SignalIcon,
  ComputerDesktopIcon,
  GlobeAltIcon 
} from '@heroicons/react/24/outline';
import RealTimeMarketData from '../components/RealTimeMarketData';
import { realtimeMarketAPI } from '../services/api';

interface MarketStatus {
  global_status: string;
  open_markets_count: number;
  markets: {
    [key: string]: {
      status: string;
      description: string;
      trading_hours: string;
    };
  };
  server_time: string;
  timezone: string;
}

interface RealtimeStats {
  service_status: string;
  connected_websockets: number;
  cached_symbols: number;
  watchlist_size: number;
  last_updates: {
    [symbol: string]: string;
  };
  data_sources: {
    [source: string]: any;
  };
  uptime: string;
}

const MarketMonitoring: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null);
  const [marketOverview, setMarketOverview] = useState<any>(null);
  // const [watchlistData, setWatchlistData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      const [statusRes, statsRes, overviewRes] = await Promise.allSettled([
        realtimeMarketAPI.getMarketStatus(),
        realtimeMarketAPI.getRealtimeStats(),
        realtimeMarketAPI.getMarketOverview()
      ]);

      if (statusRes.status === 'fulfilled') {
        setMarketStatus(statusRes.value.data);
      }
      
      if (statsRes.status === 'fulfilled') {
        setRealtimeStats(statsRes.value.data);
      }
      
      if (overviewRes.status === 'fulfilled') {
        setMarketOverview(overviewRes.value.data);
      }
      
      // if (watchlistRes.status === 'fulfilled') {
      //   setWatchlistData(watchlistRes.value.data);
      // }
      
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Erreur lors du chargement des données de monitoring:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAllData, 30000); // Refresh toutes les 30s
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
      case 'active':
      case 'connected':
        return 'text-green-500 bg-green-100';
      case 'closed':
      case 'inactive':
        return 'text-red-500 bg-red-100';
      case 'pre_market':
      case 'after_hours':
        return 'text-yellow-500 bg-yellow-100';
      default:
        return 'text-gray-500 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
      case 'active':
        return <CheckCircleIcon className="h-5 w-5" />;
      case 'closed':
      case 'inactive':
        return <ExclamationTriangleIcon className="h-5 w-5" />;
      default:
        return <ClockIcon className="h-5 w-5" />;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffMins < 1440) return `Il y a ${Math.floor(diffMins / 60)} h`;
    return `Il y a ${Math.floor(diffMins / 1440)} j`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ComputerDesktopIcon className="h-8 w-8 text-blue-600 mr-3" />
            Monitoring Système
          </h1>
          <p className="text-gray-600 mt-1">
            Surveillance en temps réel des marchés et services
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${autoRefresh ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className="text-sm text-gray-600">
              Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            MAJ: {lastRefresh.toLocaleTimeString('fr-FR')}
          </div>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-2 rounded-lg text-sm font-medium ${
              autoRefresh 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {autoRefresh ? 'Auto ON' : 'Auto OFF'}
          </button>
          <button
            onClick={fetchAllData}
            className="px-3 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium hover:bg-blue-200"
            disabled={loading}
          >
            {loading ? '🔄' : '↻'} Actualiser
          </button>
        </div>
      </div>

      {/* Statut des marchés */}
      {marketStatus && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <GlobeAltIcon className="h-6 w-6 text-blue-600 mr-2" />
            Statut des Marchés Mondiaux
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Statut Global</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(marketStatus.global_status)}`}>
                  {getStatusIcon(marketStatus.global_status)}
                  <span className="ml-1">{marketStatus.global_status}</span>
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Marchés Ouverts</span>
                <span className="text-lg font-bold text-gray-900">
                  {marketStatus.open_markets_count}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Heure Serveur</span>
                <span className="text-sm text-gray-600">
                  {new Date(marketStatus.server_time).toLocaleTimeString('fr-FR')} {marketStatus.timezone}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(marketStatus.markets).map(([region, market]) => (
              <div key={region} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{market.description}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(market.status)}`}>
                    {getStatusIcon(market.status)}
                    <span className="ml-1">{market.status}</span>
                  </span>
                </div>
                <p className="text-sm text-gray-600">{market.trading_hours}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistiques du service temps réel */}
      {realtimeStats && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <ServerIcon className="h-6 w-6 text-green-600 mr-2" />
            Service Temps Réel
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-700">Service</p>
                  <p className="text-lg font-bold text-gray-900">{realtimeStats.service_status}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <SignalIcon className="h-8 w-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-700">WebSockets</p>
                  <p className="text-lg font-bold text-gray-900">{realtimeStats.connected_websockets}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-700">Symboles en Cache</p>
                  <p className="text-lg font-bold text-gray-900">{realtimeStats.cached_symbols}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-orange-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-700">Watchlist</p>
                  <p className="text-lg font-bold text-gray-900">{realtimeStats.watchlist_size}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sources de données */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3">Sources de Données</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(realtimeStats.data_sources).map(([source, config]) => (
                <div key={source} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium capitalize">{source}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      config.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {config.enabled ? 'Actif' : 'Inactif'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Limite: {config.rate_limit}/min | Priorité: {config.priority}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Dernières mises à jour */}
          <div>
            <h3 className="text-lg font-medium mb-3">Dernières Mises à Jour</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Symbole</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Dernière MAJ</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Il y a</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {Object.entries(realtimeStats.last_updates).slice(0, 8).map(([symbol, timestamp]) => (
                    <tr key={symbol}>
                      <td className="px-4 py-2 font-medium text-gray-900">{symbol}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">
                        {new Date(timestamp).toLocaleTimeString('fr-FR')}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-500">
                        {formatTimeAgo(timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Aperçu du marché */}
      {marketOverview && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Aperçu du Marché</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700">Symboles Actifs</p>
              <p className="text-2xl font-bold text-gray-900">{marketOverview.active_symbols}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700">Sentiment</p>
              <p className={`text-2xl font-bold ${
                marketOverview.market_status === 'bullish' ? 'text-green-600' :
                marketOverview.market_status === 'bearish' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {marketOverview.market_status}
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700">Hausses</p>
              <p className="text-2xl font-bold text-green-600">{marketOverview.market_trends?.positive_count || 0}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700">Baisses</p>
              <p className="text-2xl font-bold text-red-600">{marketOverview.market_trends?.negative_count || 0}</p>
            </div>
          </div>

          {/* Top gainers/losers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-3 text-green-600">Top Gainers</h3>
              <div className="space-y-2">
                {marketOverview.top_gainers?.slice(0, 3).map((item: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <span className="font-medium">{item.symbol}</span>
                    <span className="text-green-600 font-bold">
                      +{item.change_percent?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-3 text-red-600">Top Losers</h3>
              <div className="space-y-2">
                {marketOverview.top_losers?.slice(0, 3).map((item: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <span className="font-medium">{item.symbol}</span>
                    <span className="text-red-600 font-bold">
                      {item.change_percent?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Données temps réel WebSocket */}
      <RealTimeMarketData 
        autoConnect={true}
        onDataUpdate={(data) => {
          console.log('Données WebSocket mises à jour:', Object.keys(data).length, 'symboles');
        }}
      />
    </div>
  );
};

export default MarketMonitoring;