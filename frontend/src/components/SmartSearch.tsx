import React, { useState, useEffect, useRef } from 'react';
import {
  MagnifyingGlassIcon,
  SparklesIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  TagIcon,
  ClockIcon,
  XMarkIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import { getApiUrl, API_CONFIG } from '../config/api';
// import { Link } from 'react-router-dom'; // eslint-disable-line @typescript-eslint/no-unused-vars

interface SearchResult {
  type: 'etf' | 'signal' | 'portfolio' | 'suggestion';
  id: string;
  title: string;
  subtitle: string;
  data: any;
  relevance: number;
  category: string;
  icon: React.ComponentType<any>;
}

interface SmartSearchProps {
  onClose?: () => void;
  className?: string;
}

const SmartSearch: React.FC<SmartSearchProps> = ({ onClose, className = '' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [suggestedSearches] = useState([
    'ETF technologie',
    'S&P 500',
    'Signaux haussiers',
    'Emerging Markets',
    'High dividend yield',
    'Gold ETF',
    'European equities',
    'Clean energy'
  ]);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }

    // Charger les recherches récentes
    const stored = localStorage.getItem('recent_searches');
    if (stored) {
      setRecentSearches(JSON.parse(stored));
    }
  }, []);

  useEffect(() => {
    if (searchTerm.trim().length > 2) {
      performSearch(searchTerm);
    } else {
      setResults([]);
      setActiveIndex(-1);
    }
  }, [searchTerm]); // eslint-disable-line react-hooks/exhaustive-deps

  const performSearch = async (query: string) => {
    setLoading(true);
    
    try {
      // Recherche multi-sources
      const [etfResults, signalResults] = await Promise.allSettled([
        searchETFs(query),
        searchSignals(query)
      ]);

      const allResults: SearchResult[] = [];

      // Traiter les résultats ETF
      if (etfResults.status === 'fulfilled') {
        allResults.push(...etfResults.value);
      }

      // Traiter les résultats de signaux
      if (signalResults.status === 'fulfilled') {
        allResults.push(...signalResults.value);
      }

      // Ajouter des suggestions intelligentes
      const suggestions = generateSmartSuggestions(query);
      allResults.push(...suggestions);

      // Trier par pertinence
      allResults.sort((a, b) => b.relevance - a.relevance);

      setResults(allResults.slice(0, 10));
    } catch (error) {
      console.error('Erreur de recherche:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchETFs = async (query: string): Promise<SearchResult[]> => {
    try {
      const response = await fetch(getApiUrl('/api/v1/real-market/real-etfs'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const etfs = data.data || [];

        return etfs
          .filter((etf: any) => 
            etf.name.toLowerCase().includes(query.toLowerCase()) ||
            etf.symbol.toLowerCase().includes(query.toLowerCase()) ||
            etf.sector?.toLowerCase().includes(query.toLowerCase())
          )
          .map((etf: any) => ({
            type: 'etf' as const,
            id: etf.symbol,
            title: etf.name,
            subtitle: `${etf.symbol} • ${etf.sector} • ${etf.current_price?.toFixed(2)} ${etf.currency}`,
            data: etf,
            relevance: calculateETFRelevance(etf, query),
            category: 'ETF',
            icon: ChartBarIcon
          }))
          .slice(0, 5);
      }
    } catch (error) {
      console.error('Erreur recherche ETFs:', error);
    }

    return [];
  };

  const searchSignals = async (query: string): Promise<SearchResult[]> => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.ADVANCED_SIGNALS), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const signals = data.data || [];

        return signals
          .filter((signal: any) => 
            signal.etf_symbol?.toLowerCase().includes(query.toLowerCase()) ||
            signal.etf_name?.toLowerCase().includes(query.toLowerCase()) ||
            signal.signal_type?.toLowerCase().includes(query.toLowerCase())
          )
          .map((signal: any) => ({
            type: 'signal' as const,
            id: signal.id,
            title: `Signal ${signal.signal_type} - ${signal.etf_symbol}`,
            subtitle: `${signal.etf_name} • Confiance: ${signal.confidence}% • ${signal.strategy}`,
            data: signal,
            relevance: calculateSignalRelevance(signal, query),
            category: 'Signal',
            icon: signal.signal_type === 'BUY' ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
          }))
          .slice(0, 3);
      }
    } catch (error) {
      console.error('Erreur recherche signaux:', error);
    }

    return [];
  };

  const generateSmartSuggestions = (query: string): SearchResult[] => {
    const suggestions: SearchResult[] = [];
    
    // Suggestions basées sur le contenu
    if (query.toLowerCase().includes('tech')) {
      suggestions.push({
        type: 'suggestion',
        id: 'tech_suggestion',
        title: 'ETFs Technologie les plus performants',
        subtitle: 'Découvrez les meilleurs ETFs du secteur technologique',
        data: { filter: { sector: 'Technology' } },
        relevance: 70,
        category: 'Suggestion',
        icon: SparklesIcon
      });
    }

    if (query.toLowerCase().includes('signal') || query.toLowerCase().includes('buy') || query.toLowerCase().includes('sell')) {
      suggestions.push({
        type: 'suggestion',
        id: 'signals_suggestion',
        title: 'Derniers signaux de trading',
        subtitle: 'Voir tous les signaux récents avec haute confiance',
        data: { page: '/signals' },
        relevance: 80,
        category: 'Navigation',
        icon: FireIcon
      });
    }

    if (query.toLowerCase().includes('portfolio')) {
      suggestions.push({
        type: 'suggestion',
        id: 'portfolio_suggestion',
        title: 'Analyser mon portfolio',
        subtitle: 'Outils d\'analyse et optimisation de portfolio',
        data: { page: '/portfolio' },
        relevance: 75,
        category: 'Navigation',
        icon: CurrencyDollarIcon
      });
    }

    return suggestions;
  };

  const calculateETFRelevance = (etf: any, query: string): number => {
    let score = 0;
    const queryLower = query.toLowerCase();
    
    // Score basé sur la correspondance
    if (etf.symbol.toLowerCase().includes(queryLower)) score += 100;
    if (etf.name.toLowerCase().includes(queryLower)) score += 80;
    if (etf.sector?.toLowerCase().includes(queryLower)) score += 60;
    
    // Bonus pour la performance
    if (etf.change_percent > 0) score += 10;
    if (etf.change_percent > 5) score += 20;
    
    // Bonus pour le volume
    if (etf.volume > 1000000) score += 15;
    
    return score;
  };

  const calculateSignalRelevance = (signal: any, query: string): number => {
    let score = 0;
    const queryLower = query.toLowerCase();
    
    // Score basé sur la correspondance
    if (signal.etf_symbol?.toLowerCase().includes(queryLower)) score += 100;
    if (signal.etf_name?.toLowerCase().includes(queryLower)) score += 80;
    if (signal.signal_type?.toLowerCase().includes(queryLower)) score += 90;
    
    // Bonus pour la confiance
    score += signal.confidence || 0;
    
    // Bonus pour les signaux récents
    const signalDate = new Date(signal.generated_at);
    const daysDiff = (Date.now() - signalDate.getTime()) / (1000 * 60 * 60 * 24);
    if (daysDiff < 1) score += 30;
    else if (daysDiff < 7) score += 15;
    
    return score;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => prev > 0 ? prev - 1 : prev);
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0) {
          handleResultClick(results[activeIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose?.();
        break;
    }
  };

  const handleResultClick = (result: SearchResult) => {
    // Sauvegarder la recherche
    saveRecentSearch(searchTerm);
    
    switch (result.type) {
      case 'etf':
        window.location.href = `/etf/${result.data.symbol}`;
        break;
      case 'signal':
        window.location.href = `/signals`;
        break;
      case 'suggestion':
        if (result.data.page) {
          window.location.href = result.data.page;
        } else if (result.data.filter) {
          window.location.href = `/etfs?filter=${encodeURIComponent(JSON.stringify(result.data.filter))}`;
        }
        break;
    }
    
    onClose?.();
  };

  const saveRecentSearch = (query: string) => {
    const trimmed = query.trim();
    if (trimmed.length < 2) return;
    
    const updated = [trimmed, ...recentSearches.filter(s => s !== trimmed)].slice(0, 10);
    setRecentSearches(updated);
    localStorage.setItem('recent_searches', JSON.stringify(updated));
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recent_searches');
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchTerm(suggestion);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Zone de recherche */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="🔍 Recherche intelligente: ETFs, signaux, secteurs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full pl-12 pr-12 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
        />
        {searchTerm && (
          <button
            onClick={() => {
              setSearchTerm('');
              setResults([]);
              setActiveIndex(-1);
            }}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded-full"
          >
            <XMarkIcon className="h-5 w-5 text-gray-400" />
          </button>
        )}
      </div>

      {/* Résultats */}
      {(searchTerm.length > 0 || recentSearches.length > 0) && (
        <div 
          ref={resultsRef}
          className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl z-50 max-h-96 overflow-y-auto"
        >
          {loading && (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-gray-600">Recherche en cours...</p>
            </div>
          )}

          {!loading && searchTerm.length > 2 && results.length === 0 && (
            <div className="p-6 text-center">
              <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 font-medium">Aucun résultat trouvé</p>
              <p className="text-gray-500 text-sm">Essayez des termes plus généraux</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="py-2">
              <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Résultats de recherche
              </div>
              {results.map((result, index) => (
                <div
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className={`px-4 py-3 cursor-pointer transition-colors ${
                    index === activeIndex ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <result.icon className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {result.title}
                        </p>
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          {result.category}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 truncate">
                        {result.subtitle}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <ChartBarIcon className="h-4 w-4 text-gray-300" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Recherches récentes */}
          {searchTerm.length === 0 && recentSearches.length > 0 && (
            <div className="py-2">
              <div className="flex items-center justify-between px-4 py-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Recherches récentes
                </span>
                <button
                  onClick={clearRecentSearches}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Effacer
                </button>
              </div>
              {recentSearches.map((search, index) => (
                <div
                  key={index}
                  onClick={() => setSearchTerm(search)}
                  className="px-4 py-2 cursor-pointer hover:bg-gray-50 flex items-center space-x-3"
                >
                  <ClockIcon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{search}</span>
                </div>
              ))}
            </div>
          )}

          {/* Suggestions */}
          {searchTerm.length === 0 && (
            <div className="py-2 border-t border-gray-100">
              <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Suggestions populaires
              </div>
              {suggestedSearches.slice(0, 6).map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-4 py-2 cursor-pointer hover:bg-gray-50 flex items-center space-x-3"
                >
                  <TagIcon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{suggestion}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SmartSearch;