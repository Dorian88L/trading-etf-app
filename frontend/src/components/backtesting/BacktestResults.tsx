import React, { useState } from 'react';

interface Trade {
  date: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  value: number;
  commission: number;
  signal: string;
}

interface EquityPoint {
  date: string;
  value: number;
  benchmark: number;
}

interface BacktestResult {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  numberOfTrades: number;
  finalValue: number;
  trades: Trade[];
  equity: EquityPoint[];
}

interface BacktestResultsProps {
  results: BacktestResult | null;
  initialCapital: number;
}

const BacktestResults: React.FC<BacktestResultsProps> = ({ results, initialCapital }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'equity' | 'trades' | 'analysis'>('overview');

  if (!results) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="text-4xl mb-4">📊</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun résultat de backtest</h3>
        <p className="text-gray-500">Lancez un backtest pour voir les résultats d'analyse.</p>
      </div>
    );
  }

  const getPerformanceColor = (value: number, isPositive: boolean = true) => {
    if (isPositive) {
      return value >= 0 ? 'text-green-600' : 'text-red-600';
    } else {
      return value <= 0 ? 'text-green-600' : 'text-red-600';
    }
  };

  const formatCurrency = (value: number) => {
    return value.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const calculateMonthlyReturns = () => {
    const monthlyReturns: { [month: string]: number } = {};
    const monthlyValues: { [month: string]: { start: number; end: number } } = {};

    results.equity.forEach(point => {
      const date = new Date(point.date);
      const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
      
      if (!monthlyValues[monthKey]) {
        monthlyValues[monthKey] = { start: point.value, end: point.value };
      } else {
        monthlyValues[monthKey].end = point.value;
      }
    });

    Object.entries(monthlyValues).forEach(([month, values]) => {
      monthlyReturns[month] = (values.end - values.start) / values.start;
    });

    return monthlyReturns;
  };

  const getBenchmarkComparison = () => {
    if (results.equity.length === 0) return null;
    
    const strategyReturn = results.totalReturn;
    const benchmarkReturn = (results.equity[results.equity.length - 1].benchmark - initialCapital) / initialCapital;
    
    return {
      strategy: strategyReturn,
      benchmark: benchmarkReturn,
      outperformance: strategyReturn - benchmarkReturn
    };
  };

  const getRiskMetrics = () => {
    // Calculate additional risk metrics
    const dailyReturns = [];
    for (let i = 1; i < results.equity.length; i++) {
      const dailyReturn = (results.equity[i].value - results.equity[i - 1].value) / results.equity[i - 1].value;
      dailyReturns.push(dailyReturn);
    }

    // Downside deviation
    const negativeReturns = dailyReturns.filter(r => r < 0);
    const downsideDeviation = negativeReturns.length > 0 
      ? Math.sqrt(negativeReturns.reduce((sum, r) => sum + r * r, 0) / negativeReturns.length) * Math.sqrt(252)
      : 0;

    // Sortino ratio
    const sortinoRatio = downsideDeviation > 0 ? results.annualizedReturn / downsideDeviation : 0;

    return {
      downsideDeviation,
      sortinoRatio,
      worstDay: Math.min(...dailyReturns),
      bestDay: Math.max(...dailyReturns)
    };
  };

  const monthlyReturns = calculateMonthlyReturns();
  const benchmarkComparison = getBenchmarkComparison();
  const riskMetrics = getRiskMetrics();

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">📈 Résultats du Backtesting</h3>
        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
          <span>Capital initial: {formatCurrency(initialCapital)}</span>
          <span>Capital final: {formatCurrency(results.finalValue)}</span>
          <span className={getPerformanceColor(results.totalReturn)}>
            Gain/Perte: {formatCurrency(results.finalValue - initialCapital)} ({formatPercentage(results.totalReturn)})
          </span>
        </div>
      </div>

      {/* Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📊 Vue d'ensemble
          </button>
          <button
            onClick={() => setActiveTab('equity')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'equity'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📈 Courbe d'équité
          </button>
          <button
            onClick={() => setActiveTab('trades')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'trades'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            💼 Trades ({results.numberOfTrades})
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🔬 Analyse détaillée
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Métriques principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {formatPercentage(results.totalReturn)}
                </div>
                <div className="text-sm text-blue-800">Rendement total</div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatPercentage(results.annualizedReturn)}
                </div>
                <div className="text-sm text-green-800">Rendement annualisé</div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {results.sharpeRatio.toFixed(2)}
                </div>
                <div className="text-sm text-purple-800">Ratio de Sharpe</div>
              </div>
              
              <div className="bg-red-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-red-600">
                  {formatPercentage(results.maxDrawdown)}
                </div>
                <div className="text-sm text-red-800">Drawdown maximum</div>
              </div>
            </div>

            {/* Comparaison avec le benchmark */}
            {benchmarkComparison && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">📊 Comparaison avec le benchmark</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-blue-600">
                      {formatPercentage(benchmarkComparison.strategy)}
                    </div>
                    <div className="text-sm text-gray-600">Stratégie</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-600">
                      {formatPercentage(benchmarkComparison.benchmark)}
                    </div>
                    <div className="text-sm text-gray-600">Benchmark</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-lg font-semibold ${getPerformanceColor(benchmarkComparison.outperformance)}`}>
                      {benchmarkComparison.outperformance >= 0 ? '+' : ''}{formatPercentage(benchmarkComparison.outperformance)}
                    </div>
                    <div className="text-sm text-gray-600">Surperformance</div>
                  </div>
                </div>
              </div>
            )}

            {/* Métriques secondaires */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-white border rounded-lg">
                <div className="text-lg font-semibold">{formatPercentage(results.volatility)}</div>
                <div className="text-sm text-gray-600">Volatilité</div>
              </div>
              
              <div className="text-center p-3 bg-white border rounded-lg">
                <div className="text-lg font-semibold">{formatPercentage(results.winRate)}</div>
                <div className="text-sm text-gray-600">Taux de réussite</div>
              </div>
              
              <div className="text-center p-3 bg-white border rounded-lg">
                <div className="text-lg font-semibold">{results.numberOfTrades}</div>
                <div className="text-sm text-gray-600">Nombre de trades</div>
              </div>
              
              <div className="text-center p-3 bg-white border rounded-lg">
                <div className="text-lg font-semibold">
                  {(results.numberOfTrades / (Object.keys(monthlyReturns).length || 1)).toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Trades/mois</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'equity' && (
          <div className="space-y-6">
            {/* Graphique simplifié de la courbe d'équité */}
            <div className="bg-gray-50 p-6 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4">Evolution du capital</h4>
              <div className="h-64 flex items-end justify-between space-x-1">
                {results.equity.slice(0, 50).map((point, index) => {
                  const height = ((point.value - initialCapital) / initialCapital) * 100 + 50;
                  const benchmarkHeight = ((point.benchmark - initialCapital) / initialCapital) * 100 + 50;
                  return (
                    <div key={index} className="flex flex-col items-center space-y-1 flex-1">
                      <div
                        className="bg-blue-500 w-full rounded-t"
                        style={{ height: `${Math.max(height, 5)}%` }}
                        title={`Stratégie: ${formatCurrency(point.value)}`}
                      />
                      <div
                        className="bg-gray-300 w-full rounded-t"
                        style={{ height: `${Math.max(benchmarkHeight, 5)}%` }}
                        title={`Benchmark: ${formatCurrency(point.benchmark)}`}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>Début</span>
                <span>Fin</span>
              </div>
              <div className="flex items-center space-x-4 mt-3 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded"></div>
                  <span>Stratégie</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-gray-300 rounded"></div>
                  <span>Benchmark</span>
                </div>
              </div>
            </div>

            {/* Rendements mensuels */}
            <div>
              <h4 className="font-medium text-gray-900 mb-4">Rendements mensuels</h4>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                {Object.entries(monthlyReturns).map(([month, return_val]) => (
                  <div
                    key={month}
                    className={`p-3 rounded text-center text-sm ${
                      return_val >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}
                  >
                    <div className="font-medium">{month}</div>
                    <div>{formatPercentage(return_val)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trades' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-medium text-gray-900">Historique des trades</h4>
              <div className="text-sm text-gray-600">
                {results.trades.length} trade{results.trades.length > 1 ? 's' : ''} exécuté{results.trades.length > 1 ? 's' : ''}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbole</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantité</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prix</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valeur</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Commission</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Signal</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.trades.slice(-20).map((trade, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {new Date(trade.date).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          trade.type === 'BUY' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.type === 'BUY' ? '📈 ACHAT' : '📉 VENTE'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{trade.symbol}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{trade.quantity}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{formatCurrency(trade.price)}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{formatCurrency(trade.value)}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{formatCurrency(trade.commission)}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{trade.signal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {results.trades.length > 20 && (
              <div className="text-center text-sm text-gray-500">
                Affichage des 20 derniers trades sur {results.trades.length}
              </div>
            )}
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {/* Métriques de risque avancées */}
            <div>
              <h4 className="font-medium text-gray-900 mb-4">📊 Analyse des risques</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <div className="text-lg font-bold text-purple-600">
                    {formatPercentage(riskMetrics.downsideDeviation)}
                  </div>
                  <div className="text-sm text-purple-800">Déviation négative</div>
                </div>
                
                <div className="bg-indigo-50 p-4 rounded-lg text-center">
                  <div className="text-lg font-bold text-indigo-600">
                    {riskMetrics.sortinoRatio.toFixed(2)}
                  </div>
                  <div className="text-sm text-indigo-800">Ratio de Sortino</div>
                </div>
                
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-lg font-bold text-red-600">
                    {formatPercentage(riskMetrics.worstDay)}
                  </div>
                  <div className="text-sm text-red-800">Pire journée</div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-lg font-bold text-green-600">
                    {formatPercentage(riskMetrics.bestDay)}
                  </div>
                  <div className="text-sm text-green-800">Meilleure journée</div>
                </div>
              </div>
            </div>

            {/* Résumé de performance */}
            <div className="bg-gray-50 p-6 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4">🏆 Résumé de performance</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span>Performance absolue:</span>
                  <span className={`font-medium ${getPerformanceColor(results.totalReturn)}`}>
                    {formatPercentage(results.totalReturn)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Performance annualisée:</span>
                  <span className={`font-medium ${getPerformanceColor(results.annualizedReturn)}`}>
                    {formatPercentage(results.annualizedReturn)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Volatilité annualisée:</span>
                  <span className="font-medium">{formatPercentage(results.volatility)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ratio rendement/risque:</span>
                  <span className="font-medium">{(results.annualizedReturn / results.volatility).toFixed(2)}</span>
                </div>
                {benchmarkComparison && (
                  <div className="flex justify-between border-t pt-2 mt-2">
                    <span>Alpha vs benchmark:</span>
                    <span className={`font-medium ${getPerformanceColor(benchmarkComparison.outperformance)}`}>
                      {formatPercentage(benchmarkComparison.outperformance)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Recommandations */}
            <div className="bg-blue-50 p-6 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-4">💡 Recommandations</h4>
              <div className="space-y-2 text-sm text-blue-800">
                {results.sharpeRatio > 1 && (
                  <div className="flex items-start space-x-2">
                    <span>✅</span>
                    <span>Excellent ratio de Sharpe - La stratégie génère un bon rendement ajusté du risque.</span>
                  </div>
                )}
                {results.maxDrawdown > 0.2 && (
                  <div className="flex items-start space-x-2">
                    <span>⚠️</span>
                    <span>Drawdown élevé - Considérez l'ajout de mécanismes de gestion des risques.</span>
                  </div>
                )}
                {results.winRate < 0.4 && (
                  <div className="flex items-start space-x-2">
                    <span>📊</span>
                    <span>Taux de réussite faible - Vérifiez la logique de sortie de la stratégie.</span>
                  </div>
                )}
                {results.numberOfTrades < 10 && (
                  <div className="flex items-start space-x-2">
                    <span>🔄</span>
                    <span>Peu de trades - Considérez l'ajustement des paramètres pour plus d'activité.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BacktestResults;