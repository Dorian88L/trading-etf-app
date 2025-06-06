import React, { useState, useEffect } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  GlobeEuropeAfricaIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface MarketIndex {
  name: string;
  symbol: string;
  value: number;
  change: number;
  changePercent: number;
  volume?: number;
  region: string;
}

interface SectorPerformance {
  name: string;
  change: number;
  volume: number;
  marketCap: number;
}

interface MarketOverviewProps {
  indices?: MarketIndex[];
  sectors?: SectorPerformance[];
  lastUpdate?: string;
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ 
  indices = [], 
  sectors = [], 
  lastUpdate 
}) => {
  const [activeTab, setActiveTab] = useState<'indices' | 'sectors' | 'sentiment'>('indices');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Données d'exemple si non fournies
  const defaultIndices: MarketIndex[] = [
    { name: 'CAC 40', symbol: 'CAC', value: 7425.30, change: 89.2, changePercent: 1.22, volume: 3200000000, region: 'France' },
    { name: 'EURO STOXX 50', symbol: 'SX5E', value: 4286.15, change: 21.4, changePercent: 0.50, volume: 2100000000, region: 'Europe' },
    { name: 'S&P 500', symbol: 'SPX', value: 4912.84, change: -14.2, changePercent: -0.29, volume: 2800000000, region: 'US' },
    { name: 'NASDAQ', symbol: 'NDX', value: 17234.56, change: 45.8, changePercent: 0.27, volume: 4100000000, region: 'US' },
    { name: 'FTSE 100', symbol: 'UKX', value: 7621.45, change: -12.3, changePercent: -0.16, volume: 1200000000, region: 'UK' },
    { name: 'DAX', symbol: 'DAX', value: 16789.23, change: 156.7, changePercent: 0.94, volume: 3400000000, region: 'Germany' },
  ];

  const defaultSectors: SectorPerformance[] = [
    { name: 'Technologie', change: 1.8, volume: 12000000000, marketCap: 2500000000000 },
    { name: 'Finance', change: 0.9, volume: 8500000000, marketCap: 1800000000000 },
    { name: 'Santé', change: -0.3, volume: 6200000000, marketCap: 1200000000000 },
    { name: 'Énergie', change: 2.4, volume: 9800000000, marketCap: 800000000000 },
    { name: 'Biens de consommation', change: 0.6, volume: 4500000000, marketCap: 950000000000 },
    { name: 'Industriel', change: 1.2, volume: 7100000000, marketCap: 760000000000 },
    { name: 'Immobilier', change: -1.1, volume: 2300000000, marketCap: 520000000000 },
    { name: 'Télécommunications', change: 0.1, volume: 3400000000, marketCap: 430000000000 },
  ];

  const displayIndices = indices.length > 0 ? indices : defaultIndices;
  const displaySectors = sectors.length > 0 ? sectors : defaultSectors;

  const getTrendIcon = (change: number) => {
    if (change > 0) return <ArrowTrendingUpIcon className="h-4 w-4 text-green-600" />;
    if (change < 0) return <ArrowTrendingDownIcon className="h-4 w-4 text-red-600" />;
    return <MinusIcon className="h-4 w-4 text-gray-500" />;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  const getChangeBackgroundColor = (change: number) => {
    if (change > 0.5) return 'bg-green-50 border-green-200';
    if (change < -0.5) return 'bg-red-50 border-red-200';
    return 'bg-gray-50 border-gray-200';
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000000) return `${(volume / 1000000000).toFixed(1)}Md€`;
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(0)}M€`;
    return `${volume.toLocaleString('fr-FR')}€`;
  };

  const formatMarketCap = (cap: number) => {
    if (cap >= 1000000000000) return `${(cap / 1000000000000).toFixed(1)}T€`;
    if (cap >= 1000000000) return `${(cap / 1000000000).toFixed(0)}Md€`;
    return `${cap.toLocaleString('fr-FR')}€`;
  };

  // Calcul du sentiment global
  const globalSentiment = () => {
    const positiveIndices = displayIndices.filter(idx => idx.changePercent > 0).length;
    const totalIndices = displayIndices.length;
    const sentimentRatio = positiveIndices / totalIndices;
    
    if (sentimentRatio >= 0.7) return { label: 'Très Positif', color: 'text-green-600', bg: 'bg-green-100' };
    if (sentimentRatio >= 0.5) return { label: 'Positif', color: 'text-green-500', bg: 'bg-green-50' };
    if (sentimentRatio >= 0.3) return { label: 'Neutre', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (sentimentRatio >= 0.1) return { label: 'Négatif', color: 'text-red-500', bg: 'bg-red-50' };
    return { label: 'Très Négatif', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const sentiment = globalSentiment();

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Simulation de mise à jour des données
        console.log('Mise à jour des données de marché...');
      }, 30000); // Toutes les 30 secondes

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <GlobeEuropeAfricaIcon className="h-6 w-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Vue des Marchés</h3>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Sentiment global */}
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${sentiment.bg} ${sentiment.color}`}>
            {sentiment.label}
          </div>
          
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-2 rounded-lg ${autoRefresh ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}`}
            title={autoRefresh ? 'Arrêter la mise à jour automatique' : 'Activer la mise à jour automatique'}
          >
            <ArrowPathIcon className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('indices')}
          className={`px-4 py-3 text-sm font-medium border-b-2 ${
            activeTab === 'indices'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Indices Majeurs
        </button>
        <button
          onClick={() => setActiveTab('sectors')}
          className={`px-4 py-3 text-sm font-medium border-b-2 ${
            activeTab === 'sectors'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Performance Sectorielle
        </button>
        <button
          onClick={() => setActiveTab('sentiment')}
          className={`px-4 py-3 text-sm font-medium border-b-2 ${
            activeTab === 'sentiment'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Sentiment
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'indices' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayIndices.map((index) => (
              <div
                key={index.symbol}
                className={`border rounded-lg p-4 ${getChangeBackgroundColor(index.changePercent)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-gray-900">{index.name}</h4>
                    <p className="text-xs text-gray-500">{index.region}</p>
                  </div>
                  {getTrendIcon(index.change)}
                </div>
                
                <div className="mb-2">
                  <div className="text-xl font-bold text-gray-900">
                    {index.value.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                  </div>
                  <div className={`text-sm font-medium ${getChangeColor(index.change)}`}>
                    {index.change > 0 ? '+' : ''}{index.change.toFixed(2)} 
                    ({index.changePercent > 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
                  </div>
                </div>
                
                {index.volume && (
                  <div className="text-xs text-gray-600">
                    Volume: {formatVolume(index.volume)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'sectors' && (
          <div className="space-y-3">
            {displaySectors
              .sort((a, b) => b.change - a.change)
              .map((sector) => (
                <div key={sector.name} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-3">
                    {getTrendIcon(sector.change)}
                    <div>
                      <div className="font-medium text-gray-900">{sector.name}</div>
                      <div className="text-sm text-gray-500">
                        Cap.: {formatMarketCap(sector.marketCap)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-lg font-semibold ${getChangeColor(sector.change)}`}>
                      {sector.change > 0 ? '+' : ''}{sector.change.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500">
                      Vol.: {formatVolume(sector.volume)}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}

        {activeTab === 'sentiment' && (
          <div className="space-y-6">
            {/* Gauge de sentiment */}
            <div className="text-center">
              <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full text-2xl font-bold ${sentiment.bg} ${sentiment.color}`}>
                {sentiment.label}
              </div>
              <p className="mt-2 text-sm text-gray-600">Sentiment de marché global</p>
            </div>

            {/* Statistiques de sentiment */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {displayIndices.filter(i => i.changePercent > 0).length}
                </div>
                <div className="text-sm text-gray-600">Indices en hausse</div>
              </div>
              
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {displayIndices.filter(i => i.changePercent < 0).length}
                </div>
                <div className="text-sm text-gray-600">Indices en baisse</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {(displayIndices.reduce((sum, i) => sum + i.changePercent, 0) / displayIndices.length).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Performance moyenne</div>
              </div>
              
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {displaySectors.filter(s => s.change > 0).length}/{displaySectors.length}
                </div>
                <div className="text-sm text-gray-600">Secteurs positifs</div>
              </div>
            </div>

            {/* Top secteurs */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Top secteurs de la session</h4>
              <div className="space-y-2">
                {displaySectors
                  .sort((a, b) => b.change - a.change)
                  .slice(0, 3)
                  .map((sector, index) => (
                    <div key={sector.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center space-x-2">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index === 0 ? 'bg-yellow-500 text-white' :
                          index === 1 ? 'bg-gray-400 text-white' :
                          'bg-yellow-600 text-white'
                        }`}>
                          {index + 1}
                        </div>
                        <span className="font-medium">{sector.name}</span>
                      </div>
                      <span className={`font-semibold ${getChangeColor(sector.change)}`}>
                        {sector.change > 0 ? '+' : ''}{sector.change.toFixed(1)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <ClockIcon className="h-4 w-4" />
            <span>
              Dernière mise à jour: {lastUpdate || new Date().toLocaleTimeString('fr-FR')}
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Marché ouvert</span>
            </div>
            <span>•</span>
            <span>Données temps réel</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;