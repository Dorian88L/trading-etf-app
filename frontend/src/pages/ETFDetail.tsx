import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { marketAPI, signalsAPI } from '../services/api';
import AdvancedChart from '../components/charts/AdvancedChart';
import AdvancedIndicators from '../components/charts/AdvancedIndicators';
import PriceAlertCreator from '../components/alerts/PriceAlertCreator';

const ETFDetail: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const [etfData, setEtfData] = useState<any>(null);
  const [marketData, setMarketData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'signals'>('overview');
  const [showPriceAlert, setShowPriceAlert] = useState(false);
  const [indicatorData, setIndicatorData] = useState<any>({});
  const [realTimePrice, setRealTimePrice] = useState<number | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);
  const [latestSignals, setLatestSignals] = useState<any[]>([]);

  useEffect(() => {
    if (symbol) {
      fetchETFData();
      fetchMarketData();
      fetchSignals();
    }
  }, [symbol]); // eslint-disable-line react-hooks/exhaustive-deps

  // Actualisation automatique toutes les 30 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      if (symbol) {
        fetchETFData();
        setRefreshCount(prev => prev + 1);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [symbol]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchETFData = async () => {
    try {
      const data = await marketAPI.getRealETFs(symbol);
      if (data && data.length > 0) {
        setEtfData(data[0]);
        setRealTimePrice(data[0].regularMarketPrice);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement de l\'ETF:', err);
      setError('Impossible de charger les données de l\'ETF. Veuillez réessayer plus tard.');
    }
  };

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      
      if (!symbol) {
        setError('Symbole ETF manquant');
        return;
      }

      // Récupérer les données historiques réelles depuis la nouvelle API
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8443'}/api/v1/historical/etf/${symbol}/historical?period=3mo&include_indicators=true`);
      
      if (!response.ok) {
        throw new Error(`Erreur API: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.historical_data && data.historical_data.length > 0) {
        // Convertir les données au format attendu par le graphique
        const formattedData = data.historical_data.map((point: any) => ({
          date: new Date(point.timestamp).toISOString().split('T')[0],
          open: point.open_price,
          high: point.high_price,
          low: point.low_price,
          close: point.close_price,
          volume: point.volume
        }));
        
        setMarketData(formattedData);
        
        // Mettre à jour les indicateurs techniques s'ils sont disponibles
        if (data.technical_indicators) {
          setIndicatorData(data.technical_indicators);
        }
      } else {
        throw new Error('Aucune donnée historique disponible');
      }
      
    } catch (err: any) {
      console.error('Erreur lors du chargement des données de marché:', err);
      setError(`Impossible de charger les données de marché: ${err.message}`);
      
      // Fallback: essayer de récupérer des données simplifiées
      try {
        const fallbackResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8443'}/api/v1/historical/etf/${symbol}/price-history?days=90`);
        
        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json();
          
          if (fallbackData.chart_data && fallbackData.chart_data.length > 0) {
            const formattedData = fallbackData.chart_data.map((point: any) => ({
              date: new Date(point.date).toISOString().split('T')[0],
              open: point.price,
              high: point.price * 1.02,
              low: point.price * 0.98,
              close: point.price,
              volume: point.volume || 100000
            }));
            
            setMarketData(formattedData);
            setError(''); // Clear error if fallback works
          }
        }
      } catch (fallbackErr) {
        console.error('Fallback aussi échoué:', fallbackErr);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleIndicatorChange = (indicators: any) => {
    setIndicatorData(indicators);
  };

  const fetchSignals = async () => {
    try {
      if (symbol) {
        const data = await signalsAPI.getLatestSignalsForETF(symbol, 10);
        setLatestSignals(data || []);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des signaux:', err);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!symbol) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <p className="text-yellow-600">Symbole ETF manquant</p>
        </div>
      </div>
    );
  }

  const currentPrice = etfData?.regularMarketPrice || marketData[marketData.length - 1]?.close || 0;
  const change = etfData?.regularMarketChange || 0;
  const changePercent = etfData?.regularMarketChangePercent || 0;

  return (
    <div className="p-6">
      {/* En-tête */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              📈 {symbol?.toUpperCase()}
            </h1>
            {etfData && (
              <p className="text-gray-600 mb-4">{etfData.longName || etfData.shortName}</p>
            )}
            
            {/* Prix actuel */}
            <div className="flex items-center space-x-4">
              <span className="text-3xl font-bold text-gray-900">
                {currentPrice.toFixed(2)} €
              </span>
              <span className={`text-lg font-medium ${
                change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {change >= 0 ? '+' : ''}{change.toFixed(2)} 
                ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Temps réel</span>
              {refreshCount > 0 && (
                <span className="text-xs">({refreshCount} mises à jour)</span>
              )}
            </div>
            <button
              onClick={() => {
                fetchETFData();
                setRefreshCount(prev => prev + 1);
              }}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm"
            >
              🔄 Actualiser
            </button>
            <button
              onClick={() => setShowPriceAlert(true)}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center gap-2"
            >
              💰 Créer une alerte
            </button>
          </div>
        </div>

        {/* Informations supplémentaires */}
        {etfData && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Volume</p>
              <p className="font-semibold text-gray-900">
                {etfData.regularMarketVolume?.toLocaleString() || 'N/A'}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Cap. boursière</p>
              <p className="font-semibold text-gray-900">
                {etfData.marketCap ? `${(etfData.marketCap / 1e9).toFixed(2)}B €` : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Ratio de frais</p>
              <p className="font-semibold text-gray-900">
                {etfData.annualReportExpenseRatio ? `${(etfData.annualReportExpenseRatio * 100).toFixed(2)}%` : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Devise</p>
              <p className="font-semibold text-gray-900">
                {etfData.currency || 'USD'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Onglets */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📊 Vue d'ensemble
          </button>
          <button
            onClick={() => setActiveTab('technical')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'technical'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🔬 Analyse technique
          </button>
          <button
            onClick={() => setActiveTab('signals')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'signals'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🎯 Signaux de trading
          </button>
        </nav>
      </div>

      {/* Contenu des onglets */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <AdvancedChart
            data={marketData}
            etfName={symbol}
            height={400}
          />
          
          {etfData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Informations générales</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Nom complet:</span>
                    <span className="font-medium">{etfData.longName || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Secteur:</span>
                    <span className="font-medium">{etfData.sector || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Exchange:</span>
                    <span className="font-medium">{etfData.exchange || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type de fonds:</span>
                    <span className="font-medium">{etfData.fundFamily || 'ETF'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">💰 Métriques financières</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Prix d'ouverture:</span>
                    <span className="font-medium">{etfData.regularMarketOpen?.toFixed(2) || 'N/A'} €</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Plus haut (52s):</span>
                    <span className="font-medium">{etfData.fiftyTwoWeekHigh?.toFixed(2) || 'N/A'} €</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Plus bas (52s):</span>
                    <span className="font-medium">{etfData.fiftyTwoWeekLow?.toFixed(2) || 'N/A'} €</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Moyenne 50j:</span>
                    <span className="font-medium">{etfData.fiftyDayAverage?.toFixed(2) || 'N/A'} €</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'technical' && (
        <div className="space-y-6">
          <AdvancedIndicators
            symbol={symbol}
            marketData={marketData}
            onIndicatorChange={handleIndicatorChange}
          />
        </div>
      )}

      {activeTab === 'signals' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Signaux de trading pour {symbol}</h3>
            
            {/* Signal principal généré */}
            <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-900">Signal algorithmique actuel</h4>
                <span className="text-xs text-gray-500">Mise à jour: {new Date().toLocaleTimeString('fr-FR')}</span>
              </div>
              
              {/* Utiliser les vrais signaux de l'API */}
              {latestSignals && latestSignals.length > 0 ? (() => {
                const latestSignal = latestSignals[0];
                
                return (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className={`text-2xl font-bold mb-1 ${
                        latestSignal.type === 'BUY' ? 'text-green-600' :
                        latestSignal.type === 'SELL' ? 'text-red-600' :
                        latestSignal.type === 'HOLD' ? 'text-blue-600' :
                        'text-gray-600'
                      }`}>
                        {latestSignal.type}
                      </div>
                      <div className="text-sm text-gray-600">Signal</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-bold mb-1 ${
                        latestSignal.confidence >= 80 ? 'text-green-600' :
                        latestSignal.confidence >= 60 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {latestSignal.confidence.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Confiance</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold mb-1 text-gray-900">
                        {latestSignal.target_price ? latestSignal.target_price.toFixed(2) : 'N/A'}€
                      </div>
                      <div className="text-sm text-gray-600">Prix cible</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold mb-1 text-gray-900">
                        {latestSignal.stop_loss ? latestSignal.stop_loss.toFixed(2) : 'N/A'}€
                      </div>
                      <div className="text-sm text-gray-600">Stop-loss</div>
                    </div>
                  </div>
                );
              })() : (
                <div className="text-center py-4 text-gray-500">
                  Aucun signal disponible pour cet ETF
                </div>
              )}
            </div>
            
            {/* Analyse des indicateurs */}
            {Object.keys(indicatorData).length > 0 && indicatorData.analysis && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h5 className="font-medium text-blue-900 mb-3">Analyse technique détaillée</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  {Object.entries(indicatorData.analysis).map(([key, analysis]: [string, any]) => (
                    <div key={key} className="bg-white p-3 rounded border">
                      <div className="font-medium text-gray-900 mb-1 capitalize">{key}</div>
                      <div className={`text-sm font-medium mb-1 ${
                        ['HAUSSIER', 'SURVENTE'].includes(analysis.signal) ? 'text-green-600' :
                        ['BAISSIER', 'SURACHAT'].includes(analysis.signal) ? 'text-red-600' :
                        'text-gray-600'
                      }`}>
                        {analysis.signal}
                      </div>
                      <div className="text-xs text-gray-500">{analysis.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Historique des signaux réels */}
            {latestSignals && latestSignals.length > 1 && (
              <div className="mt-6">
                <h5 className="font-medium text-gray-900 mb-3">Historique des signaux récents</h5>
                <div className="space-y-2">
                  {latestSignals.slice(0, 5).map((signal, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-gray-600">
                          {new Date(signal.created_at).toLocaleDateString('fr-FR')}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          signal.type === 'BUY' ? 'bg-green-100 text-green-800' :
                          signal.type === 'SELL' ? 'bg-red-100 text-red-800' :
                          signal.type === 'HOLD' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {signal.type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {signal.confidence.toFixed(1)}% confiance
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal d'alerte de prix */}
      <PriceAlertCreator
        isOpen={showPriceAlert}
        onClose={() => setShowPriceAlert(false)}
        onAlertCreated={() => {}}
        etfSymbol={symbol}
        currentPrice={currentPrice}
      />
    </div>
  );
};

export default ETFDetail;