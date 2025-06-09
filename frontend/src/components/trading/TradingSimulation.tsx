import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  CurrencyEuroIcon,
  ClockIcon,
  ChartBarIcon,
  TrophyIcon,
  RocketLaunchIcon,
  CogIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface TradingSimulationConfig {
  name: string;
  initial_capital: number;
  duration_days: number;
  strategy_type: string;
  risk_level: string;
  allowed_etf_sectors: string[];
  rebalance_frequency_hours: number;
  auto_stop_loss: boolean;
  auto_take_profit: boolean;
}

interface SimulationResult {
  id: string;
  config: TradingSimulationConfig;
  current_value: number;
  total_return_pct: number;
  daily_returns: any[];
  active_positions: any;
  completed_trades: any[];
  risk_metrics: any;
  next_rebalance: string;
  status: string;
  created_at: string;
  last_updated: string;
  days_remaining: number;
}

const TradingSimulation: React.FC = () => {
  const [config, setConfig] = useState<TradingSimulationConfig>({
    name: `Trading Bot ${new Date().toLocaleDateString('fr-FR')}`,
    initial_capital: 100,
    duration_days: 30,
    strategy_type: 'advanced',
    risk_level: 'moderate',
    allowed_etf_sectors: [],
    rebalance_frequency_hours: 24,
    auto_stop_loss: true,
    auto_take_profit: true
  });

  const [activeSimulations, setActiveSimulations] = useState<SimulationResult[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [availableSectors, setAvailableSectors] = useState<string[]>([]);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [selectedSimulation, setSelectedSimulation] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadData();
    const interval = setInterval(loadActiveSimulations, 30000); // Actualiser toutes les 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    await Promise.all([
      loadAvailableSectors(),
      loadActiveSimulations(),
      loadLeaderboard()
    ]);
  };

  const loadAvailableSectors = async () => {
    try {
      const response = await fetch('/api/v1/advanced-backtesting/etf/sectors');
      if (response.ok) {
        const data = await response.json();
        setAvailableSectors(data.sectors || []);
      }
    } catch (error) {
      console.error('Erreur chargement secteurs:', error);
    }
  };

  const loadActiveSimulations = async () => {
    try {
      const response = await fetch('/api/v1/advanced-backtesting/simulation/active', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setActiveSimulations(data);
      }
    } catch (error) {
      console.error('Erreur chargement simulations:', error);
    }
  };

  const loadLeaderboard = async () => {
    try {
      const response = await fetch('/api/v1/advanced-backtesting/simulation/leaderboard?timeframe=week&limit=5');
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.leaderboard || []);
      }
    } catch (error) {
      console.error('Erreur chargement leaderboard:', error);
    }
  };

  const startSimulation = async () => {
    setIsCreating(true);
    setError('');

    try {
      const response = await fetch('/api/v1/advanced-backtesting/simulation/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la création');
      }

      const simulation = await response.json();
      setActiveSimulations(prev => [...prev, simulation]);
      
      // Reset le formulaire
      setConfig(prev => ({
        ...prev,
        name: `Trading Bot ${new Date().toLocaleDateString('fr-FR')}`
      }));

    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsCreating(false);
    }
  };

  const pauseSimulation = async (simulationId: string) => {
    try {
      const response = await fetch(`/api/v1/advanced-backtesting/simulation/${simulationId}/pause`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await loadActiveSimulations();
      }
    } catch (error) {
      console.error('Erreur pause simulation:', error);
    }
  };

  const resumeSimulation = async (simulationId: string) => {
    try {
      const response = await fetch(`/api/v1/advanced-backtesting/simulation/${simulationId}/resume`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await loadActiveSimulations();
      }
    } catch (error) {
      console.error('Erreur reprise simulation:', error);
    }
  };

  const stopSimulation = async (simulationId: string) => {
    try {
      const response = await fetch(`/api/v1/advanced-backtesting/simulation/${simulationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setActiveSimulations(prev => prev.filter(s => s.id !== simulationId));
      }
    } catch (error) {
      console.error('Erreur arrêt simulation:', error);
    }
  };

  const updateConfig = (field: keyof TradingSimulationConfig, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const toggleSector = (sector: string) => {
    setConfig(prev => ({
      ...prev,
      allowed_etf_sectors: prev.allowed_etf_sectors.includes(sector)
        ? prev.allowed_etf_sectors.filter(s => s !== sector)
        : [...prev.allowed_etf_sectors, sector]
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'completed': return 'text-blue-600 bg-blue-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'running': return '🟢 En cours';
      case 'paused': return '⏸️ En pause';
      case 'completed': return '✅ Terminé';
      case 'error': return '❌ Erreur';
      default: return status;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-4">
          <RocketLaunchIcon className="h-8 w-8 text-green-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Automatique</h1>
            <p className="text-gray-600">Simulation de trading avec 100€ initial</p>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-medium text-green-900 mb-2">🤖 Comment ça marche</h3>
          <div className="text-sm text-green-800 space-y-1">
            <p>• <strong>Capital initial :</strong> Commencez avec 100€ virtuels</p>
            <p>• <strong>Trading automatique :</strong> L'algorithme achète/vend selon la stratégie</p>
            <p>• <strong>Données réelles :</strong> Utilise les vrais prix du marché en temps réel</p>
            <p>• <strong>Objectif :</strong> Maximiser le rendement sur la période définie</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Configuration nouvelle simulation */}
        <div className="xl:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <CogIcon className="h-5 w-5 mr-2" />
              Nouvelle Simulation
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de la simulation
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => updateConfig('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <CurrencyEuroIcon className="h-4 w-4 inline mr-1" />
                    Capital (€)
                  </label>
                  <input
                    type="number"
                    value={config.initial_capital}
                    onChange={(e) => updateConfig('initial_capital', Number(e.target.value))}
                    min="50"
                    max="1000"
                    step="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <ClockIcon className="h-4 w-4 inline mr-1" />
                    Durée (jours)
                  </label>
                  <input
                    type="number"
                    value={config.duration_days}
                    onChange={(e) => updateConfig('duration_days', Number(e.target.value))}
                    min="7"
                    max="365"
                    step="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Niveau de risque
                </label>
                <select
                  value={config.risk_level}
                  onChange={(e) => updateConfig('risk_level', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="conservative">🛡️ Conservateur</option>
                  <option value="moderate">⚖️ Modéré</option>
                  <option value="aggressive">🚀 Agressif</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fréquence de rééquilibrage
                </label>
                <select
                  value={config.rebalance_frequency_hours}
                  onChange={(e) => updateConfig('rebalance_frequency_hours', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value={6}>Toutes les 6h</option>
                  <option value={12}>Toutes les 12h</option>
                  <option value={24}>Quotidien</option>
                  <option value={48}>Tous les 2 jours</option>
                </select>
              </div>

              {/* Secteurs autorisés */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secteurs d'ETF autorisés (optionnel)
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {availableSectors.map((sector) => (
                    <label key={sector} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={config.allowed_etf_sectors.includes(sector)}
                        onChange={() => toggleSector(sector)}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{sector}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.auto_stop_loss}
                    onChange={(e) => updateConfig('auto_stop_loss', e.target.checked)}
                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Stop Loss auto</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.auto_take_profit}
                    onChange={(e) => updateConfig('auto_take_profit', e.target.checked)}
                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Take Profit auto</span>
                </label>
              </div>

              <button
                onClick={startSimulation}
                disabled={isCreating}
                className={`w-full flex items-center justify-center space-x-2 py-3 rounded-lg font-medium ${
                  isCreating
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isCreating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Création...</span>
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-5 w-5" />
                    <span>Démarrer la simulation</span>
                  </>
                )}
              </button>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
                    <span className="text-red-800 text-sm">{error}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Simulations actives */}
        <div className="xl:col-span-2">
          <div className="space-y-6">
            {/* En-tête avec leaderboard */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Mes Simulations ({activeSimulations.length})
                </h3>
                
                {activeSimulations.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">
                    Aucune simulation active.<br />
                    Créez votre première simulation pour commencer !
                  </p>
                ) : (
                  <div className="space-y-3">
                    {activeSimulations.slice(0, 3).map((sim) => (
                      <div key={sim.id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{sim.config.name}</h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(sim.status)}`}>
                            {getStatusLabel(sim.status)}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Valeur:</span>
                            <div className="font-medium">{sim.current_value.toFixed(2)}€</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Rendement:</span>
                            <div className={`font-medium ${sim.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {sim.total_return_pct >= 0 ? '+' : ''}{sim.total_return_pct.toFixed(2)}%
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Reste:</span>
                            <div className="font-medium">{sim.days_remaining}j</div>
                          </div>
                        </div>
                        
                        <div className="flex space-x-2 mt-3">
                          {sim.status === 'running' ? (
                            <button
                              onClick={() => pauseSimulation(sim.id)}
                              className="flex-1 bg-yellow-100 text-yellow-800 py-1 px-2 rounded text-xs hover:bg-yellow-200"
                            >
                              <PauseIcon className="h-3 w-3 inline mr-1" />
                              Pause
                            </button>
                          ) : sim.status === 'paused' ? (
                            <button
                              onClick={() => resumeSimulation(sim.id)}
                              className="flex-1 bg-green-100 text-green-800 py-1 px-2 rounded text-xs hover:bg-green-200"
                            >
                              <PlayIcon className="h-3 w-3 inline mr-1" />
                              Reprendre
                            </button>
                          ) : null}
                          
                          <button
                            onClick={() => stopSimulation(sim.id)}
                            className="flex-1 bg-red-100 text-red-800 py-1 px-2 rounded text-xs hover:bg-red-200"
                          >
                            <StopIcon className="h-3 w-3 inline mr-1" />
                            Arrêter
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Leaderboard */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <TrophyIcon className="h-5 w-5 mr-2 text-yellow-500" />
                  Top Performers (7j)
                </h3>
                
                {leaderboard.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">
                    Aucun classement disponible
                  </p>
                ) : (
                  <div className="space-y-3">
                    {leaderboard.map((entry, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">{index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}</span>
                          <div>
                            <div className="font-medium text-sm">{entry.name}</div>
                            <div className="text-xs text-gray-500">{entry.risk_level}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`font-medium text-sm ${entry.return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {entry.return_pct >= 0 ? '+' : ''}{entry.return_pct.toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">{entry.duration_days}j</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Détails simulation sélectionnée */}
            {selectedSimulation && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Détails: {selectedSimulation.config.name}
                </h3>
                
                {/* TODO: Ajouter graphiques et détails des trades */}
                <div className="text-gray-500 text-center py-8">
                  Graphiques et analyse détaillée à venir...
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingSimulation;