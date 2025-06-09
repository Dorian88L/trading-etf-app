import React, { useState } from 'react';
import useNotifications from '../../hooks/useNotifications';

interface SimpleNotificationButtonProps {
  className?: string;
}

export const SimpleNotificationButton: React.FC<SimpleNotificationButtonProps> = ({ className = '' }) => {
  const {
    permission,
    supported,
    subscription,
    isRegistering,
    registerPushNotifications,
    unregisterPushNotifications,
    testNotification
  } = useNotifications();

  const [showDropdown, setShowDropdown] = useState(false);

  const handleToggleNotifications = async () => {
    try {
      if (subscription) {
        await unregisterPushNotifications();
      } else {
        await registerPushNotifications();
      }
    } catch (error) {
      console.error('Erreur lors de la gestion des notifications:', error);
      alert('Erreur lors de la configuration des notifications');
    }
  };

  const isNotificationGranted = permission === 'granted';
  const isSubscribed = !!subscription;

  if (!supported) {
    return (
      <div className={`text-gray-400 ${className}`} title="Notifications non supportées">
        <span className="text-xl">🔕</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Bouton principal */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg transition-colors"
        disabled={isRegistering}
        title={isSubscribed ? 'Notifications activées' : 'Notifications désactivées'}
      >
        {isSubscribed ? (
          <span className="text-xl text-blue-600">🔔</span>
        ) : (
          <span className="text-xl text-gray-400">🔕</span>
        )}
        
        {/* Indicateur d'état */}
        {isSubscribed && (
          <span className="absolute -top-1 -right-1 bg-green-500 rounded-full h-3 w-3"></span>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              <span className="text-gray-500">⚙️</span>
            </div>

            {/* Statut actuel */}
            <div className="space-y-3">
              {!isNotificationGranted && (
                <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-yellow-800">
                        Autoriser les notifications
                      </p>
                      <p className="text-xs text-yellow-600 mt-1">
                        Recevez des alertes de trading en temps réel
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {isNotificationGranted && !isSubscribed && (
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-800">
                        Activer les notifications push
                      </p>
                      <p className="text-xs text-blue-600 mt-1">
                        Restez informé des signaux de trading
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {isSubscribed && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-800">
                        ✓ Notifications activées
                      </p>
                      <p className="text-xs text-green-600 mt-1">
                        Vous recevrez des alertes de trading
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-2">
                <button
                  onClick={handleToggleNotifications}
                  disabled={isRegistering}
                  className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isSubscribed
                      ? 'bg-red-100 text-red-700 hover:bg-red-200'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  } ${isRegistering ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isRegistering ? (
                    'Chargement...'
                  ) : isSubscribed ? (
                    'Désactiver'
                  ) : (
                    'Activer'
                  )}
                </button>

                {isSubscribed && (
                  <button
                    onClick={testNotification}
                    className="px-3 py-2 text-sm text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 transition-colors"
                  >
                    Test
                  </button>
                )}
              </div>

              {/* Informations */}
              <div className="text-xs text-gray-500 space-y-1">
                <p>• Signaux de trading BUY/SELL/HOLD</p>
                <p>• Alertes de prix personnalisées</p>
                <p>• Mouvements importants du marché</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Overlay pour fermer le dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};