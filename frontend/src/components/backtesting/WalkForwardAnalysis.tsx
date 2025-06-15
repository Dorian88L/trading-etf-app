import React, { useState } from 'react';
import { apiCall } from '../../services/api';

interface WalkForwardRequest {
  etf_symbol: string;
  strategy_type: string;
  optimization_window_days: number;
  test_window_days: number;
  step_size_days: number;
  start_date?: string;
  end_date?: string;
  param_ranges?: { [key: string]: number[] };
}

interface FutureSimulationRequest {
  etf_symbol: string;
  strategy_type: string;
  simulation_weeks: number;
  use_optimized_params: boolean;
}

const WalkForwardAnalysis: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [walkForwardResults, setWalkForwardResults] = useState<any>(null);
  const [futureSimResults, setFutureSimResults] = useState<any>(null);
  const [config, setConfig] = useState<WalkForwardRequest>({
    etf_symbol: 'CSPX.L',
    strategy_type: 'rsi_mean_reversion',
    optimization_window_days: 252,
    test_window_days: 63,
    step_size_days: 21
  });

  const [futureConfig, setFutureConfig] = useState<FutureSimulationRequest>({
    etf_symbol: 'CSPX.L',
    strategy_type: 'rsi_mean_reversion',
    simulation_weeks: 12,
    use_optimized_params: true
  });

  const strategies = [
    { value: 'rsi_mean_reversion', label: 'RSI Mean Reversion' },
    { value: 'sma_crossover', label: 'SMA Crossover' },
    { value: 'bollinger_mean_reversion', label: 'Bollinger Mean Reversion' },
    { value: 'macd_momentum', label: 'MACD Momentum' }
  ];

  const etfSymbols = [
    { value: 'CSPX.L', label: 'Core S&P 500 (CSPX.L)' },
    { value: 'VWCE.L', label: 'FTSE All-World (VWCE.L)' },
    { value: 'IWDA.L', label: 'Core MSCI World (IWDA.L)' },
    { value: 'SPY', label: 'SPDR S&P 500 (SPY)' },
    { value: 'VTI', label: 'Vanguard Total Stock (VTI)' },
    { value: 'QQQ', label: 'PowerShares QQQ (QQQ)' }
  ];

  const runWalkForwardAnalysis = async () => {
    setIsRunning(true);
    try {
      const response = await apiCall('advanced-backtesting/walk-forward-analysis', 'POST', config);
      setWalkForwardResults(response.data);
    } catch (error) {
      console.error('Erreur Walk-Forward Analysis:', error);
      alert('Erreur lors de l\'analyse Walk-Forward');
    } finally {
      setIsRunning(false);
    }
  };

  const runFutureSimulation = async () => {
    setIsRunning(true);
    try {
      const response = await apiCall('advanced-backtesting/future-simulation', 'POST', futureConfig);
      setFutureSimResults(response.data);
    } catch (error) {
      console.error('Erreur simulation futures:', error);
      alert('Erreur lors de la simulation futures');
    } finally {
      setIsRunning(false);
    }
  };

  const formatPerformanceMetric = (value: number, isPercentage: boolean = false) => {
    if (isPercentage) {
      return `${(value * 100).toFixed(2)}%`;
    }
    return value.toFixed(4);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">🔬 Walk-Forward Analysis & Tests Futurs</h2>
        <p className="text-gray-600">
          Validation robuste des stratégies avec optimisation continue et tests sur données futures simulées
        </p>
      </div>

      {/* Configuration Walk-Forward */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">📊 Walk-Forward Analysis</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ETF</label>
              <select
                value={config.etf_symbol}
                onChange={(e) => setConfig({ ...config, etf_symbol: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {etfSymbols.map(etf => (
                  <option key={etf.value} value={etf.value}>{etf.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stratégie</label>
              <select
                value={config.strategy_type}
                onChange={(e) => setConfig({ ...config, strategy_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {strategies.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>{strategy.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fenêtre optimisation (jours)</label>
              <input
                type="number"
                value={config.optimization_window_days}
                onChange={(e) => setConfig({ ...config, optimization_window_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="30"
                max="500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fenêtre test (jours)</label>
              <input
                type="number"
                value={config.test_window_days}
                onChange={(e) => setConfig({ ...config, test_window_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="7"
                max="180"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pas avancement (jours)</label>
              <input
                type="number"
                value={config.step_size_days}
                onChange={(e) => setConfig({ ...config, step_size_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="60"
              />
            </div>
          </div>

          <button
            onClick={runWalkForwardAnalysis}
            disabled={isRunning}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
          >
            {isRunning ? '🔄 Analyse en cours...' : '🚀 Lancer Walk-Forward Analysis'}
          </button>
        </div>

        {/* Configuration Test Futures */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">🔮 Test avec Données Futures</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ETF</label>
              <select
                value={futureConfig.etf_symbol}
                onChange={(e) => setFutureConfig({ ...futureConfig, etf_symbol: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {etfSymbols.map(etf => (
                  <option key={etf.value} value={etf.value}>{etf.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stratégie</label>
              <select
                value={futureConfig.strategy_type}
                onChange={(e) => setFutureConfig({ ...futureConfig, strategy_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {strategies.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>{strategy.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Simulation (semaines)</label>
            <input
              type="number"
              value={futureConfig.simulation_weeks}
              onChange={(e) => setFutureConfig({ ...futureConfig, simulation_weeks: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              min="4"
              max="52"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="useOptimized"
              checked={futureConfig.use_optimized_params}
              onChange={(e) => setFutureConfig({ ...futureConfig, use_optimized_params: e.target.checked })}
              className="rounded border-gray-300 text-green-600 focus:ring-green-500"
            />
            <label htmlFor="useOptimized" className="text-sm text-gray-700">
              Utiliser paramètres optimisés
            </label>
          </div>

          <button
            onClick={runFutureSimulation}
            disabled={isRunning}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium"
          >
            {isRunning ? '🔄 Simulation en cours...' : '🔮 Lancer Test Futures'}
          </button>
        </div>
      </div>

      {/* Résultats Walk-Forward */}
      {walkForwardResults && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">📊 Résultats Walk-Forward Analysis</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4">
              <div className="text-sm text-gray-600">Périodes analysées</div>
              <div className="text-2xl font-bold text-blue-600">
                {walkForwardResults.summary?.num_periods || 0}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <div className="text-sm text-gray-600">Rendement cumulé</div>
              <div className="text-2xl font-bold text-blue-600">
                {formatPerformanceMetric(walkForwardResults.summary?.cumulative_return || 0, true)}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <div className="text-sm text-gray-600">Sharpe moyen</div>
              <div className="text-2xl font-bold text-blue-600">
                {formatPerformanceMetric(walkForwardResults.summary?.average_sharpe_ratio || 0)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">Métriques de Robustesse</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Score de robustesse:</span>
                  <span className={`font-bold ${getScoreColor(walkForwardResults.robustness_score || 0)}`}>
                    {formatPerformanceMetric(walkForwardResults.robustness_score || 0, true)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Stabilité paramètres:</span>
                  <span className={`font-bold ${getScoreColor(walkForwardResults.summary?.parameter_stability || 0)}`}>
                    {formatPerformanceMetric(walkForwardResults.summary?.parameter_stability || 0, true)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Drawdown maximum:</span>
                  <span className="font-bold text-red-600">
                    {formatPerformanceMetric(walkForwardResults.summary?.maximum_drawdown || 0, true)}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">Performance Globale</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Total trades:</span>
                  <span className="font-bold">{walkForwardResults.summary?.total_trades || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Taux de réussite:</span>
                  <span className="font-bold text-green-600">
                    {formatPerformanceMetric(walkForwardResults.summary?.average_win_rate || 0, true)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Résultats Test Futures */}
      {futureSimResults && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-4">🔮 Résultats Test avec Données Futures</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Performance Historique vs Future */}
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">📈 Comparaison Performance</h4>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-gray-600">Historique</div>
                    <div className="font-bold text-blue-600">
                      {formatPerformanceMetric(futureSimResults.historical_performance?.total_return || 0, true)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Sharpe: {formatPerformanceMetric(futureSimResults.historical_performance?.sharpe_ratio || 0)}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-gray-600">Futur Simulé</div>
                    <div className="font-bold text-green-600">
                      {formatPerformanceMetric(futureSimResults.future_performance?.total_return || 0, true)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Sharpe: {formatPerformanceMetric(futureSimResults.future_performance?.sharpe_ratio || 0)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Analyse de Robustesse */}
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">🛡️ Analyse de Robustesse</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Consistance performance:</span>
                  <span className={`font-bold ${getScoreColor(futureSimResults.robustness_analysis?.performance_consistency || 0)}`}>
                    {formatPerformanceMetric(futureSimResults.robustness_analysis?.performance_consistency || 0, true)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Efficacité paramètres:</span>
                  <span className={`font-bold ${getScoreColor(futureSimResults.robustness_analysis?.parameter_effectiveness || 0)}`}>
                    {formatPerformanceMetric(futureSimResults.robustness_analysis?.parameter_effectiveness || 0, true)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Score forward-looking:</span>
                  <span className={`font-bold ${getScoreColor(futureSimResults.robustness_analysis?.forward_looking_score || 0)}`}>
                    {formatPerformanceMetric(futureSimResults.robustness_analysis?.forward_looking_score || 0, true)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Validation Results */}
          <div className="mt-4 p-4 bg-white rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">✅ Résultats de Validation</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`flex items-center space-x-2 p-3 rounded-lg ${
                futureSimResults.validation_results?.strategy_stable ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <span className="text-lg">
                  {futureSimResults.validation_results?.strategy_stable ? '✅' : '❌'}
                </span>
                <div>
                  <div className="font-medium">Stratégie Stable</div>
                  <div className="text-xs text-gray-600">Cohérence > 70%</div>
                </div>
              </div>

              <div className={`flex items-center space-x-2 p-3 rounded-lg ${
                futureSimResults.validation_results?.params_effective ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <span className="text-lg">
                  {futureSimResults.validation_results?.params_effective ? '✅' : '❌'}
                </span>
                <div>
                  <div className="font-medium">Paramètres Efficaces</div>
                  <div className="text-xs text-gray-600">Efficacité > 60%</div>
                </div>
              </div>

              <div className={`flex items-center space-x-2 p-3 rounded-lg ${
                futureSimResults.validation_results?.future_ready ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <span className="text-lg">
                  {futureSimResults.validation_results?.future_ready ? '✅' : '❌'}
                </span>
                <div>
                  <div className="font-medium">Prêt pour le Futur</div>
                  <div className="text-xs text-gray-600">Score forward > 65%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Guide d'utilisation */}
      <div className="bg-gray-50 border rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">💡 Guide d'Utilisation</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <p>• <strong>Walk-Forward Analysis:</strong> Optimise les paramètres sur une période puis teste sur la suivante, répète le processus</p>
          <p>• <strong>Test Données Futures:</strong> Simule des données futures basées sur les caractéristiques historiques et teste la robustesse</p>
          <p>• <strong>Validation:</strong> Une stratégie robuste doit maintenir ses performances sur données non-vues</p>
          <p>• <strong>Scores > 70%:</strong> Indiquent une stratégie fiable pour le trading automatique</p>
        </div>
      </div>
    </div>
  );
};

export default WalkForwardAnalysis;