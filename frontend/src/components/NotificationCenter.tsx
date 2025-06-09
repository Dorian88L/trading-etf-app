import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  BellAlertIcon,
  Cog6ToothIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import useNotifications from '../hooks/useNotifications';

interface NotificationSetting {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  category: 'signals' | 'market' | 'portfolio' | 'system';
}

interface NotificationCenterProps {
  onClose?: () => void;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ onClose }) => {
  const {
    permission,
    supported,
    subscription,
    isRegistering,
    requestPermission,
    registerPushNotifications,
    unregisterPushNotifications,
    testNotification
  } = useNotifications();

  const [activeTab, setActiveTab] = useState<'status' | 'settings' | 'test'>('status');
  const [preferences, setPreferences] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/notifications/preferences', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
      }
    } catch (error) {
      console.error('Erreur chargement préférences:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    if (!preferences) return;

    try {
      const response = await fetch('/api/v1/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(preferences)
      });

      if (response.ok) {
        setMessage('Préférences sauvegardées');
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (error) {
      setMessage('Erreur de sauvegarde');
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const [settings, setSettings] = useState<NotificationSetting[]>([
    {
      id: 'high-confidence-signals',
      name: 'Signaux haute confiance',
      description: 'Notifications pour les signaux avec confiance > 80%',
      enabled: true,
      category: 'signals'
    },
    {
      id: 'buy-sell-signals',
      name: 'Signaux d\'achat/vente',
      description: 'Toutes les recommandations d\'achat et de vente',
      enabled: true,
      category: 'signals'
    },
    {
      id: 'breakout-signals',
      name: 'Signaux de cassure',
      description: 'Alertes pour les cassures de résistance/support',
      enabled: false,
      category: 'signals'
    },
    {
      id: 'market-volatility',
      name: 'Volatilité du marché',
      description: 'Alertes en cas de forte volatilité',
      enabled: true,
      category: 'market'
    },
    {
      id: 'sector-rotation',
      name: 'Rotation sectorielle',
      description: 'Changements importants dans les secteurs',
      enabled: false,
      category: 'market'
    },
    {
      id: 'portfolio-risk',
      name: 'Risque du portefeuille',
      description: 'Alertes quand le risque dépasse les seuils',
      enabled: true,
      category: 'portfolio'
    },
    {
      id: 'position-targets',
      name: 'Objectifs de position',
      description: 'Notifications d\'objectifs de prix atteints',
      enabled: true,
      category: 'portfolio'
    },
    {
      id: 'stop-loss-alerts',
      name: 'Alertes stop-loss',
      description: 'Avertissements avant déclenchement stop-loss',
      enabled: true,
      category: 'portfolio'
    },
    {
      id: 'system-updates',
      name: 'Mises à jour système',
      description: 'Notifications des mises à jour de l\'application',
      enabled: false,
      category: 'system'
    },
    {
      id: 'maintenance-alerts',
      name: 'Maintenance',
      description: 'Alertes de maintenance programmée',
      enabled: true,
      category: 'system'
    }
  ]);

  const [testResult, setTestResult] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  // Sauvegarder les paramètres dans localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('notification-settings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (error) {
        console.error('Error loading notification settings:', error);
      }
    }
  }, []);

  const saveSettings = (newSettings: NotificationSetting[]) => {
    setSettings(newSettings);
    localStorage.setItem('notification-settings', JSON.stringify(newSettings));
  };

  const toggleSetting = (id: string) => {
    const newSettings = settings.map(setting =>
      setting.id === id ? { ...setting, enabled: !setting.enabled } : setting
    );
    saveSettings(newSettings);
  };

  const handleEnableNotifications = async () => {
    try {
      await registerPushNotifications();
      setTestResult({
        type: 'success',
        message: 'Notifications activées avec succès!'
      });
    } catch (error) {
      setTestResult({
        type: 'error',
        message: 'Erreur lors de l\'activation des notifications'
      });
    }
  };

  const handleDisableNotifications = async () => {
    try {
      await unregisterPushNotifications();
      setTestResult({
        type: 'info',
        message: 'Notifications désactivées'
      });
    } catch (error) {
      setTestResult({
        type: 'error',
        message: 'Erreur lors de la désactivation'
      });
    }
  };

  const handleTestNotification = async () => {
    try {
      await testNotification();
      setTestResult({
        type: 'success',
        message: 'Notification de test envoyée!'
      });
    } catch (error) {
      setTestResult({
        type: 'error',
        message: 'Erreur lors du test de notification'
      });
    }
  };

  const getPermissionStatus = () => {
    if (!supported) {
      return {
        icon: <XCircleIcon className="h-6 w-6 text-red-500" />,
        text: 'Non supporté',
        color: 'text-red-600 bg-red-50 border-red-200'
      };
    }

    switch (permission as string) {
      case 'granted':
        return {
          icon: <CheckCircleIcon className="h-6 w-6 text-green-500" />,
          text: 'Autorisées',
          color: 'text-green-600 bg-green-50 border-green-200'
        };
      case 'denied':
        return {
          icon: <XCircleIcon className="h-6 w-6 text-red-500" />,
          text: 'Refusées',
          color: 'text-red-600 bg-red-50 border-red-200'
        };
      default:
        return {
          icon: <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />,
          text: 'En attente',
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200'
        };
    }
  };

  const permissionStatus = getPermissionStatus();

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'signals': return '📈';
      case 'market': return '🌍';
      case 'portfolio': return '💼';
      case 'system': return '⚙️';
      default: return '🔔';
    }
  };

  const categoryGroups = settings.reduce((groups, setting) => {
    if (!groups[setting.category]) {
      groups[setting.category] = [];
    }
    groups[setting.category].push(setting);
    return groups;
  }, {} as Record<string, NotificationSetting[]>);

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 w-full max-w-2xl">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <BellAlertIcon className="h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Centre de Notifications</h2>
        </div>
        
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <XCircleIcon className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {[
          { id: 'status', label: 'État' },
          { id: 'settings', label: 'Paramètres' },
          { id: 'test', label: 'Test' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-3 text-sm font-medium border-b-2 ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 max-h-96 overflow-y-auto">
        {activeTab === 'status' && (
          <div className="space-y-4">
            {/* Permission Status */}
            <div className={`border rounded-lg p-4 ${permissionStatus.color}`}>
              <div className="flex items-center space-x-3">
                {permissionStatus.icon}
                <div>
                  <h3 className="font-medium">État des notifications</h3>
                  <p className="text-sm">{permissionStatus.text}</p>
                </div>
              </div>
            </div>

            {/* Push Subscription Status */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-2">Notifications Push</h3>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  {subscription ? 'Abonné aux notifications push' : 'Non abonné'}
                </span>
                <div className={`w-3 h-3 rounded-full ${subscription ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              {(permission as string) !== 'granted' && (
                <button
                  onClick={requestPermission}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Autoriser les notifications
                </button>
              )}
              
              {(permission as string) === 'granted' && !subscription && (
                <button
                  onClick={handleEnableNotifications}
                  disabled={isRegistering}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {isRegistering ? 'Activation...' : 'Activer les notifications push'}
                </button>
              )}
              
              {subscription && (
                <button
                  onClick={handleDisableNotifications}
                  className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Désactiver les notifications push
                </button>
              )}
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {settings.filter(s => s.enabled).length}
                </div>
                <div className="text-sm text-blue-600">Activées</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">
                  {settings.filter(s => !s.enabled).length}
                </div>
                <div className="text-sm text-gray-600">Désactivées</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            {Object.entries(categoryGroups).map(([category, categorySettings]) => (
              <div key={category}>
                <h3 className="flex items-center space-x-2 text-lg font-medium text-gray-900 mb-3">
                  <span>{getCategoryIcon(category)}</span>
                  <span className="capitalize">
                    {category === 'signals' && 'Signaux'}
                    {category === 'market' && 'Marché'}
                    {category === 'portfolio' && 'Portefeuille'}
                    {category === 'system' && 'Système'}
                  </span>
                </h3>
                
                <div className="space-y-3">
                  {categorySettings.map((setting) => (
                    <div key={setting.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{setting.name}</div>
                        <div className="text-sm text-gray-500">{setting.description}</div>
                      </div>
                      
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={setting.enabled}
                          onChange={() => toggleSetting(setting.id)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'test' && (
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Test des Notifications</h3>
              <p className="text-sm text-gray-600 mb-4">
                Testez que les notifications fonctionnent correctement
              </p>
              
              <button
                onClick={handleTestNotification}
                disabled={(permission as string) !== 'granted'}
                className="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Envoyer une notification test
              </button>
            </div>

            {testResult && (
              <div className={`border rounded-lg p-4 ${
                testResult.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' :
                testResult.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' :
                'bg-blue-50 border-blue-200 text-blue-700'
              }`}>
                <div className="flex items-center space-x-2">
                  {testResult.type === 'success' && <CheckCircleIcon className="h-5 w-5" />}
                  {testResult.type === 'error' && <XCircleIcon className="h-5 w-5" />}
                  {testResult.type === 'info' && <InformationCircleIcon className="h-5 w-5" />}
                  <span className="text-sm font-medium">{testResult.message}</span>
                </div>
              </div>
            )}

            {/* Diagnostic Info */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Informations de diagnostic</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Navigateur supporté:</span>
                  <span>{supported ? 'Oui' : 'Non'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Permission:</span>
                  <span>{permission as string}</span>
                </div>
                <div className="flex justify-between">
                  <span>Service Worker:</span>
                  <span>{'serviceWorker' in navigator ? 'Disponible' : 'Non disponible'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Push Manager:</span>
                  <span>{'PushManager' in window ? 'Disponible' : 'Non disponible'}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;