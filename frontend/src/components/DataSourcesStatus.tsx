import React, { useState, useEffect } from 'react';
import { marketAPI } from '../services/api';

interface SourceStatus {
  api_key_available: boolean;
  rate_limit: number | string;
  calls_used: number | string;
  calls_remaining: number | string;
  window_seconds: number;
  status: 'available' | 'limited';
  last_reset: string;
  notes?: string;
}

interface DataSourcesStatusProps {
  isOpen: boolean;
  onClose: () => void;
}

const DataSourcesStatus: React.FC<DataSourcesStatusProps> = ({ isOpen, onClose }) => {
  const [sourcesData, setSourcesData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const fetchSourcesStatus = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await marketAPI.getDataSourcesStatus();
      setSourcesData(response);
    } catch (err: any) {
      setError('Erreur lors de la récupération du statut des sources');
      console.error('Erreur sources status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSourcesStatus();
    }
  }, [isOpen]);

  const refreshCache = async () => {
    try {
      await marketAPI.refreshETFCache();
      // Rafraîchir aussi le statut
      await fetchSourcesStatus();
    } catch (err) {
      console.error('Erreur refresh cache:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available': return '🟢';
      case 'limited': return '🟡';
      default: return '🔴';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-green-600 bg-green-50 border-green-200';
      case 'limited': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            📊 Statut des Sources de Données ETF
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Chargement du statut...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error}</p>
              <button
                onClick={fetchSourcesStatus}
                className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Réessayer
              </button>
            </div>
          ) : sourcesData ? (
            <div className="space-y-6">
              {/* Résumé */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Résumé Global</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-600">Sources disponibles:</span>
                    <div className="font-semibold text-blue-900">
                      {sourcesData.summary.available_sources}/{sourcesData.summary.total_sources}
                    </div>
                  </div>
                  <div>
                    <span className="text-blue-600">Fiabilité:</span>
                    <div className="font-semibold text-blue-900">
                      {Math.round(sourcesData.summary.reliability_score * 100)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-blue-600">Source principale:</span>
                    <div className="font-semibold text-blue-900">Yahoo Finance</div>
                  </div>
                  <div>
                    <span className="text-blue-600">Sources de secours:</span>
                    <div className="font-semibold text-blue-900">
                      {sourcesData.summary.fallback_sources}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sources détaillées */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Sources de Données</h3>
                  <button
                    onClick={refreshCache}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                  >
                    🔄 Rafraîchir Cache
                  </button>
                </div>
                
                <div className="grid gap-4">
                  {Object.entries(sourcesData.sources).map(([sourceKey, source]: [string, any]) => (
                    <div
                      key={sourceKey}
                      className={`border rounded-lg p-4 ${getStatusColor(source.status)}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <span className="text-xl">{getStatusIcon(source.status)}</span>
                          <div>
                            <h4 className="font-medium">
                              {sourceKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            {source.notes && (
                              <p className="text-sm opacity-80">{source.notes}</p>
                            )}
                          </div>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(source.status)}`}>
                          {source.status === 'available' ? 'Disponible' : 'Limité'}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Clé API:</span>
                          <div className={source.api_key_available ? 'text-green-600' : 'text-red-600'}>
                            {source.api_key_available ? '✅ Configurée' : '❌ Manquante'}
                          </div>
                        </div>
                        <div>
                          <span className="font-medium">Limite:</span>
                          <div>{source.rate_limit}/jour</div>
                        </div>
                        <div>
                          <span className="font-medium">Utilisées:</span>
                          <div>{source.calls_used}</div>
                        </div>
                        <div>
                          <span className="font-medium">Restantes:</span>
                          <div className={source.calls_remaining === 0 ? 'text-red-600' : 'text-green-600'}>
                            {source.calls_remaining}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommandations */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-medium text-yellow-900 mb-2">💡 Recommandations</h3>
                <ul className="space-y-1 text-sm text-yellow-800">
                  {sourcesData.recommendations.map((rec: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Métadonnées */}
              {sourcesData.metadata && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">📈 Statistiques de Performance</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Confiance moyenne:</span>
                      <div className="font-semibold">
                        {Math.round(sourcesData.metadata.avg_confidence * 100)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Données réelles:</span>
                      <div className="font-semibold">
                        {sourcesData.metadata.real_data_percentage}%
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Prochaine MAJ:</span>
                      <div className="font-semibold">
                        {Math.round(sourcesData.metadata.next_update_in / 60)} min
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Cache utilisé:</span>
                      <div className={`font-semibold ${sourcesData.metadata.cache_used ? 'text-green-600' : 'text-gray-600'}`}>
                        {sourcesData.metadata.cache_used ? 'Oui' : 'Non'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataSourcesStatus;