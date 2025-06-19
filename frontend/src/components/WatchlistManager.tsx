import React, { useState, useEffect } from 'react';
import {
  // HeartIcon,
  EyeIcon,
  ChartBarIcon,
  BellIcon,
  PlusIcon,
  XMarkIcon,
  StarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon, EyeIcon as EyeSolidIcon } from '@heroicons/react/24/solid';

interface WatchlistItem {
  id: string;
  symbol: string;
  name: string;
  current_price: number;
  change: number;
  change_percent: number;
  volume: number;
  sector: string;
  currency: string;
  addedAt: string;
  isAlertActive: boolean;
  alertPrice?: number;
  notes?: string;
  tags: string[];
}

interface WatchlistManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

const WatchlistManager: React.FC<WatchlistManagerProps> = ({ isOpen, onClose }) => {
  const [watchlists, setWatchlists] = useState<{[key: string]: WatchlistItem[]}>({
    'favorites': [],
    'monitoring': [],
    'opportunities': []
  });
  
  const [activeWatchlist, setActiveWatchlist] = useState<string>('favorites');
  const [searchTerm, setSearchTerm] = useState('');
  const [availableETFs, setAvailableETFs] = useState<any[]>([]);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [showCreateNew, setShowCreateNew] = useState(false);
  const [selectedETF, setSelectedETF] = useState<WatchlistItem | null>(null); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [showETFDetails, setShowETFDetails] = useState(false); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [loading, setLoading] = useState(false);

  // Charger les ETFs disponibles
  useEffect(() => {
    if (isOpen) {
      fetchAvailableETFs();
      fetchUserWatchlist();
    }
  }, [isOpen]);

  const fetchAvailableETFs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/real-market/real-etfs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAvailableETFs(data.data || []);
      }
    } catch (error) {
      console.error('Erreur chargement ETFs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserWatchlist = async () => {
    try {
      const response = await fetch('/api/v1/real-market/watchlist', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Convertir les données backend en format attendu
        const watchlistData = data.data || [];
        setWatchlists({
          'favorites': watchlistData,
          'monitoring': [],
          'opportunities': []
        });
      }
    } catch (error) {
      console.error('Erreur chargement watchlist:', error);
    }
  };

  const loadWatchlistsFromStorage = () => {
    const stored = localStorage.getItem('trading_watchlists');
    if (stored) {
      try {
        setWatchlists(JSON.parse(stored));
      } catch (error) {
        console.error('Erreur parsing watchlists:', error);
      }
    }
  };

  const saveWatchlistsToStorage = (newWatchlists: typeof watchlists) => {
    localStorage.setItem('trading_watchlists', JSON.stringify(newWatchlists));
    setWatchlists(newWatchlists);
  };

  const addToWatchlist = async (etf: any, watchlistName: string) => {
    try {
      const response = await fetch('/api/v1/real-market/watchlist', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          etf_symbol: etf.symbol
        })
      });

      if (response.ok) {
        // Recharger la watchlist depuis le serveur
        await fetchUserWatchlist();
      } else {
        const error = await response.json();
        console.error('Erreur ajout watchlist:', error.detail);
      }
    } catch (error) {
      console.error('Erreur ajout watchlist:', error);
    }
  };

  const removeFromWatchlist = async (itemId: string, watchlistName: string) => {
    try {
      // Trouver l'ETF par ID dans la watchlist actuelle
      const currentList = watchlists[watchlistName] || [];
      const etfToRemove = currentList.find(item => item.id === itemId);
      
      if (etfToRemove) {
        const response = await fetch(`/api/v1/real-market/watchlist/${etfToRemove.symbol}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          // Recharger la watchlist depuis le serveur
          await fetchUserWatchlist();
        } else {
          const error = await response.json();
          console.error('Erreur suppression watchlist:', error.detail);
        }
      }
    } catch (error) {
      console.error('Erreur suppression watchlist:', error);
    }
  };

  const createNewWatchlist = () => {
    if (newWatchlistName.trim()) {
      const newWatchlists = {
        ...watchlists,
        [newWatchlistName.toLowerCase().replace(/\s+/g, '_')]: []
      };
      
      saveWatchlistsToStorage(newWatchlists);
      setNewWatchlistName('');
      setShowCreateNew(false);
    }
  };

  const deleteWatchlist = (watchlistName: string) => {
    if (['favorites', 'monitoring', 'opportunities'].includes(watchlistName)) {
      return; // Ne pas supprimer les watchlists par défaut
    }
    
    const { [watchlistName]: removed, ...newWatchlists } = watchlists;
    saveWatchlistsToStorage(newWatchlists);
    
    if (activeWatchlist === watchlistName) {
      setActiveWatchlist('favorites');
    }
  };

  const toggleAlert = (itemId: string, watchlistName: string) => {
    const newWatchlists = {
      ...watchlists,
      [watchlistName]: watchlists[watchlistName].map(item =>
        item.id === itemId ? { ...item, isAlertActive: !item.isAlertActive } : item
      )
    };

    saveWatchlistsToStorage(newWatchlists);
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const addTag = (itemId: string, watchlistName: string, tag: string) => {
    const newWatchlists = {
      ...watchlists,
      [watchlistName]: watchlists[watchlistName].map(item =>
        item.id === itemId 
          ? { ...item, tags: [...(item.tags || []), tag] }
          : item
      )
    };

    saveWatchlistsToStorage(newWatchlists);
  };

  const removeTag = (itemId: string, watchlistName: string, tagToRemove: string) => {
    const newWatchlists = {
      ...watchlists,
      [watchlistName]: watchlists[watchlistName].map(item =>
        item.id === itemId 
          ? { ...item, tags: (item.tags || []).filter(tag => tag !== tagToRemove) }
          : item
      )
    };

    saveWatchlistsToStorage(newWatchlists);
  };

  const getWatchlistIcon = (name: string) => {
    switch (name) {
      case 'favorites': return <HeartSolidIcon className="h-5 w-5 text-red-500" />;
      case 'monitoring': return <EyeSolidIcon className="h-5 w-5 text-blue-500" />;
      case 'opportunities': return <StarIcon className="h-5 w-5 text-yellow-500" />;
      default: return <ChartBarIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getWatchlistDisplayName = (name: string) => {
    switch (name) {
      case 'favorites': return 'Favoris';
      case 'monitoring': return 'Surveillance';
      case 'opportunities': return 'Opportunités';
      default: return name.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
  };

  const filteredETFs = availableETFs.filter(etf =>
    etf.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    etf.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentWatchlist = watchlists[activeWatchlist] || [];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl h-[95vh] max-h-screen flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 lg:p-6 border-b">
          <div className="flex items-center space-x-2 lg:space-x-3">
            <EyeIcon className="h-6 w-6 lg:h-8 lg:w-8 text-blue-600" />
            <div>
              <h2 className="text-lg lg:text-2xl font-bold text-gray-900">Gestionnaire de Watchlists</h2>
              <p className="text-xs lg:text-sm text-gray-600 hidden sm:block">Suivez vos ETFs préférés et configurez des alertes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="h-5 w-5 lg:h-6 lg:w-6 text-gray-500" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">
          {/* Sidebar des watchlists */}
          <div className="w-full lg:w-1/4 border-r lg:border-r border-b lg:border-b-0 bg-gray-50 p-3 lg:p-4">
            <div className="flex items-center justify-between mb-3 lg:mb-4">
              <h3 className="font-semibold text-gray-900 text-sm lg:text-base">Mes Watchlists</h3>
              <button
                onClick={() => setShowCreateNew(true)}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <PlusIcon className="h-4 w-4 lg:h-5 lg:w-5 text-gray-600" />
              </button>
            </div>

            {/* Liste des watchlists */}
            <div className="space-y-1 lg:space-y-2 overflow-x-auto lg:overflow-x-visible">
              <div className="flex lg:flex-col space-x-2 lg:space-x-0 lg:space-y-2 min-w-max lg:min-w-0">
                {Object.keys(watchlists).map(name => (
                  <button
                    key={name}
                    onClick={() => setActiveWatchlist(name)}
                    className={`flex items-center justify-between p-2 lg:p-3 rounded-lg text-left transition-colors whitespace-nowrap lg:w-full ${
                      activeWatchlist === name
                        ? 'bg-blue-100 text-blue-900'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center space-x-1 lg:space-x-2">
                      {getWatchlistIcon(name)}
                      <span className="font-medium text-xs lg:text-sm">{getWatchlistDisplayName(name)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                        {watchlists[name].length}
                      </span>
                      {!['favorites', 'monitoring', 'opportunities'].includes(name) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteWatchlist(name);
                          }}
                          className="p-1 hover:bg-red-100 rounded"
                        >
                          <XMarkIcon className="h-3 w-3 lg:h-4 lg:w-4 text-red-500" />
                        </button>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Formulaire nouvelle watchlist */}
            {showCreateNew && (
              <div className="mt-4 p-3 bg-white rounded-lg border">
                <input
                  type="text"
                  placeholder="Nom de la watchlist"
                  value={newWatchlistName}
                  onChange={(e) => setNewWatchlistName(e.target.value)}
                  className="w-full px-3 py-2 border rounded mb-2 text-sm"
                  autoFocus
                />
                <div className="flex space-x-2">
                  <button
                    onClick={createNewWatchlist}
                    className="flex-1 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    Créer
                  </button>
                  <button
                    onClick={() => {
                      setShowCreateNew(false);
                      setNewWatchlistName('');
                    }}
                    className="flex-1 bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300"
                  >
                    Annuler
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Contenu principal */}
          <div className="flex-1 flex flex-col">
            {/* Tab content header */}
            <div className="p-3 lg:p-4 border-b bg-white">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2 lg:space-x-3">
                  {getWatchlistIcon(activeWatchlist)}
                  <h3 className="text-lg lg:text-xl font-semibold text-gray-900">
                    {getWatchlistDisplayName(activeWatchlist)}
                  </h3>
                  <span className="bg-blue-100 text-blue-800 text-xs lg:text-sm px-2 py-1 rounded">
                    {currentWatchlist.length} ETF{currentWatchlist.length > 1 ? 's' : ''}
                  </span>
                </div>
                <button
                  onClick={fetchAvailableETFs}
                  className="flex items-center space-x-1 lg:space-x-2 px-2 lg:px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-xs lg:text-sm transition-colors"
                  disabled={loading}
                >
                  <ArrowPathIcon className={`h-3 w-3 lg:h-4 lg:w-4 ${loading ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">Actualiser</span>
                </button>
              </div>
            </div>

            <div className="flex-1 flex overflow-hidden flex-col lg:flex-row">
              {/* Liste actuelle */}
              <div className="flex-1 p-3 lg:p-4 overflow-y-auto">
                {currentWatchlist.length === 0 ? (
                  <div className="text-center py-8 lg:py-12">
                    <EyeIcon className="h-8 w-8 lg:h-12 lg:w-12 text-gray-400 mx-auto mb-4" />
                    <h4 className="text-base lg:text-lg font-medium text-gray-900 mb-2">Watchlist vide</h4>
                    <p className="text-sm lg:text-base text-gray-500">Ajoutez des ETFs depuis la liste ci-dessous</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 lg:gap-4">
                    {currentWatchlist.map(item => (
                      <div key={item.id} className="bg-gray-50 rounded-lg p-3 lg:p-4 hover:bg-gray-100 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <h4 className="font-semibold text-gray-900 text-sm lg:text-base">{item.symbol}</h4>
                              <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                                {item.sector}
                              </span>
                            </div>
                            <p className="text-xs lg:text-sm text-gray-600 mb-2 line-clamp-1">{item.name}</p>
                            
                            <div className="flex items-center space-x-2 lg:space-x-4 mb-2">
                              <span className="font-semibold text-sm lg:text-lg">
                                {item.current_price.toFixed(2)} {item.currency}
                              </span>
                              <span className={`flex items-center text-xs lg:text-sm font-medium ${
                                item.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {item.change_percent >= 0 ? (
                                  <ArrowTrendingUpIcon className="h-3 w-3 lg:h-4 lg:w-4 mr-1" />
                                ) : (
                                  <ArrowTrendingDownIcon className="h-3 w-3 lg:h-4 lg:w-4 mr-1" />
                                )}
                                {item.change_percent >= 0 ? '+' : ''}{item.change_percent.toFixed(2)}%
                              </span>
                            </div>

                            {/* Tags */}
                            {item.tags && item.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-2">
                                {item.tags.map(tag => (
                                  <span
                                    key={tag}
                                    className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded cursor-pointer hover:bg-blue-200"
                                    onClick={() => removeTag(item.id, activeWatchlist, tag)}
                                  >
                                    {tag} ×
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="flex flex-row lg:flex-col space-x-1 lg:space-x-0 lg:space-y-2 ml-2 lg:ml-4">
                            <button
                              onClick={() => toggleAlert(item.id, activeWatchlist)}
                              className={`p-1.5 lg:p-2 rounded transition-colors ${
                                item.isAlertActive
                                  ? 'bg-orange-100 text-orange-600'
                                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                              }`}
                              title="Activer/Désactiver alerte"
                            >
                              <BellIcon className="h-3 w-3 lg:h-4 lg:w-4" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedETF(item);
                                setShowETFDetails(true);
                              }}
                              className="p-1.5 lg:p-2 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition-colors"
                              title="Voir détails"
                            >
                              <ChartBarIcon className="h-3 w-3 lg:h-4 lg:w-4" />
                            </button>
                            <button
                              onClick={() => removeFromWatchlist(item.id, activeWatchlist)}
                              className="p-1.5 lg:p-2 bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
                              title="Supprimer"
                            >
                              <XMarkIcon className="h-3 w-3 lg:h-4 lg:w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Panel d'ajout ETFs */}
              <div className="w-full lg:w-1/3 border-t lg:border-t-0 lg:border-l bg-gray-50 flex flex-col">
                <div className="p-3 lg:p-4 border-b bg-white">
                  <h4 className="font-semibold text-gray-900 mb-3 text-sm lg:text-base">Ajouter des ETFs</h4>
                  <input
                    type="text"
                    placeholder="🔍 Rechercher ETF..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>

                <div className="flex-1 overflow-y-auto p-3 lg:p-4">
                  {loading ? (
                    <div className="text-center py-6 lg:py-8">
                      <ArrowPathIcon className="h-6 w-6 lg:h-8 lg:w-8 text-gray-400 mx-auto mb-2 animate-spin" />
                      <p className="text-gray-500 text-sm">Chargement...</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredETFs.slice(0, 20).map(etf => {
                        const isInWatchlist = currentWatchlist.some(item => item.symbol === etf.symbol);
                        
                        return (
                          <div
                            key={etf.symbol}
                            className={`p-2 lg:p-3 rounded-lg border transition-colors ${
                              isInWatchlist
                                ? 'bg-green-50 border-green-200'
                                : 'bg-white hover:bg-gray-50 border-gray-200'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2">
                                  <span className="font-medium text-xs lg:text-sm">{etf.symbol}</span>
                                  <span className={`text-xs font-medium ${
                                    etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                                  }`}>
                                    {etf.change_percent >= 0 ? '+' : ''}{etf.change_percent?.toFixed(2)}%
                                  </span>
                                </div>
                                <p className="text-xs text-gray-600 truncate">{etf.name}</p>
                                <p className="text-xs text-gray-500">{etf.current_price?.toFixed(2)} {etf.currency}</p>
                              </div>
                              
                              {!isInWatchlist ? (
                                <button
                                  onClick={() => addToWatchlist(etf, activeWatchlist)}
                                  className="p-1.5 lg:p-2 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition-colors"
                                  title="Ajouter à la watchlist"
                                >
                                  <PlusIcon className="h-3 w-3 lg:h-4 lg:w-4" />
                                </button>
                              ) : (
                                <span className="text-green-600 text-xs font-medium">
                                  ✓ Ajouté
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchlistManager;