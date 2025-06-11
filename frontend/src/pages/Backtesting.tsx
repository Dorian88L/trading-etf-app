import React, { useState } from 'react';
import BacktestingEngine from '../components/backtesting/BacktestingEngine';
import AdvancedBacktestingEngine from '../components/backtesting/AdvancedBacktestingEngine';
import BacktestResults from '../components/backtesting/BacktestResults';
import TradingSimulation from '../components/trading/TradingSimulation';

interface BacktestResult {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  numberOfTrades: number;
  finalValue: number;
  trades: any[];
  equity: any[];
}

const Backtesting: React.FC = () => {
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [savedTests, setSavedTests] = useState<any[]>([]);
  const [showSavedTests, setShowSavedTests] = useState(false);
  const [activeTab, setActiveTab] = useState<'backtest' | 'advanced' | 'simulation'>('advanced');

  const handleResultsChange = (newResults: BacktestResult | null) => {
    setResults(newResults);
  };

  const saveBacktest = () => {
    if (results) {
      const savedTest = {
        id: Date.now(),
        date: new Date().toISOString(),
        name: `Backtest ${new Date().toLocaleDateString('fr-FR')}`,
        results: results,
        config: {
          // Ces paramètres seraient normalement passés depuis le composant engine
          strategy: 'RSI',
          period: '2023-2024',
          initialCapital: 10000
        }
      };
      setSavedTests(prev => [savedTest, ...prev.slice(0, 4)]); // Garder seulement les 5 derniers
      alert('Backtest sauvegardé avec succès !');
    }
  };

  const loadBacktest = (savedTest: any) => {
    setResults(savedTest.results);
    setShowSavedTests(false);
  };

  const deleteBacktest = (id: number) => {
    setSavedTests(prev => prev.filter(test => test.id !== id));
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🧪 Backtesting & Trading</h1>
            <p className="text-gray-600 mt-2">
              Testez vos stratégies et simulez le trading automatique
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            {savedTests.length > 0 && (
              <button
                onClick={() => setShowSavedTests(!showSavedTests)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
              >
                📚 Tests sauvegardés ({savedTests.length})
              </button>
            )}
            
            {results && (
              <button
                onClick={saveBacktest}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                💾 Sauvegarder le test
              </button>
            )}
          </div>
        </div>

        {/* Onglets */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('advanced')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'advanced'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            🧪 Backtesting Avancé
          </button>
          <button
            onClick={() => setActiveTab('simulation')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'simulation'
                ? 'bg-white text-green-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            🤖 Trading Automatique
          </button>
          <button
            onClick={() => setActiveTab('backtest')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'backtest'
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📊 Backtesting Simple
          </button>
        </div>

        {/* Introduction dynamique */}
        {activeTab === 'advanced' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">🧪 Backtesting Avancé</h3>
            <div className="text-sm text-blue-800 space-y-1">
              <p>• <strong>Données réelles :</strong> Utilise les vrais prix de marché et volumes</p>
              <p>• <strong>Stratégies multiples :</strong> RSI, MACD, Bollinger et algorithmes avancés</p>
              <p>• <strong>Métriques complètes :</strong> Sharpe, Sortino, VaR, drawdown maximum</p>
              <p>• <strong>Comparaison benchmark :</strong> Performance vs buy-and-hold</p>
            </div>
          </div>
        )}

        {activeTab === 'simulation' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-medium text-green-900 mb-2">🤖 Trading Automatique</h3>
            <div className="text-sm text-green-800 space-y-1">
              <p>• <strong>Capital réel :</strong> Commencez avec 100€ et observez la croissance</p>
              <p>• <strong>Temps réel :</strong> L'algorithme trade automatiquement 24/7</p>
              <p>• <strong>Gestion du risque :</strong> Stop-loss et take-profit automatiques</p>
              <p>• <strong>Compétition :</strong> Classement des meilleures performances</p>
            </div>
          </div>
        )}

        {activeTab === 'backtest' && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-medium text-purple-900 mb-2">📊 Backtesting Simple</h3>
            <div className="text-sm text-purple-800 space-y-1">
              <p>• <strong>Interface simple :</strong> Configuration rapide et intuitive</p>
              <p>• <strong>Stratégies de base :</strong> RSI, MACD, Bandes de Bollinger</p>
              <p>• <strong>Résultats rapides :</strong> Analyse immédiate des performances</p>
              <p>• <strong>Sauvegarde :</strong> Conservez et comparez vos tests</p>
            </div>
          </div>
        )}
      </div>

      {/* Tests sauvegardés */}
      {showSavedTests && savedTests.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">📚 Tests sauvegardés</h3>
            <button
              onClick={() => setShowSavedTests(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedTests.map((test) => (
              <div key={test.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{test.name}</h4>
                    <p className="text-sm text-gray-600">
                      {new Date(test.date).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <button
                    onClick={() => deleteBacktest(test.id)}
                    className="text-red-400 hover:text-red-600 text-sm"
                  >
                    🗑️
                  </button>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Stratégie:</span>
                    <span className="font-medium">{test.config.strategy}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Rendement:</span>
                    <span className={`font-medium ${
                      test.results.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {(test.results.totalReturn * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Sharpe:</span>
                    <span className="font-medium">{test.results.sharpeRatio.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Trades:</span>
                    <span className="font-medium">{test.results.numberOfTrades}</span>
                  </div>
                </div>
                
                <button
                  onClick={() => loadBacktest(test)}
                  className="w-full mt-3 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  📊 Charger ce test
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contenu des onglets */}
      {activeTab === 'advanced' && (
        <>
          <AdvancedBacktestingEngine onResultsChange={handleResultsChange} />
          {results && (
            <BacktestResults results={results} initialCapital={(results as any).config?.initial_capital || 10000} />
          )}
        </>
      )}

      {activeTab === 'simulation' && (
        <TradingSimulation />
      )}

      {activeTab === 'backtest' && (
        <>
          <BacktestingEngine onResultsChange={handleResultsChange} />
          {results && (
            <BacktestResults results={results} initialCapital={10000} />
          )}
        </>
      )}

      {/* Section d'aide et bonnes pratiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Stratégies disponibles</h3>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-medium text-gray-900">RSI (Relative Strength Index)</h4>
              <p className="text-sm text-gray-600 mt-1">
                Achat en zone de survente (&lt;30) et vente en zone de surachat (&gt;70).
                Idéal pour les marchés en range.
              </p>
            </div>
            
            <div className="border-l-4 border-green-500 pl-4">
              <h4 className="font-medium text-gray-900">MACD</h4>
              <p className="text-sm text-gray-600 mt-1">
                Signaux générés par les croisements entre la ligne MACD et la ligne de signal.
                Efficace pour détecter les changements de tendance.
              </p>
            </div>
            
            <div className="border-l-4 border-purple-500 pl-4">
              <h4 className="font-medium text-gray-900">Bandes de Bollinger</h4>
              <p className="text-sm text-gray-600 mt-1">
                Achat près de la bande inférieure et vente près de la bande supérieure.
                Adapté aux marchés volatils.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Bonnes pratiques</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start space-x-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Testez sur des périodes suffisamment longues (minimum 1 an)</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Incluez toujours les frais de transaction dans vos calculs</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Analysez le drawdown maximum pour évaluer le risque</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Comparez toujours avec un benchmark (achat et conservation)</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-orange-600 font-bold">⚠</span>
              <span>Les performances passées ne garantissent pas les résultats futurs</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-red-600 font-bold">✗</span>
              <span>N'optimisez pas excessivement sur les données historiques (overfitting)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer informatif */}
      <div className="bg-gray-50 border rounded-lg p-6 text-center">
        <div className="text-sm text-gray-600">
          <p className="mb-2">
            <strong>Avertissement :</strong> Le backtesting est un outil d'analyse et ne constitue pas un conseil en investissement.
          </p>
          <p>
            Les résultats simulés peuvent différer significativement des performances réelles en raison de facteurs non modélisés
            (slippage, liquidité, événements de marché exceptionnels, etc.).
          </p>
        </div>
      </div>
    </div>
  );
};

export default Backtesting;