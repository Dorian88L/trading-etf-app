import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../../services/api';

interface PriceAlert {
  id: string;
  etf_symbol: string;
  target_price: number;
  current_price?: number;
  alert_type: 'above' | 'below';
  message?: string;
  is_active: boolean;
  is_triggered: boolean;
  created_at: string;
  triggered_at?: string;
}

interface PriceAlertsListProps {
  onEditAlert?: (alert: PriceAlert) => void;
  refreshTrigger?: number;
}

const PriceAlertsList: React.FC<PriceAlertsListProps> = ({ onEditAlert, refreshTrigger }) => {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPriceAlerts();
  }, [refreshTrigger]);

  const fetchPriceAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertsAPI.getPriceAlerts();
      setAlerts(response || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des alertes de prix');
    } finally {
      setLoading(false);
    }
  };

  const toggleAlertStatus = async (alertId: string, isActive: boolean) => {
    try {
      await alertsAPI.updatePriceAlert(alertId, { is_active: isActive });
      setAlerts(alerts.map(alert => 
        alert.id === alertId ? { ...alert, is_active: isActive } : alert
      ));
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour:', err);
    }
  };

  const deleteAlert = async (alertId: string) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette alerte ?')) {
      return;
    }

    try {
      await alertsAPI.deletePriceAlert(alertId);
      setAlerts(alerts.filter(alert => alert.id !== alertId));
    } catch (err: any) {
      console.error('Erreur lors de la suppression:', err);
    }
  };

  const getStatusColor = (alert: PriceAlert) => {
    if (alert.is_triggered) return 'bg-green-100 text-green-800';
    if (!alert.is_active) return 'bg-gray-100 text-gray-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getStatusText = (alert: PriceAlert) => {
    if (alert.is_triggered) return '✅ Déclenchée';
    if (!alert.is_active) return '⏸️ Inactive';
    return '🔄 Active';
  };

  const getProgressPercentage = (alert: PriceAlert) => {
    if (!alert.current_price) return 0;
    
    const currentPrice = alert.current_price;
    const targetPrice = alert.target_price;
    
    if (alert.alert_type === 'above') {
      return Math.min(100, (currentPrice / targetPrice) * 100);
    } else {
      return Math.min(100, ((targetPrice - currentPrice) / targetPrice) * 100 + 50);
    }
  };

  const getRemainingDistance = (alert: PriceAlert) => {
    if (!alert.current_price) return null;
    
    const distance = Math.abs(alert.current_price - alert.target_price);
    const percentage = (distance / alert.current_price) * 100;
    
    return {
      absolute: distance.toFixed(2),
      percentage: percentage.toFixed(1)
    };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">{error}</p>
        <button 
          onClick={fetchPriceAlerts}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">💰</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune alerte de prix</h3>
        <p className="text-gray-500">Créez votre première alerte pour être notifié des mouvements de prix importants.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {alerts.map((alert) => {
        const distance = getRemainingDistance(alert);
        const progress = getProgressPercentage(alert);
        
        return (
          <div 
            key={alert.id} 
            className={`bg-white rounded-lg shadow-sm border overflow-hidden ${
              alert.is_triggered ? 'border-green-300' : alert.is_active ? 'border-blue-300' : 'border-gray-300'
            }`}
          >
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">{alert.etf_symbol}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert)}`}>
                      {getStatusText(alert)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {alert.alert_type === 'above' ? '📈' : '📉'} 
                      {alert.alert_type === 'above' ? ' Au-dessus' : ' En-dessous'} de {alert.target_price.toFixed(2)} €
                    </span>
                  </div>

                  {alert.current_price && (
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600">Prix actuel: {alert.current_price.toFixed(2)} €</span>
                        {distance && (
                          <span className="text-gray-500">
                            Reste: {distance.absolute} € ({distance.percentage}%)
                          </span>
                        )}
                      </div>
                      
                      {/* Barre de progression */}
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            alert.is_triggered ? 'bg-green-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, progress))}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {alert.message && (
                    <p className="text-sm text-gray-600 mb-2">💭 {alert.message}</p>
                  )}

                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>📅 Créée le {new Date(alert.created_at).toLocaleDateString('fr-FR')}</span>
                    {alert.triggered_at && (
                      <span>🎯 Déclenchée le {new Date(alert.triggered_at).toLocaleDateString('fr-FR')}</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  {/* Toggle actif/inactif */}
                  <button
                    onClick={() => toggleAlertStatus(alert.id, !alert.is_active)}
                    className={`p-2 rounded transition-colors ${
                      alert.is_active 
                        ? 'text-blue-600 hover:bg-blue-50' 
                        : 'text-gray-400 hover:bg-gray-50'
                    }`}
                    title={alert.is_active ? 'Désactiver' : 'Activer'}
                    disabled={alert.is_triggered}
                  >
                    {alert.is_active ? '⏸️' : '▶️'}
                  </button>

                  {/* Modifier */}
                  {onEditAlert && (
                    <button
                      onClick={() => onEditAlert(alert)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Modifier"
                    >
                      ✏️
                    </button>
                  )}

                  {/* Supprimer */}
                  <button
                    onClick={() => deleteAlert(alert.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Supprimer"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PriceAlertsList;