import React, { useState, useEffect } from 'react';
import { signalsAPI } from '../services/api';
import useAdvancedNotifications from '../hooks/useAdvancedNotifications';

interface Signal {
  id: string;
  symbol: string;
  name: string;
  signalType: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  currentPrice: number;
  targetPrice: number;
  stopLoss: number;
  timeframe: '1H' | '4H' | '1D' | '1W';
  strategy: string;
  createdAt: string;
  expiresAt: string;
  isActive: boolean;
  volume: number;
  change24h: number;
  rsi: number;
  macd: number;
  technicalScore: number;
  fundamentalScore: number;
  marketCap: number;
  sector: string;
}

interface SignalFilter {
  type: 'ALL' | 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  timeframe: 'ALL' | '1H' | '4H' | '1D' | '1W';
  sector: 'ALL' | string;
  strategy: 'ALL' | string;
}

const Signals: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'active' | 'history' | 'analysis' | 'alerts'>('active');
  const [signalStats, setSignalStats] = useState<any>(null);
  // const [previousSignalsCount, setPreviousSignalsCount] = useState(0);
  
  // Hook pour les notifications
  const { sendTradingSignal } = useAdvancedNotifications();
  
  const [filter, setFilter] = useState<SignalFilter>({
    type: 'ALL',
    confidence: 0,
    timeframe: 'ALL',
    sector: 'ALL',
    strategy: 'ALL'
  });

  const [alertSettings, setAlertSettings] = useState({
    enabled: true,
    minConfidence: 70,
    notifyBuy: true,
    notifySell: true,
    emailNotifications: false,
    pushNotifications: true
  });

  // Mock data generation
  const generateMockSignals = (): Signal[] => {
    const symbols = ['SPY', 'QQQ', 'VTI', 'VEA', 'VWO', 'IWM', 'TLT', 'GLD', 'USO', 'FXI'];
    const names = [
      'SPDR S&P 500 ETF',
      'Invesco QQQ Trust',
      'Vanguard Total Stock Market',
      'Vanguard FTSE Developed Markets',
      'Vanguard Emerging Markets',
      'iShares Russell 2000',
      'iShares 20+ Year Treasury',
      'SPDR Gold Trust',
      'United States Oil Fund',
      'iShares China Large-Cap'
    ];
    
    const strategies = ['RSI Divergence', 'MACD Cross', 'Bollinger Breakout', 'Volume Surge', 'Moving Average', 'Support/Resistance'];
    const sectors = ['Diversifié', 'Technologie', 'International', 'Obligataire', 'Matières Premières'];
    const timeframes: Array<'1H' | '4H' | '1D' | '1W'> = ['1H', '4H', '1D', '1W'];
    const signalTypes: Array<'BUY' | 'SELL' | 'HOLD'> = ['BUY', 'SELL', 'HOLD'];

    return symbols.map((symbol, index) => {
      const currentPrice = 100 + Math.random() * 400;
      const signalType = signalTypes[Math.floor(Math.random() * signalTypes.length)];
      const confidence = 50 + Math.random() * 50;
      
      return {
        id: `signal-${index + 1}`,
        symbol,
        name: names[index],
        signalType,
        confidence: Math.round(confidence),
        currentPrice: Math.round(currentPrice * 100) / 100,
        targetPrice: signalType === 'BUY' 
          ? Math.round((currentPrice * (1 + 0.05 + Math.random() * 0.15)) * 100) / 100
          : Math.round((currentPrice * (1 - 0.05 - Math.random() * 0.15)) * 100) / 100,
        stopLoss: signalType === 'BUY'
          ? Math.round((currentPrice * (1 - 0.03 - Math.random() * 0.07)) * 100) / 100
          : Math.round((currentPrice * (1 + 0.03 + Math.random() * 0.07)) * 100) / 100,
        timeframe: timeframes[Math.floor(Math.random() * timeframes.length)],
        strategy: strategies[Math.floor(Math.random() * strategies.length)],
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(),
        expiresAt: new Date(Date.now() + Math.random() * 86400000 * 30).toISOString(),
        isActive: Math.random() > 0.2,
        volume: Math.floor(Math.random() * 10000000) + 1000000,
        change24h: (Math.random() - 0.5) * 10,
        rsi: Math.round(Math.random() * 100),
        macd: (Math.random() - 0.5) * 10,
        technicalScore: Math.round(40 + Math.random() * 60),
        fundamentalScore: Math.round(40 + Math.random() * 60),
        marketCap: Math.round((Math.random() * 500 + 10) * 1000000000),
        sector: sectors[Math.floor(Math.random() * sectors.length)]
      };
    });
  };

  useEffect(() => {
    loadSignals();
    loadSignalStatistics();
  }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadSignals = async () => {
    try {
      setLoading(true);
      setError('');
      
      let signalsData;
      
      // Load signals based on active tab
      if (activeTab === 'active') {
        // Try to get real signals first
        try {
          signalsData = await signalsAPI.getActiveSignals({
            skip: 0,
            limit: 20,
            ...(filter.type !== 'ALL' && { signal_type: filter.type as any }),
            ...(filter.confidence > 0 && { min_confidence: filter.confidence })
          });
          
          if (signalsData && signalsData.length > 0) {
            // Transform API signals to component format
            const transformedSignals = signalsData.map(transformSignalFromAPI);
            setSignals(transformedSignals);
            return;
          }
        } catch (apiError) {
          console.log('Real signals API not available, trying advanced signals');
          
          // Try advanced signals API
          try {
            const response = await fetch('/api/v1/advanced-signals/signals/advanced', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (response.ok) {
              const advancedData = await response.json();
              if (advancedData.status === 'success' && advancedData.data) {
                const transformedSignals = advancedData.data.map(transformAdvancedSignal);
                
                // Détecter les nouveaux signaux pour les notifications
                const newSignals = transformedSignals.filter((signal: Signal) => 
                  !signals.some(existing => existing.id === signal.id) &&
                  signal.confidence >= alertSettings.minConfidence &&
                  ((signal.signalType === 'BUY' && alertSettings.notifyBuy) ||
                   (signal.signalType === 'SELL' && alertSettings.notifySell))
                );
                
                // Envoyer des notifications pour les nouveaux signaux importants
                if (newSignals.length > 0 && signals.length > 0) { // Éviter les notifications au premier chargement
                  newSignals.forEach((signal: Signal) => {
                    try {
                      sendTradingSignal({
                        etf_symbol: signal.symbol,
                        etf_name: signal.name,
                        signal_type: signal.signalType,
                        confidence: signal.confidence,
                        strategy: signal.strategy,
                        id: signal.id
                      });
                    } catch (error) {
                      console.error('Erreur envoi notification signal:', error);
                    }
                  });
                }
                
                setSignals(transformedSignals);
                return;
              }
            }
          } catch (advancedError) {
            console.log('Advanced signals API not available, using mock data');
          }
        }
      } else if (activeTab === 'history') {
        try {
          signalsData = await signalsAPI.getSignalHistory({
            skip: 0,
            limit: 50,
            ...(filter.type !== 'ALL' && { signal_type: filter.type as any })
          });
          
          if (signalsData && signalsData.length > 0) {
            const transformedSignals = signalsData.map(transformSignalFromAPI);
            setSignals(transformedSignals);
            return;
          }
        } catch (apiError) {
          console.log('Signal history API not available');
        }
      }
      
      // Fallback to mock data
      const mockSignals = generateMockSignals();
      setSignals(mockSignals);
      
    } catch (err: any) {
      console.error('Error loading signals:', err);
      setError('Erreur lors du chargement des signaux: ' + (err.message || 'Erreur inconnue'));
    } finally {
      setLoading(false);
    }
  };

  const loadSignalStatistics = async () => {
    try {
      const response = await fetch('/api/v1/advanced-signals/signals/statistics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setSignalStats(data.statistics);
        }
      }
    } catch (error) {
      console.log('Signal statistics not available');
    }
  };

  const transformSignalFromAPI = (apiSignal: any): Signal => {
    return {
      id: apiSignal.id,
      symbol: apiSignal.etf_isin?.slice(-3) || 'ETF',
      name: apiSignal.etf_isin || 'ETF Fund',
      signalType: apiSignal.signal_type?.toUpperCase() || 'HOLD',
      confidence: apiSignal.confidence || 50,
      currentPrice: apiSignal.current_price || 100,
      targetPrice: apiSignal.target_price || 105,
      stopLoss: apiSignal.stop_loss || 95,
      timeframe: '1D',
      strategy: apiSignal.strategy || 'Technical Analysis',
      createdAt: apiSignal.created_at || new Date().toISOString(),
      expiresAt: apiSignal.expires_at || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      isActive: apiSignal.is_active !== false,
      volume: Math.floor(Math.random() * 10000000) + 1000000,
      change24h: (Math.random() - 0.5) * 10,
      rsi: Math.round(Math.random() * 100),
      macd: (Math.random() - 0.5) * 10,
      technicalScore: apiSignal.technical_score || Math.round(40 + Math.random() * 60),
      fundamentalScore: apiSignal.fundamental_score || Math.round(40 + Math.random() * 60),
      marketCap: Math.round((Math.random() * 500 + 10) * 1000000000),
      sector: apiSignal.sector || 'Diversifié'
    };
  };

  const transformAdvancedSignal = (advSignal: any): Signal => {
    return {
      id: advSignal.id,
      symbol: advSignal.etf_symbol,
      name: advSignal.etf_name,
      signalType: advSignal.signal_type,
      confidence: advSignal.confidence,
      currentPrice: advSignal.current_price,
      targetPrice: advSignal.price_target,
      stopLoss: advSignal.stop_loss,
      timeframe: '1D',
      strategy: advSignal.reasons?.[0] || 'Advanced Analysis',
      createdAt: advSignal.generated_at,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      isActive: true,
      volume: Math.floor(Math.random() * 10000000) + 1000000,
      change24h: advSignal.expected_return || (Math.random() - 0.5) * 10,
      rsi: advSignal.indicators?.rsi || Math.round(Math.random() * 100),
      macd: advSignal.indicators?.macd || (Math.random() - 0.5) * 10,
      technicalScore: advSignal.technical_score,
      fundamentalScore: Math.round(40 + Math.random() * 60),
      marketCap: Math.round((Math.random() * 500 + 10) * 1000000000),
      sector: advSignal.sector || 'Technology'
    };
  };

  const refreshSignals = async () => {
    await loadSignals();
    await loadSignalStatistics();
  };

  const filteredSignals = signals.filter(signal => {
    if (filter.type !== 'ALL' && signal.signalType !== filter.type) return false;
    if (signal.confidence < filter.confidence) return false;
    if (filter.timeframe !== 'ALL' && signal.timeframe !== filter.timeframe) return false;
    if (filter.sector !== 'ALL' && signal.sector !== filter.sector) return false;
    if (filter.strategy !== 'ALL' && signal.strategy !== filter.strategy) return false;
    return activeTab === 'active' ? signal.isActive : true;
  });

  const formatCurrency = (value: number) => {
    return value.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'BUY': return 'text-green-600 bg-green-100';
      case 'SELL': return 'text-red-600 bg-red-100';
      case 'HOLD': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'BUY': return '📈';
      case 'SELL': return '📉';
      case 'HOLD': return '⏸️';
      default: return '❓';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleAlertSettingsChange = (key: string, value: boolean | number) => {
    setAlertSettings(prev => ({ ...prev, [key]: value }));
  };

  if (loading && signals.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des signaux...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-red-800 font-medium">Erreur</h3>
              <p className="text-red-600">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📊 Signaux de Trading</h1>
          <p className="text-gray-600 mt-2">
            Analysez les opportunités d'investissement générées par notre IA
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={refreshSignals}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <span>🔄</span>
            )}
            Actualiser
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Signaux actifs</p>
              <p className="text-2xl font-bold text-gray-900">
                {activeTab === 'active' ? signals.length : signals.filter(s => s.isActive).length}
              </p>
            </div>
            <div className="text-3xl">🎯</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            {activeTab === 'active' ? 'Signaux en cours' : `Sur ${signals.length} signaux totaux`}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Signaux BUY</p>
              <p className="text-2xl font-bold text-green-600">
                {signalStats?.type_distribution?.BUY || signals.filter(s => s.signalType === 'BUY' && (activeTab === 'active' || s.isActive)).length}
              </p>
            </div>
            <div className="text-3xl">📈</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Opportunités d'achat
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Confidence moyenne</p>
              <p className="text-2xl font-bold text-blue-600">
                {signalStats?.average_confidence || (signals.length > 0 ? Math.round(signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length) : 0)}%
              </p>
            </div>
            <div className="text-3xl">🎲</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Fiabilité des signaux
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Signaux haute conf.</p>
              <p className="text-2xl font-bold text-purple-600">
                {signalStats?.confidence_ranges?.high_confidence_90_plus || signals.filter(s => s.confidence >= 80 && (activeTab === 'active' || s.isActive)).length}
              </p>
            </div>
            <div className="text-3xl">⭐</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Confidence ≥ {signalStats ? '90' : '80'}%
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 Filtres</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type de signal</label>
            <select
              value={filter.type}
              onChange={(e) => setFilter(prev => ({ ...prev, type: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ALL">Tous</option>
              <option value="BUY">📈 BUY</option>
              <option value="SELL">📉 SELL</option>
              <option value="HOLD">⏸️ HOLD</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confidence min.</label>
            <select
              value={filter.confidence}
              onChange={(e) => setFilter(prev => ({ ...prev, confidence: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="0">Toutes</option>
              <option value="50">≥ 50%</option>
              <option value="70">≥ 70%</option>
              <option value="80">≥ 80%</option>
              <option value="90">≥ 90%</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
            <select
              value={filter.timeframe}
              onChange={(e) => setFilter(prev => ({ ...prev, timeframe: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ALL">Tous</option>
              <option value="1H">1H</option>
              <option value="4H">4H</option>
              <option value="1D">1D</option>
              <option value="1W">1W</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Secteur</label>
            <select
              value={filter.sector}
              onChange={(e) => setFilter(prev => ({ ...prev, sector: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ALL">Tous</option>
              <option value="Diversifié">Diversifié</option>
              <option value="Technologie">Technologie</option>
              <option value="International">International</option>
              <option value="Obligataire">Obligataire</option>
              <option value="Matières Premières">Matières Premières</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stratégie</label>
            <select
              value={filter.strategy}
              onChange={(e) => setFilter(prev => ({ ...prev, strategy: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ALL">Toutes</option>
              <option value="RSI Divergence">RSI Divergence</option>
              <option value="MACD Cross">MACD Cross</option>
              <option value="Bollinger Breakout">Bollinger Breakout</option>
              <option value="Volume Surge">Volume Surge</option>
              <option value="Moving Average">Moving Average</option>
              <option value="Support/Resistance">Support/Resistance</option>
            </select>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          {filteredSignals.length} signal(s) trouvé(s) avec ces filtres
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('active')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ⚡ Signaux actifs ({signals.filter(s => s.isActive).length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📜 Historique
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analysis'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔬 Analyse
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'alerts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔔 Alertes
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {(activeTab === 'active' || activeTab === 'history') && (
            <div className="space-y-4">
              {filteredSignals.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📭</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun signal trouvé</h3>
                  <p className="text-gray-500">Modifiez vos filtres pour voir plus de signaux</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {filteredSignals.map((signal) => (
                    <div key={signal.id} className="bg-white border rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">{getSignalIcon(signal.signalType)}</div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{signal.symbol}</h3>
                            <p className="text-sm text-gray-600">{signal.name}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignalColor(signal.signalType)}`}>
                            {signal.signalType}
                          </span>
                          <div className={`text-sm font-medium mt-1 ${getConfidenceColor(signal.confidence)}`}>
                            {signal.confidence}% confiance
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <div className="text-sm text-gray-600">Prix actuel</div>
                          <div className="font-medium">{formatCurrency(signal.currentPrice)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Objectif</div>
                          <div className="font-medium text-blue-600">{formatCurrency(signal.targetPrice)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Stop Loss</div>
                          <div className="font-medium text-red-600">{formatCurrency(signal.stopLoss)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Potentiel</div>
                          <div className={`font-medium ${signal.signalType === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercentage(((signal.targetPrice - signal.currentPrice) / signal.currentPrice) * 100)}
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-between items-center text-sm text-gray-600 mb-4">
                        <span>⏱️ {signal.timeframe}</span>
                        <span>📊 {signal.strategy}</span>
                        <span>🏢 {signal.sector}</span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">RSI</div>
                          <div className={signal.rsi > 70 ? 'text-red-600' : signal.rsi < 30 ? 'text-green-600' : 'text-gray-600'}>
                            {signal.rsi}
                          </div>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">MACD</div>
                          <div className={signal.macd > 0 ? 'text-green-600' : 'text-red-600'}>
                            {signal.macd.toFixed(2)}
                          </div>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="font-medium">Volume</div>
                          <div className="text-gray-600">
                            {(signal.volume / 1000000).toFixed(1)}M
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-between items-center">
                        <div className="text-xs text-gray-500">
                          Créé: {new Date(signal.createdAt).toLocaleDateString('fr-FR')}
                        </div>
                        <div className="text-xs text-gray-500">
                          Expire: {new Date(signal.expiresAt).toLocaleDateString('fr-FR')}
                        </div>
                      </div>

                      <div className="mt-4 flex space-x-2">
                        <button className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                          📊 Analyser
                        </button>
                        <button className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                          💼 Ajouter au portfolio
                        </button>
                        <button className="px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">
                          🔔
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">🔬 Analyse des signaux</h3>
              
              {signalStats && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-white border rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{signalStats.total_signals}</div>
                    <div className="text-sm text-gray-600">Signaux générés ({signalStats.period_analyzed})</div>
                  </div>
                  <div className="bg-white border rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">{signalStats.average_confidence}%</div>
                    <div className="text-sm text-gray-600">Confiance moyenne</div>
                  </div>
                  <div className="bg-white border rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">{signalStats.signals_per_day_avg}</div>
                    <div className="text-sm text-gray-600">Signaux par jour</div>
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-medium text-gray-900 mb-4">📊 Performance des stratégies</h4>
                  <div className="space-y-3">
                    {['RSI Divergence', 'MACD Cross', 'Bollinger Breakout', 'Volume Surge'].map(strategy => {
                      const strategySignals = signals.filter(s => s.strategy === strategy);
                      const avgConfidence = strategySignals.length > 0 
                        ? strategySignals.reduce((sum, s) => sum + s.confidence, 0) / strategySignals.length 
                        : 0;
                      
                      return (
                        <div key={strategy} className="flex justify-between items-center">
                          <span className="text-sm text-gray-700">{strategy}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium">{avgConfidence.toFixed(0)}%</span>
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${avgConfidence}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-medium text-gray-900 mb-4">🎯 Répartition par type</h4>
                  <div className="space-y-3">
                    {signalStats ? 
                      Object.entries(signalStats.type_distribution).map(([type, count]: [string, any]) => (
                        <div key={type} className="flex justify-between items-center">
                          <span className="text-sm text-gray-700">{getSignalIcon(type)} {type}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium">{count}</span>
                            <span className="text-xs text-gray-500">({signalStats.type_percentages[type]?.toFixed(0)}%)</span>
                          </div>
                        </div>
                      )) :
                      ['BUY', 'SELL', 'HOLD'].map(type => {
                        const typeSignals = signals.filter(s => s.signalType === type);
                        const percentage = signals.length > 0 ? (typeSignals.length / signals.length) * 100 : 0;
                        
                        return (
                          <div key={type} className="flex justify-between items-center">
                            <span className="text-sm text-gray-700">{getSignalIcon(type)} {type}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium">{typeSignals.length}</span>
                              <span className="text-xs text-gray-500">({percentage.toFixed(0)}%)</span>
                            </div>
                          </div>
                        );
                      })
                    }
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 className="font-medium text-blue-900 mb-3">💡 Insights du marché</h4>
                <div className="space-y-2 text-sm text-blue-800">
                  {signalStats ? (
                    <>
                      <p>• {signalStats.type_distribution.BUY || 0} signaux d'achat détectés, indiquant des opportunités de croissance</p>
                      <p>• {signalStats.confidence_ranges?.high_confidence_90_plus || 0} signaux avec haute confiance (≥90%) à surveiller prioritairement</p>
                      <p>• Score de risque moyen: {signalStats.average_risk_score}% - niveau de volatilité modéré</p>
                      {signalStats.top_etfs_by_signals && (
                        <p>• ETFs les plus actifs: {signalStats.top_etfs_by_signals.slice(0, 3).map((etf: any) => etf.etf_symbol).join(', ')}</p>
                      )}
                    </>
                  ) : (
                    <>
                      <p>• {signals.filter(s => s.signalType === 'BUY').length} signaux d'achat détectés, indiquant des opportunités de croissance</p>
                      <p>• {signals.filter(s => s.confidence >= 80).length} signaux avec haute confiance (≥80%) à surveiller prioritairement</p>
                      <p>• Les ETFs technologiques montrent le plus d'activité avec {signals.filter(s => s.sector === 'Technologie').length} signaux</p>
                      <p>• Volume de trading moyens: {signals.length > 0 ? (signals.reduce((sum, s) => sum + s.volume, 0) / signals.length / 1000000).toFixed(1) : 0}M par ETF</p>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">🔔 Configuration des alertes</h3>
              
              <div className="bg-white border rounded-lg p-6">
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Alertes activées</h4>
                      <p className="text-sm text-gray-600">Recevez des notifications pour les nouveaux signaux</p>
                    </div>
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={alertSettings.enabled}
                        onChange={(e) => handleAlertSettingsChange('enabled', e.target.checked)}
                        className="sr-only"
                      />
                      <div
                        onClick={() => handleAlertSettingsChange('enabled', !alertSettings.enabled)}
                        className={`cursor-pointer w-11 h-6 rounded-full ${
                          alertSettings.enabled ? 'bg-blue-600' : 'bg-gray-200'
                        } relative transition-colors`}
                      >
                        <div
                          className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                            alertSettings.enabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Confiance minimale: {alertSettings.minConfidence}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={alertSettings.minConfidence}
                      onChange={(e) => handleAlertSettingsChange('minConfidence', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>0%</span>
                      <span>50%</span>
                      <span>100%</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h5 className="font-medium text-gray-900">Types de signaux</h5>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={alertSettings.notifyBuy}
                          onChange={(e) => handleAlertSettingsChange('notifyBuy', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-700">📈 Signaux BUY</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={alertSettings.notifySell}
                          onChange={(e) => handleAlertSettingsChange('notifySell', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-700">📉 Signaux SELL</span>
                      </label>
                    </div>

                    <div className="space-y-3">
                      <h5 className="font-medium text-gray-900">Méthodes de notification</h5>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={alertSettings.pushNotifications}
                          onChange={(e) => handleAlertSettingsChange('pushNotifications', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-700">🔔 Notifications push</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={alertSettings.emailNotifications}
                          onChange={(e) => handleAlertSettingsChange('emailNotifications', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-700">📧 Notifications email</span>
                      </label>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                      💾 Sauvegarder les paramètres
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">📈 Statistiques des alertes</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">127</div>
                    <div className="text-sm text-gray-600">Alertes envoyées ce mois</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">89%</div>
                    <div className="text-sm text-gray-600">Taux de précision</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">3.2min</div>
                    <div className="text-sm text-gray-600">Temps de réaction moyen</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Signals;