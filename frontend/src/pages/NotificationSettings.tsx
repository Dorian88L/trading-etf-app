import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
import useNotifications from '../hooks/useNotifications';
import {
  BellIcon,
  CogIcon,
  ClockIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { BellIcon as BellIconSolid } from '@heroicons/react/24/solid';
import { getApiUrl } from '../config/api';

interface NotificationPreferences {
  signal_notifications: boolean;
  price_alert_notifications: boolean;
  market_alert_notifications: boolean;
  portfolio_notifications: boolean;
  system_notifications: boolean;
  min_signal_confidence: number;
  min_price_change_percent: number;
  min_volume_spike_percent: number;
  quiet_hours_start: string;
  quiet_hours_end: string;
  weekend_notifications: boolean;
  max_notifications_per_hour: number;
  max_notifications_per_day: number;
}

const NotificationSettings: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const {
    permission,
    supported,
    subscription,
    isRegistering,
    registerPushNotifications,
    unregisterPushNotifications,
    testNotification
  } = useNotifications();

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    signal_notifications: true,
    price_alert_notifications: true,
    market_alert_notifications: true,
    portfolio_notifications: true,
    system_notifications: false,
    min_signal_confidence: 60,
    min_price_change_percent: 3,
    min_volume_spike_percent: 50,
    quiet_hours_start: "22:00",
    quiet_hours_end: "08:00",
    weekend_notifications: false,
    max_notifications_per_hour: 5,
    max_notifications_per_day: 20
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    if (user) {
      loadPreferences();
      loadStats();
    }
  }, [user]);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await fetch(getApiUrl('/api/v1/notifications/preferences'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des préférences:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(getApiUrl('/api/v1/notifications/stats'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setStats(result.data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      const response = await fetch(getApiUrl('/api/v1/notifications/preferences'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(preferences)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Préférences sauvegardées avec succès' });
        setTimeout(() => setMessage(null), 3000);
      } else {
        throw new Error('Erreur de sauvegarde');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erreur lors de la sauvegarde' });
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleTogglePushNotifications = async () => {
    try {
      if (subscription) {
        await unregisterPushNotifications();
        setMessage({ type: 'success', text: 'Notifications push désactivées' });
      } else {
        await registerPushNotifications();
        setMessage({ type: 'success', text: 'Notifications push activées' });
      }
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Erreur lors de la configuration des notifications push' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleTestNotification = async () => {
    try {
      await testNotification();
      setMessage({ type: 'success', text: 'Notification de test envoyée' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Erreur lors de l\'envoi du test' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const getPermissionStatus = () => {
    switch (permission) {
      case 'granted':
        return { color: 'text-green-600', icon: CheckCircleIcon, text: 'Autorisées' };
      case 'denied':
        return { color: 'text-red-600', icon: XCircleIcon, text: 'Refusées' };
      case 'default':
        return { color: 'text-yellow-600', icon: ExclamationTriangleIcon, text: 'En attente' };
      default:
        return { color: 'text-gray-600', icon: XCircleIcon, text: 'Non supportées' };
    }
  };

  const permissionStatus = getPermissionStatus();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <BellIconSolid className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Configuration des Notifications</h1>
              <p className="text-gray-600">Gérez vos alertes et notifications de trading</p>
            </div>
          </div>

          {message && (
            <div className={`px-4 py-2 rounded-lg ${
              message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {message.text}
            </div>
          )}
        </div>

        {/* Statut des notifications push */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <permissionStatus.icon className={`h-6 w-6 ${permissionStatus.color}`} />
              <div>
                <h3 className="font-medium text-gray-900">Notifications Push</h3>
                <p className="text-sm text-gray-600">
                  Statut: {permissionStatus.text}
                  {subscription && ' • Abonné'}
                </p>
              </div>
            </div>

            <div className="flex space-x-3">
              {permission === 'granted' && (
                <button
                  onClick={handleTestNotification}
                  className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg"
                >
                  Tester
                </button>
              )}
              
              {supported && (
                <button
                  onClick={handleTogglePushNotifications}
                  disabled={isRegistering}
                  className={`px-4 py-2 text-sm font-medium rounded-lg ${
                    subscription
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  } disabled:opacity-50`}
                >
                  {isRegistering 
                    ? 'Configuration...' 
                    : subscription 
                      ? 'Désactiver' 
                      : 'Activer'
                  }
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Types de notifications */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <CogIcon className="h-5 w-5 mr-2" />
          Types de Notifications
        </h2>

        <div className="space-y-4">
          {[
            { key: 'signal_notifications', label: 'Signaux de Trading', icon: ChartBarIcon, desc: 'Alertes BUY/SELL/HOLD/WAIT' },
            { key: 'price_alert_notifications', label: 'Alertes de Prix', icon: BellIcon, desc: 'Objectifs de prix atteints' },
            { key: 'market_alert_notifications', label: 'Alertes de Marché', icon: ExclamationTriangleIcon, desc: 'Mouvements significatifs' },
            { key: 'portfolio_notifications', label: 'Portfolio', icon: ShieldCheckIcon, desc: 'Changements dans vos positions' },
            { key: 'system_notifications', label: 'Système', icon: CogIcon, desc: 'Maintenance et mises à jour' }
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <item.icon className="h-6 w-6 text-gray-500" />
                <div>
                  <h3 className="font-medium text-gray-900">{item.label}</h3>
                  <p className="text-sm text-gray-600">{item.desc}</p>
                </div>
              </div>
              
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences[item.key as keyof NotificationPreferences] as boolean}
                  onChange={(e) => setPreferences(prev => ({
                    ...prev,
                    [item.key]: e.target.checked
                  }))}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Seuils et paramètres */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Seuils et Paramètres</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confiance minimum pour signaux: {preferences.min_signal_confidence}%
            </label>
            <input
              type="range"
              min="30"
              max="90"
              value={preferences.min_signal_confidence}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                min_signal_confidence: parseInt(e.target.value)
              }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>30%</span>
              <span>90%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Variation de prix minimum: {preferences.min_price_change_percent}%
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={preferences.min_price_change_percent}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                min_price_change_percent: parseInt(e.target.value)
              }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1%</span>
              <span>10%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pic de volume minimum: {preferences.min_volume_spike_percent}%
            </label>
            <input
              type="range"
              min="20"
              max="200"
              step="10"
              value={preferences.min_volume_spike_percent}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                min_volume_spike_percent: parseInt(e.target.value)
              }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>20%</span>
              <span>200%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max notifications/heure: {preferences.max_notifications_per_hour}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={preferences.max_notifications_per_hour}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                max_notifications_per_hour: parseInt(e.target.value)
              }))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1</span>
              <span>20</span>
            </div>
          </div>
        </div>
      </div>

      {/* Heures de silence */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <ClockIcon className="h-5 w-5 mr-2" />
          Heures de Silence
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Début</label>
            <input
              type="time"
              value={preferences.quiet_hours_start}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                quiet_hours_start: e.target.value
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Fin</label>
            <input
              type="time"
              value={preferences.quiet_hours_end}
              onChange={(e) => setPreferences(prev => ({
                ...prev,
                quiet_hours_end: e.target.value
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.weekend_notifications}
                onChange={(e) => setPreferences(prev => ({
                  ...prev,
                  weekend_notifications: e.target.checked
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Notifications le weekend</span>
            </label>
          </div>
        </div>
      </div>

      {/* Statistiques */}
      {stats && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistiques</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_sent}</div>
              <div className="text-sm text-gray-600">Notifications envoyées</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.total_clicked}</div>
              <div className="text-sm text-gray-600">Notifications cliquées</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.click_rate.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Taux de clic</div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {Object.keys(stats.type_distribution).length}
              </div>
              <div className="text-sm text-gray-600">Types actifs</div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={() => loadPreferences()}
          className="px-6 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium"
        >
          Annuler
        </button>
        
        <button
          onClick={savePreferences}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
        >
          {saving ? 'Sauvegarde...' : 'Sauvegarder'}
        </button>
      </div>
    </div>
  );
};

export default NotificationSettings;