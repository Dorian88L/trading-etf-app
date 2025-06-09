import React, { useState, useEffect } from 'react';
import useNotifications from '../../hooks/useNotifications';

interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  sent_at: string;
}

interface NotificationManagerProps {
  className?: string;
}

export const NotificationManager: React.FC<NotificationManagerProps> = ({ className = '' }) => {
  const {
    supported,
    permission,
    subscription,
    registerPushNotifications,
    unregisterPushNotifications,
    testNotification
  } = useNotifications();

  // Mock data for notifications - replace with actual API calls
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleSubscribe = async () => {
    try {
      await registerPushNotifications();
    } catch (error) {
      console.error('Erreur lors de l\'abonnement:', error);
    }
  };

  const handleUnsubscribe = async () => {
    try {
      await unregisterPushNotifications();
    } catch (error) {
      console.error('Erreur lors de la désinscription:', error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'signal_buy':
        return <span className="text-green-500 text-lg">📈</span>;
      case 'signal_sell':
        return <span className="text-red-500 text-lg">📉</span>;
      case 'price_alert':
        return <span className="text-yellow-500 text-lg">⚠️</span>;
      default:
        return <span className="text-blue-500 text-lg">🔔</span>;
    }
  };

  const formatNotificationTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'À l\'instant';
    if (diffInMinutes < 60) return `${diffInMinutes}min`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
    return date.toLocaleDateString();
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, is_read: true } : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, is_read: true }))
    );
    setUnreadCount(0);
  };

  if (!supported) {
    return (
      <div className={`text-gray-500 ${className}`}>
        <span className="text-xl">🔕</span>
        <span className="sr-only">Notifications non supportées</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Bouton principal */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg transition-colors"
        aria-label="Notifications"
      >
        {subscription ? (
          <span className="text-xl text-blue-600">🔔</span>
        ) : (
          <span className="text-xl text-gray-400">🔕</span>
        )}
        
        {/* Badge de notifications non lues */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown des notifications */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-gray-500 hover:text-gray-700"
                  title="Paramètres"
                >
                  <span className="text-sm">⚙️</span>
                </button>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                    title="Tout marquer comme lu"
                  >
                    <span className="text-sm">✓</span>
                  </button>
                )}
              </div>
            </div>

            {/* Statut des notifications */}
            <div className="mt-2">
              {permission === 'default' && (
                <div className="flex items-center justify-between p-2 bg-yellow-50 rounded">
                  <span className="text-sm text-yellow-800">
                    Autorisez les notifications pour recevoir des alertes
                  </span>
                  <button
                    onClick={handleSubscribe}
                    className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                  >
                    Activer
                  </button>
                </div>
              )}
              
              {permission === 'denied' && (
                <div className="p-2 bg-red-50 rounded">
                  <span className="text-sm text-red-800">
                    Notifications bloquées. Modifiez les paramètres de votre navigateur.
                  </span>
                </div>
              )}
              
              {permission === 'granted' && !subscription && (
                <div className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <span className="text-sm text-blue-800">
                    Notifications autorisées mais non activées
                  </span>
                  <button
                    onClick={handleSubscribe}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    S'abonner
                  </button>
                </div>
              )}
              
              {subscription && (
                <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <span className="text-sm text-green-800">
                    ✓ Notifications activées
                  </span>
                  <div className="flex space-x-2">
                    <button
                      onClick={testNotification}
                      className="text-green-600 hover:text-green-800 text-sm"
                    >
                      Test
                    </button>
                    <button
                      onClick={handleUnsubscribe}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Désactiver
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Liste des notifications */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <span className="text-2xl text-gray-300 block mb-2">🔔</span>
                <p>Aucune notification</p>
              </div>
            ) : (
              notifications.map((notification: Notification) => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.notification_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {notification.title}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.message}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {formatNotificationTime(notification.sent_at)}
                        </span>
                        {!notification.is_read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-200">
            <button
              onClick={() => {
                setShowDropdown(false);
                // Rediriger vers la page des notifications
                window.location.href = '/notifications';
              }}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-800"
            >
              Voir toutes les notifications
            </button>
          </div>
        </div>
      )}

      {/* Paramètres rapides */}
      {showSettings && (
        <div className="absolute right-0 mt-12 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-4">
            <h4 className="font-medium text-gray-900 mb-3">Paramètres rapides</h4>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="ml-2 text-sm text-gray-700">Signaux de trading</span>
              </label>
              
              <label className="flex items-center">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="ml-2 text-sm text-gray-700">Alertes de prix</span>
              </label>
              
              <label className="flex items-center">
                <input type="checkbox" className="rounded" />
                <span className="ml-2 text-sm text-gray-700">Alertes de marché</span>
              </label>
            </div>
            
            <div className="mt-4 pt-3 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowSettings(false);
                  window.location.href = '/settings/notifications';
                }}
                className="w-full text-center text-sm text-blue-600 hover:text-blue-800"
              >
                Paramètres avancés
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Overlay pour fermer les dropdowns */}
      {(showDropdown || showSettings) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowDropdown(false);
            setShowSettings(false);
          }}
        />
      )}
    </div>
  );
};