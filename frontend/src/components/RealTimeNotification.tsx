import React, { useState, useEffect } from 'react';
import { XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'info' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  autoHide?: boolean;
}

interface RealTimeNotificationProps {
  marketData: any[];
}

const RealTimeNotification: React.FC<RealTimeNotificationProps> = ({ marketData }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // Générer des notifications basées sur les données de marché
    if (marketData.length > 0) {
      const newNotifications: Notification[] = [];

      marketData.forEach(etf => {
        // Alerte pour les mouvements importants
        if (Math.abs(etf.change_percent) > 3) {
          newNotifications.push({
            id: `${etf.symbol}-${Date.now()}`,
            type: etf.change_percent > 0 ? 'success' : 'warning',
            title: `Mouvement important: ${etf.symbol}`,
            message: `${etf.name} a ${etf.change_percent > 0 ? 'augmenté' : 'chuté'} de ${Math.abs(etf.change_percent).toFixed(2)}%`,
            timestamp: new Date(),
            autoHide: true
          });
        }

        // Alerte pour les volumes élevés
        if (etf.volume > 100000) {
          newNotifications.push({
            id: `vol-${etf.symbol}-${Date.now()}`,
            type: 'info',
            title: `Volume élevé: ${etf.symbol}`,
            message: `Volume de ${etf.volume.toLocaleString('fr-FR')} détecté`,
            timestamp: new Date(),
            autoHide: true
          });
        }
      });

      if (newNotifications.length > 0) {
        setNotifications(prev => [...newNotifications, ...prev].slice(0, 5)); // Garder seulement les 5 dernières
      }
    }
  }, [marketData]);

  useEffect(() => {
    // Auto-masquer les notifications après 5 secondes
    const timer = setInterval(() => {
      setNotifications(prev => 
        prev.filter(notif => 
          !notif.autoHide || Date.now() - notif.timestamp.getTime() < 5000
        )
      );
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />;
      default:
        return <InformationCircleIcon className="h-6 w-6 text-blue-600" />;
    }
  };

  const getBackgroundColor = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${getBackgroundColor(notification.type)} border rounded-lg p-4 shadow-lg transform transition-all duration-300 ease-in-out animate-slide-in`}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {getIcon(notification.type)}
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900">
                {notification.title}
              </p>
              <p className="mt-1 text-sm text-gray-600">
                {notification.message}
              </p>
              <p className="mt-2 text-xs text-gray-500">
                {notification.timestamp.toLocaleTimeString('fr-FR')}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={() => removeNotification(notification.id)}
                className="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RealTimeNotification;