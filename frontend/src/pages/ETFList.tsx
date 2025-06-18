import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { marketAPI } from '../services/api';
import PriceAlertCreator from '../components/alerts/PriceAlertCreator';
import LoadingState from '../components/LoadingState';
import DataQualityIndicator from '../components/DataQualityIndicator';
import DataSourcesStatus from '../components/DataSourcesStatus';
import { useApiCall } from '../hooks/useApiCall';

interface RealETFData {
  symbol: string;
  isin: string;
  name: string;
  current_price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  currency: string;
  exchange: string;
  sector: string;
  last_update: string;
  source?: string;
  confidence_score?: number;
  is_real_data?: boolean;
  data_quality?: string;
  reliability_icon?: string;
}

const ETFList: React.FC = () => {
  // Utilisation du nouveau hook useApiCall pour la gestion d'erreurs améliorée
  const {
    data: etfs,
    loading,
    error,
    execute: fetchETFs,
    retry
  } = useApiCall(
    async () => {
      try {
        const response = await marketAPI.getRealETFs();
        return response.data || [];
      } catch (err) {
        console.error('Erreur API getRealETFs:', err);
        throw err;
      }
    },
    {
      retryAttempts: 3,
      autoRetry: true,
      onSuccess: (data) => {
        // ETFs loaded successfully
      },
      onError: (error) => {
        // Handle ETF loading error silently in production
      }
    }
  );

  const [searchTerm, setSearchTerm] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'change' | 'volume'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [showPriceAlert, setShowPriceAlert] = useState(false);
  const [selectedETF, setSelectedETF] = useState<RealETFData | null>(null);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [currencyFilter, setCurrencyFilter] = useState('');
  const [exchangeFilter, setExchangeFilter] = useState('');
  const [showDataSourcesStatus, setShowDataSourcesStatus] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [showOnlyRealData, setShowOnlyRealData] = useState(false);

  useEffect(() => {
    fetchETFs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredETFs = useMemo(() => {
    if (!etfs) return [];
    
    return etfs.filter((etf: RealETFData) => {
      const matchesSearch = etf.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           etf.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           etf.isin.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSector = !sectorFilter || etf.sector === sectorFilter;
      const matchesCurrency = !currencyFilter || etf.currency === currencyFilter;
      const matchesExchange = !exchangeFilter || etf.exchange === exchangeFilter;
      const matchesConfidence = (etf.confidence_score || 1.0) >= minConfidence;
      const matchesRealData = !showOnlyRealData || (etf.is_real_data !== false);
      
      return matchesSearch && matchesSector && matchesCurrency && matchesExchange && matchesConfidence && matchesRealData;
    }).sort((a: RealETFData, b: RealETFData) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'price':
          aValue = a.current_price;
          bValue = b.current_price;
          break;
        case 'change':
          aValue = a.change_percent;
          bValue = b.change_percent;
          break;
        case 'volume':
          aValue = a.volume;
          bValue = b.volume;
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
  }, [etfs, searchTerm, sectorFilter, currencyFilter, exchangeFilter, sortBy, sortOrder]);

  const sectors: string[] = useMemo(() => 
    Array.from(new Set((etfs || []).map((etf: RealETFData) => etf.sector))), [etfs]
  );
  const currencies: string[] = useMemo(() => 
    Array.from(new Set((etfs || []).map((etf: RealETFData) => etf.currency))), [etfs]
  );
  const exchanges: string[] = useMemo(() => 
    Array.from(new Set((etfs || []).map((etf: RealETFData) => etf.exchange))), [etfs]
  );

  const handleSort = (field: 'name' | 'price' | 'change' | 'volume') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const toggleFavorite = (symbol: string) => {
    setFavorites(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const openPriceAlert = (etf: RealETFData) => {
    setSelectedETF(etf);
    setShowPriceAlert(true);
  };

  const getSortIcon = (field: string) => {
    if (sortBy !== field) return '↕️';
    return sortOrder === 'asc' ? '⬆️' : '⬇️';
  };

  const formatPrice = (price: number, currency: string) => {
    if (typeof price !== 'number' || isNaN(price)) {
      return 'N/A';
    }
    try {
      return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: currency || 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(price);
    } catch (error) {
      return `${price.toFixed(2)} ${currency || 'EUR'}`;
    }
  };

  const formatPercentage = (percent: number) => {
    if (typeof percent !== 'number' || isNaN(percent)) {
      return 'N/A';
    }
    const formatted = percent.toFixed(2);
    return percent >= 0 ? `+${formatted}%` : `${formatted}%`;
  };

  return (
    <div className="p-4 sm:p-6">
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 space-y-3 sm:space-y-0">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">📈 ETFs Européens</h1>
          <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
            {/* Vue Mode Toggle */}
            <div className="flex rounded-lg border border-gray-300 bg-white w-full sm:w-auto">
              <button
                onClick={() => setViewMode('table')}
                className={`flex-1 sm:flex-none px-3 py-2 text-sm font-medium rounded-l-lg ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Tableau
              </button>
              <button
                onClick={() => setViewMode('cards')}
                className={`flex-1 sm:flex-none px-3 py-2 text-sm font-medium rounded-r-lg ${
                  viewMode === 'cards'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                🎴 Cartes
              </button>
            </div>
            <button
              onClick={() => setShowDataSourcesStatus(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              📊 Sources
            </button>
            <button
              onClick={fetchETFs}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              🔄 Actualiser
            </button>
          </div>
        </div>
        
        {/* Filtres avancés */}
        <div className="bg-white rounded-lg shadow-sm border p-4 space-y-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Recherche principale */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="🔍 Rechercher par nom, symbole ou ISIN..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-400">🔍</span>
                </div>
              </div>
            </div>
            
            {/* Filtres */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 lg:w-auto">
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="">🏢 Tous secteurs</option>
                {sectors.map(sector => (
                  <option key={sector} value={sector}>{sector}</option>
                ))}
              </select>
              
              <select
                value={currencyFilter}
                onChange={(e) => setCurrencyFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="">💱 Toutes devises</option>
                {currencies.map(currency => (
                  <option key={currency} value={currency}>{currency}</option>
                ))}
              </select>
              
              <select
                value={exchangeFilter}
                onChange={(e) => setExchangeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="">🏛️ Toutes bourses</option>
                {exchanges.map(exchange => (
                  <option key={exchange} value={exchange}>{exchange}</option>
                ))}
              </select>
              
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field as 'name' | 'price' | 'change' | 'volume');
                  setSortOrder(order as 'asc' | 'desc');
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="name-asc">📝 Nom (A-Z)</option>
                <option value="name-desc">📝 Nom (Z-A)</option>
                <option value="price-desc">💰 Prix ↑</option>
                <option value="price-asc">💰 Prix ↓</option>
                <option value="change-desc">📈 Variation ↑</option>
                <option value="change-asc">📉 Variation ↓</option>
                <option value="volume-desc">📊 Volume ↑</option>
                <option value="volume-asc">📊 Volume ↓</option>
              </select>
              
              <select
                value={minConfidence.toString()}
                onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="0.0">🎯 Toute qualité</option>
                <option value="0.7">🎯 Bonne qualité (70%+)</option>
                <option value="0.8">🎯 Très bonne (80%+)</option>
                <option value="0.9">🎯 Excellente (90%+)</option>
              </select>
              
              <button
                onClick={() => setShowOnlyRealData(!showOnlyRealData)}
                className={`px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${
                  showOnlyRealData
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {showOnlyRealData ? '🟢 Données réelles' : '⚪ Toutes données'}
              </button>
            </div>
          </div>
          
          {/* Filtres rapides */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => {
                setSearchTerm('');
                setSectorFilter('');
                setCurrencyFilter('');
                setExchangeFilter('');
                setSortBy('name');
                setSortOrder('asc');
                setMinConfidence(0.0);
                setShowOnlyRealData(false);
              }}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200"
            >
              🗑️ Effacer tous les filtres
            </button>
            <span className="text-xs text-gray-500 self-center">
              {filteredETFs.length} ETF{filteredETFs.length > 1 ? 's' : ''} trouvé{filteredETFs.length > 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Contenu principal avec gestion d'erreurs améliorée */}
      <LoadingState
        loading={loading}
        error={error}
        onRetry={retry}
        onErrorDismiss={() => {}} // L'erreur se cache automatiquement lors du retry
        isEmpty={!loading && !error && filteredETFs.length === 0}
        emptyStateComponent={
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun ETF trouvé</h3>
            <p className="text-gray-500">Essayez de modifier vos critères de recherche ou filtres.</p>
          </div>
        }
      >
        {viewMode === 'table' ? (
        /* Vue tableau */
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('name')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>ETF</span>
                      <span>{getSortIcon('name')}</span>
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('price')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Prix</span>
                      <span>{getSortIcon('price')}</span>
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('change')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Variation</span>
                      <span>{getSortIcon('change')}</span>
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('volume')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Volume</span>
                      <span>{getSortIcon('volume')}</span>
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Secteur
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Qualité
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredETFs.map((etf: RealETFData) => (
                  <tr key={etf.symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => toggleFavorite(etf.symbol)}
                          className="text-lg hover:scale-110 transition-transform"
                        >
                          {favorites.includes(etf.symbol) ? '⭐' : '☆'}
                        </button>
                        <div>
                          <Link
                            to={`/etf/${etf.symbol}`}
                            className="text-sm font-medium text-blue-600 hover:text-blue-800"
                          >
                            {etf.name}
                          </Link>
                          <div className="text-sm text-gray-500">{etf.symbol} • {etf.isin}</div>
                          <div className="text-xs text-gray-400">{etf.exchange}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatPrice(etf.current_price, etf.currency)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium flex items-center ${
                        etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        <span className="mr-1">
                          {etf.change_percent >= 0 ? '📈' : '📉'}
                        </span>
                        <div>
                          <div>{formatPrice(etf.change, etf.currency)}</div>
                          <div className="text-xs">({formatPercentage(etf.change_percent)})</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {typeof etf.volume === 'number' ? etf.volume.toLocaleString('fr-FR') : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        {etf.sector}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <DataQualityIndicator
                        source={etf.source || 'unknown'}
                        confidenceScore={etf.confidence_score || 1.0}
                        isRealData={etf.is_real_data !== false}
                        dataQuality={etf.data_quality || 'unknown'}
                        reliabilityIcon={etf.reliability_icon || '⚪'}
                        showDetails={false}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => toggleWatchlist(etf.symbol)}
                          className={`p-2 rounded transition-colors ${
                            watchlist.includes(etf.symbol)
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                          title={watchlist.includes(etf.symbol) ? 'Retirer de la watchlist' : 'Ajouter à la watchlist'}
                        >
                          👁️
                        </button>
                        <button
                          onClick={() => openPriceAlert(etf)}
                          className="p-2 bg-yellow-100 text-yellow-600 rounded hover:bg-yellow-200 transition-colors"
                          title="Créer une alerte de prix"
                        >
                          💰
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Vue cartes */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredETFs.map((etf: RealETFData) => (
            <div key={etf.symbol} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
              <div className="p-4">
                {/* Header de la carte */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleFavorite(etf.symbol)}
                      className="text-lg hover:scale-110 transition-transform"
                    >
                      {favorites.includes(etf.symbol) ? '⭐' : '☆'}
                    </button>
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                      {etf.symbol}
                    </span>
                  </div>
                  <div className={`text-lg ${etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {etf.change_percent >= 0 ? '📈' : '📉'}
                  </div>
                </div>

                {/* Titre */}
                <Link 
                  to={`/etf/${etf.symbol}`}
                  className="block mb-3"
                >
                  <h3 className="font-medium text-gray-900 hover:text-blue-600 line-clamp-2 leading-tight">
                    {etf.name}
                  </h3>
                </Link>

                {/* Prix */}
                <div className="mb-3">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatPrice(etf.current_price, etf.currency)}
                  </div>
                  <div className={`text-sm font-medium ${
                    etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPrice(etf.change, etf.currency)} ({formatPercentage(etf.change_percent)})
                  </div>
                </div>

                {/* Informations */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Volume:</span>
                    <span className="font-medium">{typeof etf.volume === 'number' ? etf.volume.toLocaleString('fr-FR') : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Secteur:</span>
                    <span className="font-medium">{etf.sector}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Bourse:</span>
                    <span className="font-medium">{etf.exchange}</span>
                  </div>
                  <div className="flex justify-between text-sm items-center">
                    <span className="text-gray-600">Qualité:</span>
                    <DataQualityIndicator
                      source={etf.source || 'unknown'}
                      confidenceScore={etf.confidence_score || 1.0}
                      isRealData={etf.is_real_data !== false}
                      dataQuality={etf.data_quality || 'unknown'}
                      reliabilityIcon={etf.reliability_icon || '⚪'}
                      showDetails={false}
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-between pt-3 border-t border-gray-100">
                  <button
                    onClick={() => toggleWatchlist(etf.symbol)}
                    className={`flex-1 px-3 py-2 mr-2 rounded transition-colors text-sm ${
                      watchlist.includes(etf.symbol)
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    👁️ {watchlist.includes(etf.symbol) ? 'Suivi' : 'Suivre'}
                  </button>
                  <button
                    onClick={() => openPriceAlert(etf)}
                    className="flex-1 px-3 py-2 bg-yellow-100 text-yellow-600 rounded hover:bg-yellow-200 transition-colors text-sm"
                  >
                    💰 Alerte
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      </LoadingState>

      {/* Statistiques en bas */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-blue-600">{filteredETFs.length}</div>
          <div className="text-sm text-gray-600">ETFs trouvés</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-green-600">
            {filteredETFs.filter((etf: RealETFData) => etf.change_percent > 0).length}
          </div>
          <div className="text-sm text-gray-600">En hausse</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-red-600">
            {filteredETFs.filter((etf: RealETFData) => etf.change_percent < 0).length}
          </div>
          <div className="text-sm text-gray-600">En baisse</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-yellow-600">{favorites.length}</div>
          <div className="text-sm text-gray-600">Favoris</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(filteredETFs.reduce((sum, etf) => sum + (etf.confidence_score || 1.0), 0) / (filteredETFs.length || 1) * 100)}%
          </div>
          <div className="text-sm text-gray-600">Qualité moy.</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border text-center">
          <div className="text-2xl font-bold text-purple-600">
            {filteredETFs.filter(etf => etf.is_real_data !== false).length}
          </div>
          <div className="text-sm text-gray-600">Données réelles</div>
        </div>
      </div>

      <div className="mt-6 text-xs text-gray-500 text-center">
        <p>Dernière mise à jour: {etfs && etfs.length > 0 ? new Date(etfs[0].last_update).toLocaleString('fr-FR') : 'N/A'}</p>
        <p>Données multi-sources: Yahoo Finance, Alpha Vantage, FMP, EODHD</p>
        <button
          onClick={() => setShowDataSourcesStatus(true)}
          className="text-blue-600 hover:text-blue-800 underline"
        >
          Voir le statut des sources
        </button>
      </div>

      {/* Modal d'alerte de prix */}
      {selectedETF && (
        <PriceAlertCreator
          isOpen={showPriceAlert}
          onClose={() => {
            setShowPriceAlert(false);
            setSelectedETF(null);
          }}
          onAlertCreated={() => {
            setShowPriceAlert(false);
            setSelectedETF(null);
          }}
          etfSymbol={selectedETF.symbol}
          currentPrice={selectedETF.current_price}
        />
      )}

      {/* Modal du statut des sources */}
      <DataSourcesStatus
        isOpen={showDataSourcesStatus}
        onClose={() => setShowDataSourcesStatus(false)}
      />

    </div>
  );
};

export default ETFList;