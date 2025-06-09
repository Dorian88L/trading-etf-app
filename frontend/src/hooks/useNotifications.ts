import { useState, useEffect } from 'react';

interface UseNotificationsReturn {
  permission: NotificationPermission;
  supported: boolean;
  subscription: any | null;
  isRegistering: boolean;
  requestPermission: () => Promise<void>;
  registerPushNotifications: () => Promise<void>;
  unregisterPushNotifications: () => Promise<void>;
  testNotification: () => Promise<void>;
}

const useNotifications = (): UseNotificationsReturn => {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [supported, setSupported] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const [isRegistering, setIsRegistering] = useState(false);

  useEffect(() => {
    // Vérifier le support des notifications
    setSupported('Notification' in window && 'serviceWorker' in navigator);
    
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = async () => {
    if (!supported) return;
    
    try {
      const result = await Notification.requestPermission();
      setPermission(result);
    } catch (error) {
      console.error('Erreur lors de la demande de permission:', error);
    }
  };

  const registerPushNotifications = async () => {
    if (!supported || permission !== 'granted') return;
    
    setIsRegistering(true);
    try {
      // Service worker registration pour les notifications push
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
        setSubscription(registration);
      }
    } catch (error) {
      console.error('Erreur lors de l\'enregistrement:', error);
    } finally {
      setIsRegistering(false);
    }
  };

  const unregisterPushNotifications = async () => {
    try {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          await registration.unregister();
          setSubscription(null);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la désinscription:', error);
    }
  };

  const testNotification = async () => {
    if (!supported || permission !== 'granted') return;
    
    try {
      new Notification('🧪 Test de Notification', {
        body: 'Ceci est une notification de test de l\'application Trading ETF',
        icon: '/logo192.png',
        badge: '/favicon.ico'
      });
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la notification test:', error);
    }
  };

  return {
    permission,
    supported,
    subscription,
    isRegistering,
    requestPermission,
    registerPushNotifications,
    unregisterPushNotifications,
    testNotification
  };
};

export { useNotifications };
export default useNotifications;