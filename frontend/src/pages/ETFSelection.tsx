import React, { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import ETFSelector from '../components/ETFSelector';
import { PlusIcon, TrashIcon, EyeIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface UserWatchlist {
  id: string;
  name: string;
  etfSymbols: string[];
  createdAt: string;
  isDefault: boolean;
}

interface ETFData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sector: string;
  signal?: 'BUY' | 'SELL' | 'HOLD' | 'WAIT';
  confidence?: number;
}

const ETFSelection: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  
  const [watchlists, setWatchlists] = useState<UserWatchlist[]>([]);
  const [selectedWatchlist, setSelectedWatchlist] = useState<string | null>(null);
  const [etfData, setETFData] = useState<{ [key: string]: ETFData }>({});
  const [showETFSelector, setShowETFSelector] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadUserWatchlists();
    }
  }, [user]);

  useEffect(() => {
    if (selectedWatchlist) {
      const watchlist = watchlists.find(w => w.id === selectedWatchlist);
      if (watchlist && watchlist.etfSymbols.length > 0) {
        loadETFData(watchlist.etfSymbols);
      }
    }
  }, [selectedWatchlist, watchlists]);

  const loadUserWatchlists = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/user/watchlists', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWatchlists(data);
        
        // Sélectionner la première watchlist ou créer une par défaut
        if (data.length > 0) {
          setSelectedWatchlist(data[0].id);
        } else {
          createDefaultWatchlist();
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des watchlists:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadETFData = async (symbols: string[]) => {
    try {
      const responses = await Promise.all(
        symbols.map(symbol => 
          fetch(`/api/v1/market/etf/${symbol}`)
            .then(res => res.ok ? res.json() : null)
        )
      );

      const newETFData: { [key: string]: ETFData } = {};
      responses.forEach((data, index) => {
        if (data) {
          newETFData[symbols[index]] = {
            symbol: data.symbol,
            name: data.name,
            price: data.price,
            change: data.change,
            changePercent: data.change_percent,
            sector: data.sector,
            signal: data.signal?.signal_type,
            confidence: data.signal?.confidence
          };
        }
      });

      setETFData(newETFData);
    } catch (error) {
      console.error('Erreur lors du chargement des données ETF:', error);
    }
  };

  const createDefaultWatchlist = async () => {
    const defaultWatchlist: UserWatchlist = {
      id: 'default',
      name: 'Ma Watchlist',
      etfSymbols: ['IWDA.AS', 'CSPX.AS', 'VWCE.DE'],
      createdAt: new Date().toISOString(),
      isDefault: true
    };

    try {
      const response = await fetch('/api/v1/user/watchlists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(defaultWatchlist)
      });

      if (response.ok) {
        const savedWatchlist = await response.json();
        setWatchlists([savedWatchlist]);
        setSelectedWatchlist(savedWatchlist.id);
      }
    } catch (error) {
      console.error('Erreur lors de la création de la watchlist par défaut:', error);
    }
  };

  const createNewWatchlist = async () => {
    if (!newWatchlistName.trim()) return;

    const newWatchlist: Omit<UserWatchlist, 'id'> = {
      name: newWatchlistName,
      etfSymbols: [],
      createdAt: new Date().toISOString(),
      isDefault: false
    };

    try {
      const response = await fetch('/api/v1/user/watchlists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newWatchlist)
      });

      if (response.ok) {
        const savedWatchlist = await response.json();
        setWatchlists([...watchlists, savedWatchlist]);
        setSelectedWatchlist(savedWatchlist.id);
        setNewWatchlistName('');
      }
    } catch (error) {
      console.error('Erreur lors de la création de la watchlist:', error);
    }
  };

  const updateWatchlistETFs = async (etfSymbols: string[]) => {
    if (!selectedWatchlist) return;

    try {
      const response = await fetch(`/api/v1/user/watchlists/${selectedWatchlist}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ etfSymbols })
      });

      if (response.ok) {
        setWatchlists(watchlists.map(w => 
          w.id === selectedWatchlist 
            ? { ...w, etfSymbols } 
            : w
        ));
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour de la watchlist:', error);
    }
  };

  const deleteWatchlist = async (watchlistId: string) => {
    try {
      const response = await fetch(`/api/v1/user/watchlists/${watchlistId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const newWatchlists = watchlists.filter(w => w.id !== watchlistId);
        setWatchlists(newWatchlists);
        
        if (selectedWatchlist === watchlistId) {
          setSelectedWatchlist(newWatchlists.length > 0 ? newWatchlists[0].id : null);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la suppression de la watchlist:', error);
    }
  };

  const getSignalBadge = (signal?: string, confidence?: number) => {
    if (!signal) return null;

    const colors = {
      BUY: 'bg-green-100 text-green-800',
      SELL: 'bg-red-100 text-red-800',
      HOLD: 'bg-yellow-100 text-yellow-800',
      WAIT: 'bg-gray-100 text-gray-800'
    };

    return (
      <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${colors[signal as keyof typeof colors]}`}>
        <span>{signal}</span>
        {confidence && <span>({confidence.toFixed(0)}%)</span>}
      </div>
    );
  };

  const currentWatchlist = watchlists.find(w => w.id === selectedWatchlist);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Mes ETFs</h1>
          <button
            onClick={() => setShowETFSelector(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Ajouter des ETFs
          </button>
        </div>

        {/* Gestion des watchlists */}
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <select
              value={selectedWatchlist || ''}
              onChange={(e) => setSelectedWatchlist(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Sélectionner une watchlist</option>
              {watchlists.map(watchlist => (
                <option key={watchlist.id} value={watchlist.id}>
                  {watchlist.name} ({watchlist.etfSymbols.length} ETFs)
                </option>
              ))}
            </select>

            {selectedWatchlist && !watchlists.find(w => w.id === selectedWatchlist)?.isDefault && (
              <button
                onClick={() => deleteWatchlist(selectedWatchlist)}
                className="p-2 text-red-600 hover:text-red-800"
                title="Supprimer la watchlist"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Nom de la nouvelle watchlist"
              value={newWatchlistName}
              onChange={(e) => setNewWatchlistName(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && createNewWatchlist()}
            />
            <button
              onClick={createNewWatchlist}
              disabled={!newWatchlistName.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-md"
            >
              Créer
            </button>
          </div>
        </div>
      </div>

      {/* Liste des ETFs de la watchlist sélectionnée */}
      {currentWatchlist && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              {currentWatchlist.name} ({currentWatchlist.etfSymbols.length} ETFs)
            </h2>
          </div>

          {currentWatchlist.etfSymbols.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <ChartBarIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="mb-4">Aucun ETF dans cette watchlist</p>
              <button
                onClick={() => setShowETFSelector(true)}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Ajouter des ETFs
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ETF
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Prix
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Variation
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Signal
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {currentWatchlist.etfSymbols.map((symbol) => {
                    const data = etfData[symbol];
                    return (
                      <tr key={symbol} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{symbol}</div>
                            <div className="text-sm text-gray-500">{data?.name || 'Chargement...'}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {data?.price ? `${data.price.toFixed(2)} €` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {data?.changePercent !== undefined ? (
                            <span className={data.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}>
                              {data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%
                            </span>
                          ) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getSignalBadge(data?.signal, data?.confidence)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => window.open(`/etf/${symbol}`, '_blank')}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Modal de sélection d'ETFs */}
      {showETFSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Sélectionner des ETFs</h3>
              <button
                onClick={() => setShowETFSelector(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="max-h-[70vh] overflow-y-auto">
              <ETFSelector
                selectedETFs={currentWatchlist?.etfSymbols || []}
                onSelectionChange={(symbols) => {
                  updateWatchlistETFs(symbols);
                }}
                maxSelection={20}
              />
            </div>

            <div className="p-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowETFSelector(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ETFSelection;