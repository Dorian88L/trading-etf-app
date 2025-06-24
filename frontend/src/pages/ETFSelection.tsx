import React, { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import ETFSelector from '../components/ETFSelector';
import { PlusIcon, TrashIcon, EyeIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { getApiUrl } from '../config/api';

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

interface ETFDetails {
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
  inception_date: string;
  dividend_frequency: string;
  replication_method: string;
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
  const [userWatchlistData, setUserWatchlistData] = useState<any[]>([]);
  const [availableETFs, setAvailableETFs] = useState<any[]>([]);
  const [etfDetails, setEtfDetails] = useState<{ [isin: string]: ETFDetails }>({});
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUserWatchlist();
      fetchAvailableETFs();
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

  const fetchUserWatchlist = async () => {
    try {
      setLoading(true);
      console.log('🔄 Chargement watchlist...');
      console.log('Token:', localStorage.getItem('access_token') ? 'Présent' : 'Absent');
      
      const response = await fetch(getApiUrl('/api/v1/watchlist/watchlist'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📡 Réponse API:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📊 Données reçues:', data);
        console.log('📋 Watchlist data:', data.data);
        console.log('📈 Nombre d\'ETFs:', data.data?.length || 0);
        
        setUserWatchlistData(data.data || []);
        
        // Récupérer les détails des ETFs
        if (data.data && data.data.length > 0) {
          await fetchETFDetails(data.data);
        }
        
        // Convertir en format ancien pour compatibilité
        const watchlistCompat = [{
          id: 'main',
          name: 'Ma Watchlist',
          etfSymbols: (data.data || []).map((item: any) => item.symbol),
          createdAt: new Date().toISOString(),
          isDefault: true
        }];
        setWatchlists(watchlistCompat);
        setSelectedWatchlist('main');
      } else {
        const errorData = await response.text();
        console.error('❌ Erreur API:', response.status, errorData);
        setUserWatchlistData([]);
      }
    } catch (error) {
      console.error('❌ Erreur chargement watchlist:', error);
      setUserWatchlistData([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchETFDetails = async (watchlistData: any[]) => {
    console.log('🔍 Récupération détails ETFs...');
    const details: { [isin: string]: ETFDetails } = {};
    
    for (const etf of watchlistData) {
      try {
        // Essayer avec l'ISIN depuis les données watchlist
        const isin = etf.isin || etf.etf_isin;
        if (!isin) {
          console.warn('⚠️ Pas d\'ISIN pour:', etf);
          continue;
        }
        
        console.log(`🔎 Récupération détails pour ISIN: ${isin}`);
        const response = await fetch(getApiUrl(`/api/v1/real-market/etf-details/${isin}`), {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          details[isin] = data.data;
          console.log(`✅ Détails récupérés pour ${isin}:`, data.data.name);
        } else {
          console.error(`❌ Erreur détails ${isin}:`, response.status);
        }
      } catch (error) {
        console.error('❌ Erreur récupération détails ETF:', error);
      }
    }
    
    console.log('📋 Détails ETFs récupérés:', Object.keys(details).length);
    setEtfDetails(details);
  };

  const fetchAvailableETFs = async () => {
    try {
      const response = await fetch(getApiUrl('/api/v1/real-market/real-etfs'), {
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
    }
  };

  const loadETFData = async (symbols: string[]) => {
    try {
      // Utiliser les données déjà chargées de la watchlist
      const newETFData: { [key: string]: ETFData } = {};
      
      userWatchlistData.forEach((etf) => {
        if (symbols.includes(etf.symbol)) {
          newETFData[etf.symbol] = {
            symbol: etf.symbol,
            name: etf.name,
            price: etf.current_price,
            change: etf.change,
            changePercent: etf.change_percent,
            sector: etf.sector,
            signal: 'HOLD', // Valeur par défaut
            confidence: 75 // Valeur par défaut
          };
        }
      });

      setETFData(newETFData);
    } catch (error) {
      console.error('Erreur lors du chargement des données ETF:', error);
    }
  };

  const addETFToWatchlist = async (etfSymbol: string) => {
    try {
      const response = await fetch(getApiUrl('/api/v1/watchlist/watchlist'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          etf_symbol: etfSymbol
        })
      });

      if (response.ok) {
        // Recharger la watchlist
        await fetchUserWatchlist();
      } else {
        const error = await response.json();
        console.error('Erreur ajout watchlist:', error.detail);
      }
    } catch (error) {
      console.error('Erreur ajout watchlist:', error);
    }
  };

  const removeETFFromWatchlist = async (etfSymbol: string) => {
    try {
      const response = await fetch(getApiUrl(`/api/v1/watchlist/watchlist/${etfSymbol}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Recharger la watchlist
        await fetchUserWatchlist();
      } else {
        const error = await response.json();
        console.error('Erreur suppression watchlist:', error.detail);
      }
    } catch (error) {
      console.error('Erreur suppression watchlist:', error);
    }
  };

  const addTestETFs = async () => {
    const testETFs = [
      'EQQQ', // IE0032077012 - Invesco NASDAQ-100
      'VWCE', // IE00BK5BQT80 - Vanguard All-World
      'VEUR'  // IE00BK5BQV03 - Vanguard Europe
    ];
    
    console.log('🧪 Ajout des ETFs de test...');
    
    for (const symbol of testETFs) {
      try {
        await addETFToWatchlist(symbol);
        console.log(`✅ ETF ${symbol} ajouté`);
        // Petit délai entre les ajouts
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        console.error(`❌ Erreur ajout ${symbol}:`, error);
      }
    }
    
    // Recharger la watchlist après tous les ajouts
    await fetchUserWatchlist();
  };

  const deleteWatchlist = async (watchlistId: string) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer tous les ETFs de cette watchlist ?')) {
      return;
    }

    try {
      const response = await fetch(getApiUrl('/api/v1/watchlist/watchlist'), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log(result.message);
        
        // Recharger la watchlist
        await fetchUserWatchlist();
      } else {
        const error = await response.json();
        console.error('Erreur suppression watchlist:', error.detail);
      }
    } catch (error) {
      console.error('Erreur suppression watchlist:', error);
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
          <div className="flex space-x-2">
            <button
              onClick={() => setShowETFSelector(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Ajouter des ETFs
            </button>
            <button
              onClick={() => setShowDebug(!showDebug)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              🔍 Debug
            </button>
            <button
              onClick={() => addTestETFs()}
              className="inline-flex items-center px-3 py-2 border border-orange-300 text-sm font-medium rounded-md text-orange-700 bg-orange-50 hover:bg-orange-100"
            >
              🧪 Test ETFs
            </button>
          </div>
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
              onKeyPress={(e) => e.key === 'Enter' && console.log('Création désactivée')}
            />
            <button
              onClick={() => console.log('Création désactivée')}
              disabled={true}
              className="px-4 py-2 text-sm font-medium text-white bg-gray-400 rounded-md"
            >
              Créer (désactivé)
            </button>
          </div>
        </div>

        {/* Section Debug */}
        {showDebug && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">🔍 Informations Debug</h3>
            <div className="space-y-3 text-sm">
              <div><strong>Utilisateur connecté:</strong> {user ? 'Oui' : 'Non'}</div>
              <div><strong>Token présent:</strong> {localStorage.getItem('access_token') ? 'Oui' : 'Non'}</div>
              <div><strong>Nombre ETFs watchlist:</strong> {userWatchlistData.length}</div>
              <div><strong>Nombre détails ETFs:</strong> {Object.keys(etfDetails).length}</div>
              <div><strong>Loading:</strong> {loading ? 'Oui' : 'Non'}</div>
              
              {userWatchlistData.length > 0 && (
                <div>
                  <strong>Données brutes watchlist:</strong>
                  <pre className="mt-2 p-2 bg-white rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(userWatchlistData, null, 2)}
                  </pre>
                </div>
              )}
              
              {Object.keys(etfDetails).length > 0 && (
                <div>
                  <strong>Détails ETFs:</strong>
                  <pre className="mt-2 p-2 bg-white rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(etfDetails, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Liste des ETFs de la watchlist sélectionnée */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Ma Watchlist ({userWatchlistData.length} ETFs)
          </h2>
        </div>

        {userWatchlistData.length === 0 ? (
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
                  {userWatchlistData.map((etf) => {
                    const isin = etf.isin || etf.etf_isin;
                    const details = etfDetails[isin];
                    
                    return (
                      <tr key={etf.symbol || etf.isin} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {details?.name || etf.name || etf.symbol || isin}
                            </div>
                            <div className="text-sm text-gray-500">
                              {details?.symbol || etf.symbol} • {details?.sector || etf.sector || 'N/A'}
                            </div>
                            {details?.ter && (
                              <div className="text-xs text-gray-400">
                                TER: {details.ter}% • {details.region}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {etf.current_price ? 
                            `${etf.current_price.toFixed(2)} ${etf.currency || details?.currency || 'EUR'}` : 
                            'N/A'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {etf.change_percent !== undefined ? (
                            <span className={etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
                              {etf.change_percent >= 0 ? '+' : ''}{etf.change_percent.toFixed(2)}%
                            </span>
                          ) : (
                            <span className="text-gray-400">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getSignalBadge('HOLD', 75)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => window.open('/etf/' + (etf.symbol || isin), '_blank')}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                            title="Voir les détails"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => removeETFFromWatchlist(etf.symbol || isin)}
                            className="text-red-600 hover:text-red-900"
                            title="Supprimer de la watchlist"
                          >
                            <TrashIcon className="w-4 h-4" />
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
              <div className="p-4">
                <p className="text-sm text-gray-600 mb-4">
                  Utilisez la page "ETFs" pour rechercher et ajouter des ETFs à votre watchlist.
                </p>
                <a 
                  href="/etfs" 
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Aller aux ETFs →
                </a>
              </div>
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