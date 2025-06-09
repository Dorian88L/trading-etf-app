import React, { useState } from 'react';
import {
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

interface TechnicalIndicatorData {
  timestamp: string;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_20?: number;
  ema_50?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  bb_upper?: number;
  bb_lower?: number;
  bb_middle?: number;
  williams_r?: number;
  stoch_k?: number;
  stoch_d?: number;
  roc?: number;
  adx?: number;
}

interface TechnicalIndicatorsProps {
  data: TechnicalIndicatorData[];
  currentPrice: number;
  etfName: string;
}

interface IndicatorConfig {
  name: string;
  key: keyof TechnicalIndicatorData;
  visible: boolean;
  color: string;
  category: 'trend' | 'momentum' | 'volatility' | 'volume';
  description: string;
  interpretation: (value: number) => { status: 'bullish' | 'bearish' | 'neutral'; message: string };
}

const TechnicalIndicators: React.FC<TechnicalIndicatorsProps> = ({
  data,
  currentPrice,
  etfName
}) => {
  const [activeCategory, setActiveCategory] = useState<'trend' | 'momentum' | 'volatility' | 'volume'>('trend');
  const [showConfig, setShowConfig] = useState(false);

  // Configuration des indicateurs
  const [indicators, setIndicators] = useState<IndicatorConfig[]>([
    {
      name: 'SMA 20',
      key: 'sma_20',
      visible: true,
      color: '#3B82F6',
      category: 'trend',
      description: 'Moyenne mobile simple sur 20 périodes',
      interpretation: (value: number) => {
        if (currentPrice > value * 1.02) return { status: 'bullish', message: 'Prix au-dessus de la SMA20' };
        if (currentPrice < value * 0.98) return { status: 'bearish', message: 'Prix en-dessous de la SMA20' };
        return { status: 'neutral', message: 'Prix proche de la SMA20' };
      }
    },
    {
      name: 'SMA 50',
      key: 'sma_50',
      visible: true,
      color: '#10B981',
      category: 'trend',
      description: 'Moyenne mobile simple sur 50 périodes',
      interpretation: (value: number) => {
        if (currentPrice > value * 1.03) return { status: 'bullish', message: 'Tendance haussière confirmée' };
        if (currentPrice < value * 0.97) return { status: 'bearish', message: 'Tendance baissière confirmée' };
        return { status: 'neutral', message: 'Tendance neutre' };
      }
    },
    {
      name: 'RSI',
      key: 'rsi',
      visible: true,
      color: '#F59E0B',
      category: 'momentum',
      description: 'Relative Strength Index (14 périodes)',
      interpretation: (value: number) => {
        if (value > 70) return { status: 'bearish', message: 'Zone de surachat' };
        if (value < 30) return { status: 'bullish', message: 'Zone de survente' };
        return { status: 'neutral', message: 'Zone neutre' };
      }
    },
    {
      name: 'MACD',
      key: 'macd',
      visible: true,
      color: '#8B5CF6',
      category: 'momentum',
      description: 'Moving Average Convergence Divergence',
      interpretation: (value: number) => {
        const signal = data[data.length - 1]?.macd_signal || 0;
        if (value > signal) return { status: 'bullish', message: 'MACD au-dessus du signal' };
        if (value < signal) return { status: 'bearish', message: 'MACD en-dessous du signal' };
        return { status: 'neutral', message: 'MACD proche du signal' };
      }
    },
    {
      name: 'Williams %R',
      key: 'williams_r',
      visible: true,
      color: '#EF4444',
      category: 'momentum',
      description: 'Williams Percent Range (14 périodes)',
      interpretation: (value: number) => {
        if (value > -20) return { status: 'bearish', message: 'Zone de surachat' };
        if (value < -80) return { status: 'bullish', message: 'Zone de survente' };
        return { status: 'neutral', message: 'Zone neutre' };
      }
    },
    {
      name: 'Stochastique %K',
      key: 'stoch_k',
      visible: true,
      color: '#06B6D4',
      category: 'momentum',
      description: 'Oscillateur Stochastique %K',
      interpretation: (value: number) => {
        if (value > 80) return { status: 'bearish', message: 'Zone de surachat' };
        if (value < 20) return { status: 'bullish', message: 'Zone de survente' };
        return { status: 'neutral', message: 'Zone neutre' };
      }
    },
    {
      name: 'Rate of Change',
      key: 'roc',
      visible: true,
      color: '#F97316',
      category: 'momentum',
      description: 'Taux de variation (10 périodes)',
      interpretation: (value: number) => {
        if (value > 5) return { status: 'bullish', message: 'Momentum positif fort' };
        if (value < -5) return { status: 'bearish', message: 'Momentum négatif fort' };
        return { status: 'neutral', message: 'Momentum modéré' };
      }
    },
    {
      name: 'ADX',
      key: 'adx',
      visible: true,
      color: '#84CC16',
      category: 'trend',
      description: 'Average Directional Index',
      interpretation: (value: number) => {
        if (value > 30) return { status: 'bullish', message: 'Tendance très forte' };
        if (value > 25) return { status: 'neutral', message: 'Tendance forte' };
        if (value < 20) return { status: 'bearish', message: 'Tendance faible' };
        return { status: 'neutral', message: 'Tendance modérée' };
      }
    },
    {
      name: 'Bollinger Sup.',
      key: 'bb_upper',
      visible: true,
      color: '#DC2626',
      category: 'volatility',
      description: 'Bande de Bollinger supérieure',
      interpretation: (value: number) => {
        if (currentPrice > value) return { status: 'bearish', message: 'Prix au-dessus de la bande sup.' };
        return { status: 'neutral', message: 'Prix dans les bandes' };
      }
    },
    {
      name: 'Bollinger Inf.',
      key: 'bb_lower',
      visible: true,
      color: '#16A34A',
      category: 'volatility',
      description: 'Bande de Bollinger inférieure',
      interpretation: (value: number) => {
        if (currentPrice < value) return { status: 'bullish', message: 'Prix en-dessous de la bande inf.' };
        return { status: 'neutral', message: 'Prix dans les bandes' };
      }
    }
  ]);

  const toggleIndicator = (key: keyof TechnicalIndicatorData) => {
    setIndicators(prev => 
      prev.map(ind => 
        ind.key === key ? { ...ind, visible: !ind.visible } : ind
      )
    );
  };

  const getStatusColor = (status: 'bullish' | 'bearish' | 'neutral') => {
    switch (status) {
      case 'bullish': return 'text-green-600 bg-green-50 border-green-200';
      case 'bearish': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: 'bullish' | 'bearish' | 'neutral') => {
    switch (status) {
      case 'bullish': return '📈';
      case 'bearish': return '📉';
      default: return '➖';
    }
  };

  const filteredIndicators = indicators.filter(ind => ind.category === activeCategory);
  const latestData = data[data.length - 1];

  if (!latestData) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8 text-gray-500">
          <ChartBarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p>Aucune donnée d'indicateur disponible</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="h-6 w-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Indicateurs Techniques - {etfName}
          </h3>
        </div>
        
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
        >
          <AdjustmentsHorizontalIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Configuration des indicateurs</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {indicators.map((indicator) => (
              <label key={indicator.key} className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={indicator.visible}
                  onChange={() => toggleIndicator(indicator.key)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: indicator.color }}
                ></span>
                <span className="text-gray-700">{indicator.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex border-b border-gray-200">
        {(['trend', 'momentum', 'volatility', 'volume'] as const).map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`px-4 py-3 text-sm font-medium border-b-2 capitalize ${
              activeCategory === category
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {category === 'trend' && 'Tendance'}
            {category === 'momentum' && 'Momentum'}
            {category === 'volatility' && 'Volatilité'}
            {category === 'volume' && 'Volume'}
            <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full">
              {indicators.filter(i => i.category === category && i.visible).length}
            </span>
          </button>
        ))}
      </div>

      {/* Indicators Grid */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredIndicators
            .filter(indicator => indicator.visible)
            .map((indicator) => {
              const value = latestData[indicator.key] as number;
              
              if (value === undefined || value === null) {
                return (
                  <div key={indicator.key} className="border rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{indicator.name}</h4>
                      <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                    </div>
                    <p className="text-sm text-gray-500">Données non disponibles</p>
                  </div>
                );
              }

              const interpretation = indicator.interpretation(value);
              
              return (
                <div key={indicator.key} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                      <h4 className="font-medium text-gray-900">{indicator.name}</h4>
                    </div>
                    <EyeIcon className="h-4 w-4 text-gray-400" />
                  </div>
                  
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xl font-bold text-gray-900">
                      {typeof value === 'number' ? value.toFixed(2) : 'N/A'}
                    </div>
                    <div className={`text-lg`}>
                      {getStatusIcon(interpretation.status)}
                    </div>
                  </div>
                  
                  <div className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(interpretation.status)}`}>
                    {interpretation.message}
                  </div>
                  
                  <p className="text-xs text-gray-500 mt-2">{indicator.description}</p>
                </div>
              );
            })}
        </div>

        {filteredIndicators.filter(i => i.visible).length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>Aucun indicateur activé pour cette catégorie</p>
            <p className="text-sm">Utilisez la configuration pour activer des indicateurs</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-600">
            Prix actuel: <span className="font-semibold text-gray-900">{currentPrice.toFixed(2)} €</span>
          </div>
          <div className="flex items-center space-x-4 text-gray-500">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Haussier</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>Baissier</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span>Neutre</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TechnicalIndicators;