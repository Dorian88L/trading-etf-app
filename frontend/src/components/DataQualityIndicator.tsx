import React from 'react';

interface DataQualityIndicatorProps {
  source: string;
  confidenceScore: number;
  isRealData: boolean;
  dataQuality: string;
  reliabilityIcon: string;
  className?: string;
  showDetails?: boolean;
}

const DataQualityIndicator: React.FC<DataQualityIndicatorProps> = ({
  source,
  confidenceScore,
  isRealData,
  dataQuality,
  reliabilityIcon,
  className = '',
  showDetails = false
}) => {
  const getSourceDisplayName = (source: string) => {
    const sourceNames: { [key: string]: string } = {
      'yahoo_finance': 'Yahoo Finance',
      'alpha_vantage': 'Alpha Vantage',
      'financial_modeling_prep': 'FMP',
      'eodhd': 'EODHD',
      'finnhub': 'Finnhub',
      'marketstack': 'Marketstack',
      'twelvedata': 'TwelveData',
      'hybrid_calculated': 'Données calculées',
      'cache': 'Cache'
    };
    return sourceNames[source] || source;
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'text-green-600 bg-green-50 border-green-200';
      case 'good': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'fair': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSourceBadgeColor = (source: string) => {
    if (source === 'yahoo_finance') return 'bg-purple-100 text-purple-800';
    if (source === 'alpha_vantage') return 'bg-blue-100 text-blue-800';
    if (source === 'financial_modeling_prep') return 'bg-green-100 text-green-800';
    if (source === 'hybrid_calculated') return 'bg-orange-100 text-orange-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (!showDetails) {
    // Version compacte - juste l'icône et le tooltip
    return (
      <div 
        className={`inline-flex items-center ${className}`}
        title={`Source: ${getSourceDisplayName(source)} | Qualité: ${dataQuality} (${Math.round(confidenceScore * 100)}%)`}
      >
        <span className="text-sm">{reliabilityIcon}</span>
        {!isRealData && (
          <span className="ml-1 text-xs text-orange-500" title="Données calculées">
            ⚡
          </span>
        )}
      </div>
    );
  }

  // Version détaillée
  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      {/* Icône de fiabilité */}
      <span className="text-lg">{reliabilityIcon}</span>
      
      {/* Badge source */}
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSourceBadgeColor(source)}`}>
        {getSourceDisplayName(source)}
      </span>
      
      {/* Badge qualité */}
      <span className={`px-2 py-1 text-xs font-medium rounded border ${getQualityColor(dataQuality)}`}>
        {dataQuality} ({Math.round(confidenceScore * 100)}%)
      </span>
      
      {/* Indicateur données réelles */}
      {isRealData ? (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
          <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
          Temps réel
        </span>
      ) : (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded-full">
          <span className="w-2 h-2 bg-orange-500 rounded-full mr-1"></span>
          Calculé
        </span>
      )}
    </div>
  );
};

export default DataQualityIndicator;