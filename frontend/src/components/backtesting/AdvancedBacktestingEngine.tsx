import React, { useState, useEffect } from 'react';
import { 
  PlayIcon, 
  StopIcon, 
  CogIcon, 
  ChartBarIcon,
  CurrencyEuroIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import WalkForwardAnalysis from './WalkForwardAnalysis';

interface BacktestConfig {
  name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  strategy_type: string;
  strategy_params: any;
  etf_symbols: string[];
  rebalance_frequency: string;
  transaction_cost_pct: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  max_position_size_pct: number;
}

interface AdvancedBacktestingEngineProps {
  onResultsChange?: (results: any) => void;
}

const AdvancedBacktestingEngine: React.FC<AdvancedBacktestingEngineProps> = ({ onResultsChange }) => {
  const [config, setConfig] = useState<BacktestConfig>({
    name: `Backtest ${new Date().toLocaleDateString('fr-FR')}`,
    start_date: '2023-01-01',
    end_date: '2024-06-01',
    initial_capital: 10000,
    strategy_type: 'advanced',
    strategy_params: {},
    etf_symbols: [],
    rebalance_frequency: 'daily',
    transaction_cost_pct: 0.1,
    max_position_size_pct: 10
  });

  const [availableETFs, setAvailableETFs] = useState<any[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<any[]>([]);
  const [etfSectors, setEtfSectors] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadAvailableData();
  }, []);

  const loadAvailableData = async () => {
    try {
      // Charger les stratégies disponibles
      const strategiesRes = await fetch('/api/v1/advanced-backtesting/strategies/available');
      if (strategiesRes.ok) {
        const strategiesData = await strategiesRes.json();
        setAvailableStrategies(strategiesData.strategies || []);
      }

      // Charger les secteurs ETF
      const sectorsRes = await fetch('/api/v1/advanced-backtesting/etf/sectors');
      if (sectorsRes.ok) {
        const sectorsData = await sectorsRes.json();
        setEtfSectors(sectorsData.sectors || []);
      }

      // Charger les ETFs disponibles
      const etfsRes = await fetch('/api/v1/real-market/real-etfs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      if (etfsRes.ok) {
        const etfsData = await etfsRes.json();
        setAvailableETFs(etfsData.data || []);
      }
    } catch (error) {
      console.error('Erreur chargement données:', error);
    }
  };

  const runBacktest = async () => {
    if (config.etf_symbols.length === 0) {
      setError('Veuillez sélectionner au moins un ETF');
      return;
    }

    setIsRunning(true);
    setProgress(0);
    setError('');
    setResults(null);

    try {
      const response = await fetch('/api/v1/advanced-backtesting/backtest/run', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors du backtest');
      }

      const result = await response.json();
      setResults(result);
      
      if (onResultsChange) {
        onResultsChange(result);
      }

    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsRunning(false);
      setProgress(100);
    }
  };

  const updateConfig = (field: keyof BacktestConfig, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const getStrategyParams = (strategyType: string) => {
    const strategy = availableStrategies.find(s => s.id === strategyType);
    return strategy?.params || {};
  };

  const addETF = (symbol: string) => {
    if (!config.etf_symbols.includes(symbol)) {
      updateConfig('etf_symbols', [...config.etf_symbols, symbol]);
    }
  };

  const removeETF = (symbol: string) => {
    updateConfig('etf_symbols', config.etf_symbols.filter(s => s !== symbol));
  };

  const filteredETFs = availableETFs.filter(etf => 
    etf.name.toLowerCase().includes('') || 
    etf.symbol.toLowerCase().includes('')
  );

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Backtesting Avancé</h2>
            <p className="text-gray-600">Testez vos stratégies avec des données réelles</p>
          </div>
        </div>
        
        <button
          onClick={runBacktest}
          disabled={isRunning || config.etf_symbols.length === 0}
          className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium ${
            isRunning || config.etf_symbols.length === 0
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isRunning ? (
            <>
              <StopIcon className="h-5 w-5" />
              <span>En cours...</span>
            </>
          ) : (
            <>
              <PlayIcon className="h-5 w-5" />
              <span>Lancer le backtest</span>
            </>
          )}
        </button>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Paramètres généraux */}
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CogIcon className="h-5 w-5 mr-2" />
              Configuration générale
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom du backtest
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => updateConfig('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <CalendarIcon className="h-4 w-4 inline mr-1" />
                    Date de début
                  </label>
                  <input
                    type="date"
                    value={config.start_date}
                    onChange={(e) => updateConfig('start_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <CalendarIcon className="h-4 w-4 inline mr-1" />
                    Date de fin
                  </label>
                  <input
                    type="date"
                    value={config.end_date}
                    onChange={(e) => updateConfig('end_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <CurrencyEuroIcon className="h-4 w-4 inline mr-1" />
                  Capital initial (€)
                </label>
                <input
                  type="number"
                  value={config.initial_capital}
                  onChange={(e) => updateConfig('initial_capital', Number(e.target.value))}
                  min="100"
                  step="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stratégie de trading
                </label>
                <select
                  value={config.strategy_type}
                  onChange={(e) => updateConfig('strategy_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {availableStrategies.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </option>
                  ))}
                </select>
                {availableStrategies.find(s => s.id === config.strategy_type)?.description && (
                  <p className="text-xs text-gray-500 mt-1">
                    {availableStrategies.find(s => s.id === config.strategy_type)?.description}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Paramètres avancés */}
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
              <AdjustmentsHorizontalIcon className="h-4 w-4 mr-2" />
              Paramètres avancés
            </h4>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Frais de transaction (%)
                  </label>
                  <input
                    type="number"
                    value={config.transaction_cost_pct}
                    onChange={(e) => updateConfig('transaction_cost_pct', Number(e.target.value))}
                    min="0"
                    max="2"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Taille max position (%)
                  </label>
                  <input
                    type="number"
                    value={config.max_position_size_pct}
                    onChange={(e) => updateConfig('max_position_size_pct', Number(e.target.value))}
                    min="1"
                    max="50"
                    step="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fréquence de rééquilibrage
                </label>
                <select
                  value={config.rebalance_frequency}
                  onChange={(e) => updateConfig('rebalance_frequency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="daily">Quotidien</option>
                  <option value="weekly">Hebdomadaire</option>
                  <option value="monthly">Mensuel</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Sélection des ETFs */}
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Sélection des ETFs ({config.etf_symbols.length})
            </h3>
            
            {/* ETFs sélectionnés */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">ETFs sélectionnés</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {config.etf_symbols.length === 0 ? (
                  <p className="text-gray-500 text-sm">Aucun ETF sélectionné</p>
                ) : (
                  config.etf_symbols.map((symbol) => {
                    const etf = availableETFs.find(e => e.symbol === symbol);
                    return (
                      <div key={symbol} className="flex items-center justify-between bg-blue-50 p-2 rounded">
                        <div>
                          <span className="font-medium text-sm">{symbol}</span>
                          {etf && <span className="text-xs text-gray-600 ml-2">{etf.name}</span>}
                        </div>
                        <button
                          onClick={() => removeETF(symbol)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          ✕
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Liste des ETFs disponibles */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">ETFs disponibles</h4>
              <div className="border border-gray-300 rounded-lg max-h-60 overflow-y-auto">
                {filteredETFs.slice(0, 20).map((etf) => (
                  <div
                    key={etf.symbol}
                    className={`p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                      config.etf_symbols.includes(etf.symbol) ? 'bg-green-50' : ''
                    }`}
                    onClick={() => addETF(etf.symbol)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm">{etf.symbol}</div>
                        <div className="text-xs text-gray-600 truncate">{etf.name}</div>
                        <div className="text-xs text-gray-500">{etf.sector}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{etf.current_price?.toFixed(2)}€</div>
                        <div className={`text-xs ${
                          etf.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {etf.change_percent >= 0 ? '+' : ''}{etf.change_percent?.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {isRunning && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Exécution du backtest</span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <InformationCircleIcon className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Walk-Forward Analysis Section */}
      <div className="mt-8">
        <WalkForwardAnalysis />
      </div>

      {/* Informations supplémentaires */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">💡 Conseils pour un backtest efficace</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Utilisez une période d'au moins 6 mois pour des résultats significatifs</li>
          <li>• Diversifiez vos ETFs pour réduire les risques</li>
          <li>• Les coûts de transaction ont un impact important sur les performances</li>
          <li>• Comparez toujours avec une stratégie buy-and-hold</li>
          <li>• <strong>Walk-Forward Analysis:</strong> Validez la robustesse avec des tests sur données futures</li>
        </ul>
      </div>
    </div>
  );
};

export default AdvancedBacktestingEngine;