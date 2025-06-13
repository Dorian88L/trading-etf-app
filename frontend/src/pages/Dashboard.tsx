import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  CurrencyDollarIcon,
  BellIcon,
  SparklesIcon,
  RocketLaunchIcon 
} from '@heroicons/react/24/outline';
import MarketOverview from '../components/dashboard/MarketOverview';
import SignalsPanel from '../components/dashboard/SignalsPanel';
import AdvancedChart from '../components/charts/AdvancedChart';
import RealTimeNotification from '../components/RealTimeNotification';
import RealTimeMarketData from '../components/RealTimeMarketData';
import SmartSearch from '../components/SmartSearch';
import { getApiUrl, API_CONFIG } from '../config/api';
import { marketAPI } from '../services/api';

interface DashboardStats {
  market_overview: {
    total_etfs: number;
    avg_change_percent: number;
    positive_etfs: number;
    negative_etfs: number;
  };
  alerts_count: number;
  last_update: string;
}

const Dashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'1D' | '1W' | '1M' | '3M'>('1W');
  const [realTimeData, setRealTimeData] = useState(true);
  const [marketData, setMarketData] = useState<any[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Charger les données réelles
  useEffect(() => {
    fetchRealData();
    
    // Actualiser toutes les 30 secondes si en temps réel
    const interval = realTimeData ? setInterval(fetchRealData, 30000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [realTimeData]);

  const fetchRealData = async () => {
    try {
      // Récupérer les données ETF réelles
      const etfsResponse = await marketAPI.getRealETFs();
      
      // Récupérer les stats du dashboard depuis l'API
      try {
        const statsResponse = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.DASHBOARD_STATS), {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setDashboardStats(statsData.data);
        }
      } catch (error) {
        console.log('Dashboard stats API not available');
      }
      
      setMarketData(etfsResponse.data || []);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Erreur de récupération:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculer les stats basées sur les vraies données du marché
  const calculateStats = (): any[] => {
    if (!dashboardStats) return [];
    
    const { market_overview, alerts_count } = dashboardStats;
    
    return [
      {
        name: 'Marché Global',
        value: `${market_overview.total_etfs} ETFs`,
        change: `${market_overview.avg_change_percent >= 0 ? '+' : ''}${market_overview.avg_change_percent.toFixed(2)}%`,
        changeType: market_overview.avg_change_percent >= 0 ? 'positive' : 'negative',
        icon: CurrencyDollarIcon,
      },
      {
        name: 'ETFs Positifs',
        value: `${market_overview.positive_etfs}/${market_overview.total_etfs}`,
        change: `${((market_overview.positive_etfs / market_overview.total_etfs) * 100).toFixed(1)}%`,
        changeType: 'positive',
        icon: ArrowTrendingUpIcon,
      },
      {
        name: 'Performance Moyenne',
        value: `${market_overview.avg_change_percent >= 0 ? '+' : ''}${market_overview.avg_change_percent.toFixed(2)}%`,
        change: 'En temps réel',
        changeType: market_overview.avg_change_percent >= 0 ? 'positive' : 'negative',
        icon: ChartBarIcon,
      },
      {
        name: 'Alertes',
        value: alerts_count.toString(),
        change: 'Mouvements > 2%',
        changeType: alerts_count > 0 ? 'neutral' : 'positive',
        icon: BellIcon,
      },
    ];
  };

  // Enhanced mock data with advanced signals
  const stats: any[] = calculateStats();

  // Récupérer les signaux depuis l'API plutôt que des données hardcodées
  const [advancedSignals, setAdvancedSignals] = useState<any[]>([]);

  // Charger les signaux depuis l'API
  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.ADVANCED_SIGNALS));
        if (response.ok) {
          const data = await response.json();
          setAdvancedSignals(data.data || []);
        }
      } catch (error) {
        // Signaux non disponibles
        setAdvancedSignals([]);
      }
    };
    
    fetchSignals();
  }, []);

  const [chartData, setChartData] = useState<any[]>([]);
  
  // Load chart data from API
  useEffect(() => {
    const fetchChartData = async () => {
      if (marketData.length > 0) {
        try {
          const firstEtf = marketData[0];
          const response = await fetch(getApiUrl(`${API_CONFIG.ENDPOINTS.HISTORICAL}/${firstEtf.symbol}?period=1W`));
          if (response.ok) {
            const data = await response.json();
            setChartData(data.data || []);
          }
        } catch (error) {
          console.error('Erreur lors du chargement des données de graphique:', error);
        }
      }
    };
    
    fetchChartData();
  }, [marketData]);


  const handleSignalClick = (signal: any) => {
    console.log('Signal clicked:', signal);
    // Navigation vers la page détaillée de l'ETF
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header amélioré */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <SparklesIcon className="h-8 w-8 text-blue-600 mr-3" />
              Trading ETF Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Analyse avancée et signaux automatisés • Données temps réel
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <div className={`w-3 h-3 rounded-full ${realTimeData ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className="text-sm text-gray-600">
              {realTimeData ? 'Live' : 'Hors ligne'}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            MAJ: {lastUpdate.toLocaleTimeString('fr-FR')}
          </div>
          <button
            onClick={() => setRealTimeData(!realTimeData)}
            className={`px-3 py-2 rounded-lg text-sm font-medium ${
              realTimeData 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {realTimeData ? 'Temps réel activé' : 'Temps réel désactivé'}
          </button>
          <button
            onClick={fetchRealData}
            className="px-3 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium hover:bg-blue-200"
            disabled={loading}
          >
            {loading ? '🔄' : '↻'} Actualiser
          </button>
        </div>
        
        {/* Barre de recherche intelligente */}
        <div className="max-w-2xl">
          <SmartSearch className="w-full" />
        </div>
      </div>

      {/* Stats Grid amélioré */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <stat.icon className="h-8 w-8 text-blue-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                  <p className={`ml-2 text-sm font-semibold ${
                    stat.changeType === 'positive' 
                      ? 'text-green-600' 
                      : stat.changeType === 'negative'
                      ? 'text-red-600'
                      : 'text-gray-500'
                  }`}>
                    {stat.change}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Vue des marchés */}
      <MarketOverview 
        indices={marketData.map(etf => ({
          name: etf.name || etf.symbol,
          symbol: etf.symbol,
          value: etf.current_price || 0,
          change: etf.price_change || 0,
          changePercent: etf.change_percent || 0,
          volume: etf.volume,
          region: etf.currency === 'EUR' ? 'Europe' : 'International'
        }))}
        lastUpdate={lastUpdate.toLocaleTimeString('fr-FR')}
      />

      {/* Signaux avancés et graphique */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Panneau des signaux (2/3) */}
        <div className="xl:col-span-2">
          <SignalsPanel 
            signals={advancedSignals} 
            onSignalClick={handleSignalClick}
            maxSignals={6}
          />
        </div>
        
        {/* Graphique rapide (1/3) */}
        <div className="xl:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Vue Rapide</h3>
              <div className="flex space-x-1">
                {(['1D', '1W', '1M', '3M'] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setSelectedPeriod(period)}
                    className={`px-2 py-1 text-xs rounded ${
                      selectedPeriod === period
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {period}
                  </button>
                ))}
              </div>
            </div>
            
            <AdvancedChart
              data={chartData}
              etfName={marketData.length > 0 ? marketData[0]?.name || marketData[0]?.symbol : "Aperçu Marché"}
              chartType="line"
              showIndicators={false}
              height={200}
            />
            
            {/* Actions rapides */}
            <div className="mt-4 space-y-2">
              <button className="w-full bg-green-50 text-green-700 hover:bg-green-100 py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                <RocketLaunchIcon className="h-4 w-4 inline mr-2" />
                Analyser en détail
              </button>
              <button className="w-full bg-blue-50 text-blue-700 hover:bg-blue-100 py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                📊 Vue technique avancée
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Section d'alertes et notifications */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BellIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Alertes Intelligentes</h3>
              <p className="text-sm text-gray-600">Notifications en temps réel basées sur vos préférences</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {(dashboardStats?.alerts_count ?? 0) > 0 && (
              <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                {dashboardStats?.alerts_count ?? 0} nouvelles
              </span>
            )}
            <button 
              onClick={() => {
                // Ouvrir le centre de notifications
                const event = new CustomEvent('openNotificationCenter');
                window.dispatchEvent(event);
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Configurer
            </button>
          </div>
        </div>
      </div>

      {/* Données de marché temps réel WebSocket */}
      <RealTimeMarketData 
        symbols={marketData.slice(0, 8).map(etf => etf.symbol)}
        autoConnect={realTimeData}
        onDataUpdate={(data) => {
          // Mise à jour des données locales avec les données WebSocket
          console.log('Données temps réel reçues:', data);
        }}
      />

      {/* Notifications en temps réel */}
      <RealTimeNotification marketData={marketData} />
    </div>
  );
};

export default Dashboard;