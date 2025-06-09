import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../services/api';
import { Alert, AlertType } from '../types';
import PriceAlertCreator from '../components/alerts/PriceAlertCreator';
import PriceAlertsList from '../components/alerts/PriceAlertsList';

const Alerts: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [filter, setFilter] = useState<AlertType | 'ALL'>('ALL');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'price'>('general');
  const [showPriceAlertCreator, setShowPriceAlertCreator] = useState(false);
  const [priceAlertsRefresh, setPriceAlertsRefresh] = useState(0);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertsAPI.getAlerts();
      setAlerts(response || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des alertes');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (alertId: string) => {
    try {
      await alertsAPI.markAsRead(alertId);
      setAlerts(alerts.map(alert => 
        alert.id === alertId ? { ...alert, is_read: true } : alert
      ));
    } catch (err: any) {
      console.error('Erreur lors du marquage comme lu:', err);
    }
  };

  const deleteAlert = async (alertId: string) => {
    try {
      await alertsAPI.deleteAlert(alertId);
      setAlerts(alerts.filter(alert => alert.id !== alertId));
    } catch (err: any) {
      console.error('Erreur lors de la suppression:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await alertsAPI.markAllAsRead();
      setAlerts(alerts.map(alert => ({ ...alert, is_read: true })));
    } catch (err: any) {
      console.error('Erreur lors du marquage global:', err);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    const matchesType = filter === 'ALL' || alert.alert_type === filter;
    const matchesRead = !showUnreadOnly || !alert.is_read;
    return matchesType && matchesRead;
  });

  const getAlertTypeColor = (alertType: AlertType) => {
    switch (alertType) {
      case 'SIGNAL':
        return 'bg-blue-100 text-blue-800';
      case 'EVENT':
        return 'bg-green-100 text-green-800';
      case 'RISK':
        return 'bg-red-100 text-red-800';
      case 'NEWS':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertIcon = (alertType: AlertType) => {
    switch (alertType) {
      case 'SIGNAL':
        return '📊';
      case 'EVENT':
        return '📅';
      case 'RISK':
        return '⚠️';
      case 'NEWS':
        return '📰';
      default:
        return '🔔';
    }
  };

  const unreadCount = alerts.filter(alert => !alert.is_read).length;

  const handlePriceAlertCreated = () => {
    setPriceAlertsRefresh(prev => prev + 1);
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
          <button 
            onClick={fetchAlerts}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900">🔔 Alertes</h1>
          <div className="flex items-center gap-3">
            {activeTab === 'general' && unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Marquer tout comme lu ({unreadCount})
              </button>
            )}
            {activeTab === 'price' && (
              <button
                onClick={() => setShowPriceAlertCreator(true)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                💰 Nouvelle alerte de prix
              </button>
            )}
          </div>
        </div>

        {/* Onglets */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('general')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'general'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔔 Alertes générales
              {unreadCount > 0 && (
                <span className="ml-2 bg-red-100 text-red-600 py-0.5 px-2 rounded-full text-xs">
                  {unreadCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('price')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'price'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💰 Alertes de prix
            </button>
          </nav>
        </div>
        
        {/* Filtres pour les alertes générales */}
        {activeTab === 'general' && (
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="md:w-48">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as AlertType | 'ALL')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ALL">Toutes les alertes</option>
                <option value="SIGNAL">Signaux</option>
                <option value="EVENT">Événements</option>
                <option value="RISK">Risques</option>
                <option value="NEWS">Actualités</option>
              </select>
            </div>
            <div className="flex items-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showUnreadOnly}
                  onChange={(e) => setShowUnreadOnly(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Non lues uniquement</span>
              </label>
            </div>
            <button
              onClick={fetchAlerts}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Actualiser
            </button>
          </div>
        )}
      </div>

      {/* Contenu des onglets */}
      {activeTab === 'general' ? (
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">Aucune alerte trouvée avec ces critères.</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`bg-white rounded-lg shadow overflow-hidden border-l-4 ${
                alert.is_read ? 'border-gray-300' : 'border-blue-500'
              }`}
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className="text-2xl">
                      {getAlertIcon(alert.alert_type)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAlertTypeColor(alert.alert_type)}`}>
                          {alert.alert_type}
                        </span>
                        {!alert.is_read && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                            Nouveau
                          </span>
                        )}
                        {alert.etf_isin && (
                          <span className="text-sm text-gray-500">
                            ETF: {alert.etf_isin}
                          </span>
                        )}
                      </div>
                      
                      <h3 className={`text-lg font-medium mb-2 ${
                        alert.is_read ? 'text-gray-700' : 'text-gray-900'
                      }`}>
                        {alert.title}
                      </h3>
                      
                      <p className={`text-sm ${
                        alert.is_read ? 'text-gray-500' : 'text-gray-700'
                      }`}>
                        {alert.message}
                      </p>
                      
                      <div className="mt-3 text-xs text-gray-400">
                        {new Date(alert.created_at).toLocaleString('fr-FR')}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    {!alert.is_read && (
                      <button
                        onClick={() => markAsRead(alert.id)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="Marquer comme lu"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={() => deleteAlert(alert.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Supprimer"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            ))
          )}
          
          {/* Statistiques pour les alertes générales */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Total alertes</h3>
              <div className="text-3xl font-bold text-blue-600">
                {alerts.length}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Non lues</h3>
              <div className="text-3xl font-bold text-red-600">
                {unreadCount}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Signaux</h3>
              <div className="text-3xl font-bold text-green-600">
                {alerts.filter(a => a.alert_type === 'SIGNAL').length}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Risques</h3>
              <div className="text-3xl font-bold text-orange-600">
                {alerts.filter(a => a.alert_type === 'RISK').length}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Onglet Alertes de prix */
        <div>
          <PriceAlertsList 
            refreshTrigger={priceAlertsRefresh}
          />
        </div>
      )}

      {/* Modal de création d'alerte de prix */}
      <PriceAlertCreator
        isOpen={showPriceAlertCreator}
        onClose={() => setShowPriceAlertCreator(false)}
        onAlertCreated={handlePriceAlertCreated}
      />
    </div>
  );
};

export default Alerts;