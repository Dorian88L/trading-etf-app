import React, { useState } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  StarIcon,
  FireIcon,
  BoltIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

interface AdvancedSignal {
  id: string;
  etf_isin: string;
  etf_name: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD' | 'WAIT';
  algorithm_type: 'BREAKOUT' | 'MEAN_REVERSION' | 'MOMENTUM' | 'STATISTICAL_ARBITRAGE';
  confidence: number;
  technical_score: number;
  fundamental_score: number;
  risk_score: number;
  current_price: number;
  price_target: number;
  stop_loss: number;
  expected_return: number;
  risk_reward_ratio: number;
  holding_period: number;
  justification: string;
  timestamp: string;
  sector: string;
}

interface SignalsPanelProps {
  signals: AdvancedSignal[];
  onSignalClick?: (signal: AdvancedSignal) => void;
  maxSignals?: number;
}

const SignalsPanel: React.FC<SignalsPanelProps> = ({ 
  signals, 
  onSignalClick,
  maxSignals = 10 
}) => {
  const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL');
  const [sortBy, setSortBy] = useState<'confidence' | 'return' | 'risk_reward'>('confidence');
  
  // Filtrer et trier les signaux
  const filteredSignals = signals
    .filter(signal => filter === 'ALL' || signal.signal_type === filter)
    .sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence;
        case 'return':
          return b.expected_return - a.expected_return;
        case 'risk_reward':
          return b.risk_reward_ratio - a.risk_reward_ratio;
        default:
          return 0;
      }
    })
    .slice(0, maxSignals);

  const getSignalIcon = (signalType: string, algorithmType: string) => {
    switch (signalType) {
      case 'BUY':
        return algorithmType === 'BREAKOUT' ? 
          <BoltIcon className="h-5 w-5 text-green-600" /> :
          <ArrowTrendingUpIcon className="h-5 w-5 text-green-600" />;
      case 'SELL':
        return <ArrowTrendingDownIcon className="h-5 w-5 text-red-600" />;
      case 'HOLD':
        return <EyeIcon className="h-5 w-5 text-blue-600" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSignalBadgeClass = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'SELL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'HOLD':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 70) return 'text-yellow-600';
    if (confidence >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const getAlgorithmName = (algorithm: string) => {
    const names = {
      'BREAKOUT': 'Cassure',
      'MEAN_REVERSION': 'Retour moyenne',
      'MOMENTUM': 'Momentum',
      'STATISTICAL_ARBITRAGE': 'Arbitrage stat.'
    };
    return names[algorithm as keyof typeof names] || algorithm;
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffHours > 0) {
      return `il y a ${diffHours}h`;
    } else if (diffMinutes > 0) {
      return `il y a ${diffMinutes}min`;
    } else {
      return 'À l\'instant';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <FireIcon className="h-6 w-6 text-orange-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            Signaux Avancés
          </h3>
          <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
            {filteredSignals.length}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Filtres */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="ALL">Tous</option>
            <option value="BUY">Achat</option>
            <option value="SELL">Vente</option>
            <option value="HOLD">Conservation</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="confidence">Confiance</option>
            <option value="return">Rendement</option>
            <option value="risk_reward">Risk/Reward</option>
          </select>
        </div>
      </div>

      {/* Liste des signaux */}
      <div className="space-y-4">
        {filteredSignals.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>Aucun signal disponible</p>
            <p className="text-sm">Les signaux apparaîtront ici automatiquement</p>
          </div>
        ) : (
          filteredSignals.map((signal) => (
            <div
              key={signal.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onSignalClick?.(signal)}
            >
              {/* En-tête du signal */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {getSignalIcon(signal.signal_type, signal.algorithm_type)}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{signal.etf_name}</h4>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSignalBadgeClass(signal.signal_type)}`}>
                        {signal.signal_type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">{signal.etf_isin} • {signal.sector}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`text-lg font-bold ${getConfidenceColor(signal.confidence)}`}>
                    {signal.confidence.toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatTimeAgo(signal.timestamp)}
                  </div>
                </div>
              </div>

              {/* Métriques principales */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                <div className="text-center">
                  <div className="text-xs text-gray-500">Prix actuel</div>
                  <div className="font-semibold text-gray-900">
                    {signal.current_price.toFixed(2)} €
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Objectif</div>
                  <div className="font-semibold text-gray-900">
                    {signal.price_target.toFixed(2)} €
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Rendement</div>
                  <div className={`font-semibold ${
                    signal.expected_return > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {signal.expected_return > 0 ? '+' : ''}{signal.expected_return.toFixed(1)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Risk/Reward</div>
                  <div className="font-semibold text-gray-900">
                    1:{signal.risk_reward_ratio.toFixed(1)}
                  </div>
                </div>
              </div>

              {/* Barres de score */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Technique</span>
                    <span className="font-medium">{signal.technical_score.toFixed(0)}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full" 
                      style={{ width: `${signal.technical_score}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Fondamental</span>
                    <span className="font-medium">{signal.fundamental_score.toFixed(0)}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${signal.fundamental_score}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Risque</span>
                    <span className="font-medium">{signal.risk_score.toFixed(0)}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-500 h-2 rounded-full" 
                      style={{ width: `${signal.risk_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Algorithme et période */}
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4">
                  <span className="text-gray-500">
                    Algorithme: <span className="font-medium text-gray-700">{getAlgorithmName(signal.algorithm_type)}</span>
                  </span>
                  <span className="text-gray-500">
                    Période: <span className="font-medium text-gray-700">{signal.holding_period} jours</span>
                  </span>
                </div>
                
                {signal.confidence >= 80 && (
                  <div className="flex items-center space-x-1">
                    <StarIcon className="h-4 w-4 text-yellow-500" />
                    <span className="text-xs font-medium text-yellow-600">Signal Fort</span>
                  </div>
                )}
              </div>

              {/* Justification */}
              <div className="mt-2 text-xs text-gray-600 bg-gray-50 rounded p-2">
                {signal.justification}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pied de page */}
      {filteredSignals.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              Dernière mise à jour: {new Date().toLocaleTimeString('fr-FR')}
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Signaux actifs</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span>En surveillance</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SignalsPanel;