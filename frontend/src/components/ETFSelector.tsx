import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, MagnifyingGlassIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

interface ETF {
  isin: string;
  symbol: string;
  name: string;
  sector: string;
  region: string;
  currency: string;
  ter: number;
  aum: number;
  exchange: string;
  description: string;
  benchmark: string;
  price?: number;
  change?: number;
  changePercent?: number;
}

interface ETFSelectorProps {
  selectedETFs: string[];
  onSelectionChange: (etfSymbols: string[]) => void;
  maxSelection?: number;
  className?: string;
}

const ETFSelector: React.FC<ETFSelectorProps> = ({
  selectedETFs,
  onSelectionChange,
  maxSelection = 10,
  className = ''
}) => {
  const [etfs, setEtfs] = useState<ETF[]>([]);
  const [filteredETFs, setFilteredETFs] = useState<ETF[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [maxTER, setMaxTER] = useState<number>(1.0);
  const [sortBy, setSortBy] = useState<'name' | 'ter' | 'aum' | 'change'>('aum');
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const [sectors, setSectors] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);

  useEffect(() => {
    fetchETFs();
  }, []);

  useEffect(() => {
    filterAndSortETFs();
  }, [etfs, searchQuery, selectedSectors, selectedRegions, maxTER, sortBy]);

  const fetchETFs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/market/etf-catalog');
      if (response.ok) {
        const data = await response.json();
        setEtfs(data);
        
        // Extraire les secteurs et régions uniques des données réelles
        const uniqueSectors = [...new Set(data.map((etf: any) => etf.sector).filter(Boolean))];
        const uniqueRegions = [...new Set(data.map((etf: any) => etf.region).filter(Boolean))];
        
        setSectors(uniqueSectors);
        setRegions(uniqueRegions);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des ETFs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortETFs = () => {
    let filtered = etfs.filter(etf => {
      const matchesSearch = searchQuery === '' || 
        etf.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        etf.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        etf.sector.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesSector = selectedSectors.length === 0 || selectedSectors.includes(etf.sector);
      const matchesRegion = selectedRegions.length === 0 || selectedRegions.includes(etf.region);
      const matchesTER = etf.ter <= maxTER;

      return matchesSearch && matchesSector && matchesRegion && matchesTER;
    });

    // Tri
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'ter':
          return a.ter - b.ter;
        case 'aum':
          return b.aum - a.aum;
        case 'change':
          return (b.changePercent || 0) - (a.changePercent || 0);
        default:
          return 0;
      }
    });

    setFilteredETFs(filtered);
  };

  const toggleETFSelection = (symbol: string) => {
    const newSelection = selectedETFs.includes(symbol)
      ? selectedETFs.filter(s => s !== symbol)
      : selectedETFs.length < maxSelection
        ? [...selectedETFs, symbol]
        : selectedETFs;
    
    onSelectionChange(newSelection);
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1e9) return `${(amount / 1e9).toFixed(1)}Md€`;
    if (amount >= 1e6) return `${(amount / 1e6).toFixed(0)}M€`;
    return `${amount.toFixed(0)}€`;
  };

  const getSignalColor = (changePercent?: number) => {
    if (!changePercent) return 'text-gray-500';
    return changePercent >= 0 ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Sélection d'ETFs ({selectedETFs.length}/{maxSelection})
          </h3>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <span>Filtres</span>
            <ChevronDownIcon className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Barre de recherche */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un ETF par nom, symbole ou secteur..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Filtres */}
      {showFilters && (
        <div className="p-6 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Secteurs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Secteurs</label>
              <select
                multiple
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                value={selectedSectors}
                onChange={(e) => setSelectedSectors(Array.from(e.target.selectedOptions, option => option.value))}
              >
                {sectors.map(sector => (
                  <option key={sector} value={sector}>{sector}</option>
                ))}
              </select>
            </div>

            {/* Régions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Régions</label>
              <select
                multiple
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                value={selectedRegions}
                onChange={(e) => setSelectedRegions(Array.from(e.target.selectedOptions, option => option.value))}
              >
                {regions.map(region => (
                  <option key={region} value={region}>{region}</option>
                ))}
              </select>
            </div>

            {/* TER Max */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                TER Max: {maxTER.toFixed(2)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={maxTER}
                onChange={(e) => setMaxTER(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Tri */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Trier par</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
              >
                <option value="aum">Taille (AUM)</option>
                <option value="name">Nom</option>
                <option value="ter">Frais (TER)</option>
                <option value="change">Performance</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Liste des ETFs */}
      <div className="max-h-96 overflow-y-auto">
        {filteredETFs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>Aucun ETF trouvé avec ces critères</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredETFs.map((etf) => (
              <div
                key={etf.symbol}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  selectedETFs.includes(etf.symbol) ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                onClick={() => toggleETFSelection(etf.symbol)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      {selectedETFs.includes(etf.symbol) ? (
                        <StarIconSolid className="w-5 h-5 text-yellow-500" />
                      ) : (
                        <StarIcon className="w-5 h-5 text-gray-400" />
                      )}
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-gray-900">{etf.symbol}</h4>
                          <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                            {etf.sector}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{etf.name}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>TER: {etf.ter.toFixed(2)}%</span>
                          <span>AUM: {formatCurrency(etf.aum)}</span>
                          <span>{etf.region}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    {etf.price && (
                      <div className="text-sm font-medium text-gray-900">
                        {etf.price.toFixed(2)} {etf.currency}
                      </div>
                    )}
                    {etf.changePercent !== undefined && (
                      <div className={`text-sm ${getSignalColor(etf.changePercent)}`}>
                        {etf.changePercent >= 0 ? '+' : ''}{etf.changePercent.toFixed(2)}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>{filteredETFs.length} ETFs disponibles</span>
          <span>
            {selectedETFs.length > 0 && (
              <button
                onClick={() => onSelectionChange([])}
                className="text-red-600 hover:text-red-800 font-medium"
              >
                Tout désélectionner
              </button>
            )}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ETFSelector;