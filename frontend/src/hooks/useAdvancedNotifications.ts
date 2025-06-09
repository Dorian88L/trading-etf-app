import { useState, useEffect, useCallback } from 'react';
import { notificationService } from '../services/notificationService';

interface UseAdvancedNotificationsReturn {
  isSupported: boolean;
  permission: NotificationPermission;
  pendingCount: number;
  requestPermission: () => Promise<NotificationPermission>;
  sendPriceAlert: (symbol: string, price: number, change: number, targetPrice: number) => Promise<void>;
  sendTradingSignal: (signal: any) => Promise<void>;
  sendPortfolioUpdate: (value: number, change: number, changePercent: number) => Promise<void>;
  sendMarketAlert: (status: string, message: string) => Promise<void>;
  sendTestNotification: () => Promise<void>;
}

const useAdvancedNotifications = (): UseAdvancedNotificationsReturn => {
  const [isSupported, setIsSupported] = useState(notificationService.isNotificationSupported);
  const [permission, setPermission] = useState<NotificationPermission>(notificationService.notificationPermission);
  const [pendingCount, setPendingCount] = useState(notificationService.pendingNotifications);

  // Mettre à jour l'état quand les propriétés du service changent
  useEffect(() => {
    const updateState = () => {
      setIsSupported(notificationService.isNotificationSupported);
      setPermission(notificationService.notificationPermission);
      setPendingCount(notificationService.pendingNotifications);
    };

    // Vérifier les changements toutes les secondes
    const interval = setInterval(updateState, 1000);

    return () => clearInterval(interval);
  }, []);

  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    try {
      const result = await notificationService.requestPermission();
      setPermission(result);
      return result;
    } catch (error) {
      console.error('Erreur lors de la demande de permission:', error);
      throw error;
    }
  }, []);

  const sendPriceAlert = useCallback(async (
    symbol: string, 
    price: number, 
    change: number, 
    targetPrice: number
  ): Promise<void> => {
    try {
      await notificationService.sendPriceAlert(symbol, price, change, targetPrice);
    } catch (error) {
      console.error('Erreur lors de l\'envoi de l\'alerte prix:', error);
      throw error;
    }
  }, []);

  const sendTradingSignal = useCallback(async (signal: any): Promise<void> => {
    try {
      await notificationService.sendTradingSignal(signal);
    } catch (error) {
      console.error('Erreur lors de l\'envoi du signal trading:', error);
      throw error;
    }
  }, []);

  const sendPortfolioUpdate = useCallback(async (
    value: number, 
    change: number, 
    changePercent: number
  ): Promise<void> => {
    try {
      await notificationService.sendPortfolioUpdate(value, change, changePercent);
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la mise à jour portfolio:', error);
      throw error;
    }
  }, []);

  const sendMarketAlert = useCallback(async (status: string, message: string): Promise<void> => {
    try {
      await notificationService.sendMarketAlert(status, message);
    } catch (error) {
      console.error('Erreur lors de l\'envoi de l\'alerte marché:', error);
      throw error;
    }
  }, []);

  const sendTestNotification = useCallback(async (): Promise<void> => {
    try {
      await notificationService.testNotification();
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la notification test:', error);
      throw error;
    }
  }, []);

  return {
    isSupported,
    permission,
    pendingCount,
    requestPermission,
    sendPriceAlert,
    sendTradingSignal,
    sendPortfolioUpdate,
    sendMarketAlert,
    sendTestNotification
  };
};

export default useAdvancedNotifications;