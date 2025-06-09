import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { marketAPI } from '../services/api';
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

  useEffect(() => {
    if (symbol) {
      fetchETFData();
      fetchMarketData();
    }
  }, [symbol]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchETFData = async () => {
    try {
      const data = await marketAPI.getRealETFs(symbol);
      if (data && data.length > 0) {
        setEtfData(data[0]);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement de l\'ETF:', err);
      setError('Impossible de charger les données de l\'ETF');
    }
  };

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      // Simuler des données de marché pour la démo
      const mockData = generateMockMarketData();
      setMarketData(mockData);
    } catch (err: any) {
      console.error('Erreur lors du chargement des données de marché:', err);
      setError('Impossible de charger les données de marché');
    } finally {
      setLoading(false);
    }
  };

  const generateMockMarketData = () => {
    const data = [];
    const basePrice = 100;
    let currentPrice = basePrice;
    
    for (let i = 0; i < 100; i++) {
      const change = (Math.random() - 0.5) * 4;
      currentPrice += change;
      
      const high = currentPrice + Math.random() * 2;
      const low = currentPrice - Math.random() * 2;
      const volume = Math.floor(Math.random() * 1000000) + 100000;
      
      data.push({
        date: new Date(Date.now() - (99 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        open: currentPrice - change + (Math.random() - 0.5),
        high: Math.max(high, currentPrice),
        low: Math.min(low, currentPrice),
        close: currentPrice,
        volume
      });
    }
    
    return data;
  };

  const handleIndicatorChange = (indicators: any) => {
    setIndicatorData(indicators);
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
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Signaux de trading récents</h3>
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📊</div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Signaux de trading</h4>
              <p className="text-gray-500 mb-4">
                Les signaux automatisés basés sur l'analyse technique seront bientôt disponibles.
              </p>
              
              {Object.keys(indicatorData).length > 0 && indicatorData.analysis && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h5 className="font-medium text-blue-900 mb-3">Analyse basée sur les indicateurs actuels</h5>
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
            </div>
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