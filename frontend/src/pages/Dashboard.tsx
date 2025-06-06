import React, { useState } from 'react';
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

const Dashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'1D' | '1W' | '1M' | '3M'>('1W');
  const [realTimeData, setRealTimeData] = useState(true);

  // Enhanced mock data with advanced signals
  const stats = [
    {
      name: 'Portfolio Value',
      value: '€125,430',
      change: '+2.1%',
      changeType: 'positive',
      icon: CurrencyDollarIcon,
    },
    {
      name: 'Active Signals',
      value: '12',
      change: '+3',
      changeType: 'positive',
      icon: ArrowTrendingUpIcon,
    },
    {
      name: 'Today P&L',
      value: '€1,250',
      change: '+0.8%',
      changeType: 'positive',
      icon: ChartBarIcon,
    },
    {
      name: 'Alerts',
      value: '5',
      change: 'New',
      changeType: 'neutral',
      icon: BellIcon,
    },
  ];

  // Advanced signals data
  const advancedSignals = [
    {
      id: 'sig_001',
      etf_isin: 'FR0010296061',
      etf_name: 'Lyxor CAC 40 UCITS ETF',
      signal_type: 'BUY' as const,
      algorithm_type: 'BREAKOUT' as const,
      confidence: 87.5,
      technical_score: 82.3,
      fundamental_score: 75.8,
      risk_score: 68.2,
      current_price: 52.30,
      price_target: 56.40,
      stop_loss: 49.80,
      expected_return: 7.8,
      risk_reward_ratio: 1.64,
      holding_period: 5,
      justification: 'Signal BUY - Algorithme Cassure. Score composite: 87.5/100. Indicateurs clés: RSI favorable, Volume élevé.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      sector: 'Large Cap France'
    },
    {
      id: 'sig_002',
      etf_isin: 'IE00B4L5Y983',
      etf_name: 'iShares Core MSCI World UCITS ETF',
      signal_type: 'SELL' as const,
      algorithm_type: 'MEAN_REVERSION' as const,
      confidence: 73.2,
      technical_score: 45.6,
      fundamental_score: 89.4,
      risk_score: 71.8,
      current_price: 71.45,
      price_target: 68.20,
      stop_loss: 74.50,
      expected_return: -4.5,
      risk_reward_ratio: 1.07,
      holding_period: 3,
      justification: 'Signal SELL - Algorithme Retour à la moyenne. Score composite: 73.2/100. Indicateurs clés: RSI surachat, MACD divergence.',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      sector: 'Global Developed'
    },
    {
      id: 'sig_003',
      etf_isin: 'LU0290358497',
      etf_name: 'Xtrackers EURO STOXX 50 UCITS ETF',
      signal_type: 'HOLD' as const,
      algorithm_type: 'MOMENTUM' as const,
      confidence: 65.8,
      technical_score: 58.9,
      fundamental_score: 72.1,
      risk_score: 67.4,
      current_price: 45.20,
      price_target: 46.10,
      stop_loss: 44.30,
      expected_return: 2.0,
      risk_reward_ratio: 1.0,
      holding_period: 7,
      justification: 'Signal HOLD - Algorithme Momentum. Score composite: 65.8/100. Position consolidée.',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      sector: 'Europe Large Cap'
    },
    {
      id: 'sig_004',
      etf_isin: 'IE00B4L5YC18',
      etf_name: 'iShares Core S&P 500 UCITS ETF',
      signal_type: 'BUY' as const,
      algorithm_type: 'MOMENTUM' as const,
      confidence: 91.3,
      technical_score: 94.2,
      fundamental_score: 88.7,
      risk_score: 85.1,
      current_price: 425.80,
      price_target: 448.20,
      stop_loss: 405.30,
      expected_return: 5.3,
      risk_reward_ratio: 1.09,
      holding_period: 10,
      justification: 'Signal BUY - Algorithme Momentum. Score composite: 91.3/100. Indicateurs clés: Tendance forte, Volume confirmé.',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      sector: 'US Large Cap'
    }
  ];

  // Sample market data for charts
  const sampleMarketData = [
    { timestamp: '2024-01-15T09:00:00Z', open_price: 50.2, high_price: 51.8, low_price: 50.0, close_price: 51.5, volume: 2500000 },
    { timestamp: '2024-01-16T09:00:00Z', open_price: 51.5, high_price: 52.3, low_price: 51.1, close_price: 52.0, volume: 2800000 },
    { timestamp: '2024-01-17T09:00:00Z', open_price: 52.0, high_price: 52.8, low_price: 51.7, close_price: 52.3, volume: 3100000 },
    { timestamp: '2024-01-18T09:00:00Z', open_price: 52.3, high_price: 53.1, low_price: 52.0, close_price: 52.8, volume: 2900000 },
    { timestamp: '2024-01-19T09:00:00Z', open_price: 52.8, high_price: 53.5, low_price: 52.5, close_price: 53.2, volume: 3200000 },
  ];


  const handleSignalClick = (signal: any) => {
    console.log('Signal clicked:', signal);
    // Navigation vers la page détaillée de l'ETF
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header amélioré */}
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
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Live</span>
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
      <MarketOverview />

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
              data={sampleMarketData}
              etfName="Lyxor CAC 40"
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
            <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              3 nouvelles
            </span>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
              Configurer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;