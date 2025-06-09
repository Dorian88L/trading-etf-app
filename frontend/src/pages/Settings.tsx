import React, { useState, useEffect } from 'react';
import { UserPreferences } from '../types';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { userAPI } from '../services/api';
import { logoutUser } from '../store/slices/authSlice';
import useAdvancedNotifications from '../hooks/useAdvancedNotifications';

const Settings: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  
  // Hook pour les notifications
  const {
    isSupported: notificationSupported,
    permission: notificationPermission,
    pendingCount,
    requestPermission,
    sendTestNotification
  } = useAdvancedNotifications();

  useEffect(() => {
    fetchPreferences();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      setError('');
      
      if (isAuthenticated) {
        // Try to fetch from API first
        try {
          const userPrefs = await userAPI.getPreferences();
          setPreferences(userPrefs);
        } catch (apiError) {
          console.log('Could not fetch preferences from API, using local storage');
          
          // Fallback to localStorage
          const savedPreferences = localStorage.getItem('userPreferences');
          
          if (savedPreferences) {
            setPreferences(JSON.parse(savedPreferences));
          } else {
            const defaultPrefs = getDefaultPreferences();
            setPreferences(defaultPrefs);
            localStorage.setItem('userPreferences', JSON.stringify(defaultPrefs));
          }
        }
      } else {
        // Use localStorage for non-authenticated users
        const savedPreferences = localStorage.getItem('userPreferences');
        
        if (savedPreferences) {
          setPreferences(JSON.parse(savedPreferences));
        } else {
          const defaultPrefs = getDefaultPreferences();
          setPreferences(defaultPrefs);
          localStorage.setItem('userPreferences', JSON.stringify(defaultPrefs));
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des préférences:', error);
      setError('Erreur lors du chargement des préférences');
      setPreferences(getDefaultPreferences());
    } finally {
      setLoading(false);
    }
  };

  const getDefaultPreferences = (): UserPreferences => ({
    user_id: '',
    risk_tolerance: 50,
    min_signal_confidence: 60,
    notification_settings: {
      email: true,
      push: true,
      sms: false
    },
    trading_preferences: {
      max_position_size: 0.1,
      stop_loss_pct: 0.05
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  });

  const savePreferences = async () => {
    if (!preferences) return;

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      if (isAuthenticated) {
        // Try to save to API first
        try {
          await userAPI.updatePreferences(preferences);
          setSuccess('Préférences sauvegardées avec succès sur le serveur');
        } catch (apiError) {
          console.log('Could not save to API, saving locally');
          // Fallback to localStorage
          localStorage.setItem('userPreferences', JSON.stringify(preferences));
          setSuccess('Préférences sauvegardées localement');
        }
      } else {
        // Save to localStorage for non-authenticated users
        localStorage.setItem('userPreferences', JSON.stringify(preferences));
        setSuccess('Préférences sauvegardées localement');
      }
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError('Erreur lors de la sauvegarde des préférences: ' + (err.message || 'Erreur inconnue'));
    } finally {
      setSaving(false);
    }
  };

  const updatePreferences = (updates: Partial<UserPreferences>) => {
    if (preferences) {
      setPreferences({ ...preferences, ...updates });
    }
  };

  const updateNotificationSettings = (key: keyof UserPreferences['notification_settings'], value: boolean) => {
    if (preferences) {
      setPreferences({
        ...preferences,
        notification_settings: {
          ...preferences.notification_settings,
          [key]: value
        }
      });
    }
  };

  const updateTradingPreferences = (key: keyof UserPreferences['trading_preferences'], value: number) => {
    if (preferences) {
      setPreferences({
        ...preferences,
        trading_preferences: {
          ...preferences.trading_preferences,
          [key]: value
        }
      });
    }
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

  if (!preferences) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">Impossible de charger les préférences</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Paramètres</h1>
        <p className="text-gray-600">Configurez vos préférences de trading et notifications</p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <p className="text-green-600">{success}</p>
        </div>
      )}

      <div className="space-y-8">
        {/* User Profile Section */}
        {isAuthenticated && user && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">👤 Profil Utilisateur</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                <p className="text-gray-900 font-medium">{user.full_name || 'Nom non défini'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p className="text-gray-900">{user.email}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Statut du compte</label>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {user.is_active ? '✅ Actif' : '❌ Inactif'}
                </span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Membre depuis</label>
                <p className="text-gray-900">{user.created_at ? new Date(user.created_at).toLocaleDateString('fr-FR') : 'N/A'}</p>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => dispatch(logoutUser())}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                🚪 Se déconnecter
              </button>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Préférences de Trading</h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tolérance au risque: {preferences.risk_tolerance}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={preferences.risk_tolerance}
                onChange={(e) => updatePreferences({ risk_tolerance: Number(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Conservateur</span>
                <span>Modéré</span>
                <span>Agressif</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confiance minimum des signaux: {preferences.min_signal_confidence}%
              </label>
              <input
                type="range"
                min="50"
                max="95"
                value={preferences.min_signal_confidence}
                onChange={(e) => updatePreferences({ min_signal_confidence: Number(e.target.value) })}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Seuls les signaux avec une confiance supérieure à ce seuil seront affichés
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Taille maximum d'une position: {(preferences.trading_preferences.max_position_size * 100).toFixed(1)}%
              </label>
              <input
                type="range"
                min="0.05"
                max="0.5"
                step="0.01"
                value={preferences.trading_preferences.max_position_size}
                onChange={(e) => updateTradingPreferences('max_position_size', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Pourcentage maximum du portfolio pour une seule position
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stop Loss par défaut: {(preferences.trading_preferences.stop_loss_pct * 100).toFixed(1)}%
              </label>
              <input
                type="range"
                min="0.02"
                max="0.15"
                step="0.01"
                value={preferences.trading_preferences.stop_loss_pct}
                onChange={(e) => updateTradingPreferences('stop_loss_pct', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Seuil de perte par défaut pour les nouvelles positions
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🔔 Notifications</h2>
          
          {/* Statut des notifications push */}
          <div className="mb-6 p-4 rounded-lg border border-gray-200 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Statut des Notifications Push</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Support navigateur:</span>
                <span className={`text-sm font-medium ${notificationSupported ? 'text-green-600' : 'text-red-600'}`}>
                  {notificationSupported ? '✅ Supporté' : '❌ Non supporté'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Permission:</span>
                <span className={`text-sm font-medium ${
                  notificationPermission === 'granted' ? 'text-green-600' : 
                  notificationPermission === 'denied' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {notificationPermission === 'granted' ? '✅ Accordée' : 
                   notificationPermission === 'denied' ? '❌ Refusée' : '⏳ En attente'}
                </span>
              </div>
              {pendingCount > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Notifications en attente:</span>
                  <span className="text-sm font-medium text-blue-600">{pendingCount}</span>
                </div>
              )}
            </div>
            
            <div className="mt-4 flex space-x-3">
              {notificationPermission !== 'granted' && (
                <button
                  onClick={requestPermission}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                >
                  Autoriser les notifications
                </button>
              )}
              <button
                onClick={sendTestNotification}
                disabled={!notificationSupported}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                🧪 Tester une notification
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">📧 Notifications par email</label>
                <p className="text-xs text-gray-500">Recevoir les alertes et signaux par email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.notification_settings.email}
                  onChange={(e) => updateNotificationSettings('email', e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">🌐 Notifications push (navigateur)</label>
                <p className="text-xs text-gray-500">Recevoir les notifications dans le navigateur en temps réel</p>
                {!notificationSupported && (
                  <p className="text-xs text-red-500 mt-1">❌ Non supporté par votre navigateur</p>
                )}
                {notificationSupported && notificationPermission === 'denied' && (
                  <p className="text-xs text-red-500 mt-1">❌ Permission refusée - activez dans les paramètres du navigateur</p>
                )}
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.notification_settings.push && notificationSupported}
                  onChange={(e) => updateNotificationSettings('push', e.target.checked)}
                  disabled={!notificationSupported}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">📱 Notifications SMS</label>
                <p className="text-xs text-gray-500">Recevoir les alertes urgentes par SMS</p>
                <p className="text-xs text-orange-500 mt-1">🚧 Fonctionnalité en développement</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.notification_settings.sms}
                  onChange={(e) => updateNotificationSettings('sms', e.target.checked)}
                  disabled={true}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
              </label>
            </div>
          </div>
          
          {/* Types d'alertes */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Types d'Alertes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-green-600 mr-2">📈</span>
                  <span>Signaux de trading</span>
                </div>
                <div className="flex items-center">
                  <span className="text-blue-600 mr-2">💰</span>
                  <span>Alertes de prix</span>
                </div>
                <div className="flex items-center">
                  <span className="text-purple-600 mr-2">📊</span>
                  <span>Mises à jour portfolio</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-orange-600 mr-2">🌍</span>
                  <span>Alertes marché</span>
                </div>
                <div className="flex items-center">
                  <span className="text-red-600 mr-2">⚠️</span>
                  <span>Alertes de risque</span>
                </div>
                <div className="flex items-center">
                  <span className="text-gray-600 mr-2">🔔</span>
                  <span>Nouvelles importantes</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Sécurité</h2>
          
          <div className="space-y-4">
            <button className="w-full md:w-auto px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700">
              Changer le mot de passe
            </button>
            
            <button className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Activer l'authentification 2FA
            </button>
            
            <button className="w-full md:w-auto px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
              Télécharger mes données
            </button>
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            onClick={fetchPreferences}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Annuler
          </button>
          <button
            onClick={savePreferences}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;