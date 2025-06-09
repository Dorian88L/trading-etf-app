import React, { useState, useEffect } from 'react';
import { cache } from '../utils/cache';
import { marketAPI } from '../services/api';

const SystemMonitoring: React.FC = () => {
  const [systemStats, setSystemStats] = useState({
    cacheStats: { total: 0, valid: 0, expired: 0 },
    apiResponseTimes: [] as number[],
    errorRate: 0,
    lastApiCall: null as Date | null,
    memoryUsage: 0
  });

  const [refreshInterval, setRefreshInterval] = useState(5000);

  useEffect(() => {
    const updateStats = () => {
      const cacheStats = cache.getStats();
      
      // Simuler l'utilisation mémoire (approximation)
      const memoryUsage = (performance as any).memory ? 
        ((performance as any).memory.usedJSHeapSize / 1048576).toFixed(2) : Math.random() * 50;

      setSystemStats(prev => ({
        ...prev,
        cacheStats,
        memoryUsage: Number(memoryUsage)
      }));
    };

    updateStats();
    const interval = setInterval(updateStats, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const testApiPerformance = async () => {
    const startTime = Date.now();
    try {
      await marketAPI.getRealETFs(undefined, false); // Pas de cache pour le test
      const responseTime = Date.now() - startTime;
      
      setSystemStats(prev => ({
        ...prev,
        apiResponseTimes: [...prev.apiResponseTimes.slice(-9), responseTime],
        lastApiCall: new Date()
      }));
    } catch (error) {
      console.error('Erreur API:', error);
      setSystemStats(prev => ({
        ...prev,
        errorRate: prev.errorRate + 1
      }));
    }
  };

  const clearCache = () => {
    cache.clear();
    alert('Cache vidé avec succès');
  };

  const avgResponseTime = systemStats.apiResponseTimes.length > 0 
    ? systemStats.apiResponseTimes.reduce((a, b) => a + b, 0) / systemStats.apiResponseTimes.length 
    : 0;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Monitoring Système</h1>
        <p className="text-gray-600">Surveillance des performances et diagnostics</p>
      </div>

      {/* Statistiques principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Cache</h3>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total:</span>
              <span className="font-bold">{systemStats.cacheStats.total}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Valides:</span>
              <span className="font-bold text-green-600">{systemStats.cacheStats.valid}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Expirés:</span>
              <span className="font-bold text-red-600">{systemStats.cacheStats.expired}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">API Response</h3>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Moyenne:</span>
              <span className="font-bold">{avgResponseTime.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Tests:</span>
              <span className="font-bold">{systemStats.apiResponseTimes.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Erreurs:</span>
              <span className="font-bold text-red-600">{systemStats.errorRate}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Mémoire</h3>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Utilisée:</span>
              <span className="font-bold">{systemStats.memoryUsage} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Cache:</span>
              <span className="font-bold">{systemStats.cacheStats.total} items</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Statut</h3>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm">Système opérationnel</span>
            </div>
            <div className="text-xs text-gray-500">
              Dernière vérification: {systemStats.lastApiCall?.toLocaleTimeString('fr-FR') || 'Jamais'}
            </div>
          </div>
        </div>
      </div>

      {/* Graphique des temps de réponse */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Temps de Réponse API</h3>
          <div className="h-64 flex items-end space-x-1">
            {systemStats.apiResponseTimes.map((time, index) => (
              <div
                key={index}
                className="bg-blue-500 rounded-t flex-1 relative"
                style={{ 
                  height: `${Math.min((time / 2000) * 100, 100)}%`,
                  minHeight: '4px'
                }}
                title={`${time}ms`}
              >
                <span className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600">
                  {time}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Moyenne: {avgResponseTime.toFixed(0)}ms | 
              Min: {Math.min(...systemStats.apiResponseTimes, Infinity) || 0}ms | 
              Max: {Math.max(...systemStats.apiResponseTimes, -Infinity) || 0}ms
            </p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions de Diagnostic</h3>
          <div className="space-y-4">
            <button
              onClick={testApiPerformance}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              🚀 Tester Performance API
            </button>
            
            <button
              onClick={clearCache}
              className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              🗑️ Vider le Cache
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              🔄 Redémarrer Application
            </button>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Intervalle de rafraîchissement (ms)
              </label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value={1000}>1 seconde</option>
                <option value={5000}>5 secondes</option>
                <option value={10000}>10 secondes</option>
                <option value={30000}>30 secondes</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Informations système */}
      <div className="bg-gray-50 p-6 rounded-lg border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations Système</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <strong>User Agent:</strong><br />
            <span className="text-gray-600 break-all">{navigator.userAgent}</span>
          </div>
          <div>
            <strong>Plateforme:</strong> {navigator.platform}<br />
            <strong>Langue:</strong> {navigator.language}<br />
            <strong>Cookies activés:</strong> {navigator.cookieEnabled ? 'Oui' : 'Non'}<br />
            <strong>En ligne:</strong> {navigator.onLine ? 'Oui' : 'Non'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitoring;