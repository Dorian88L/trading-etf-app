/**
 * Service de notifications push pour l'application Trading ETF
 * Gère les notifications browser, web push et en temps réel
 */

interface NotificationData {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: any;
  actions?: NotificationAction[];
}

interface NotificationAction {
  action: string;
  title: string;
  icon?: string;
}

export class NotificationService {
  private static instance: NotificationService;
  private isSupported: boolean = false;
  private permission: NotificationPermission = 'default';
  private notificationQueue: NotificationData[] = [];
  private isProcessingQueue: boolean = false;

  private constructor() {
    this.initialize();
  }

  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private initialize() {
    // Vérifier le support des notifications
    this.isSupported = 'Notification' in window;
    
    if (this.isSupported) {
      this.permission = Notification.permission;
      
      // Écouter les changements de permission
      this.setupPermissionListener();
      
      // Initialiser le service worker si supporté
      this.initializeServiceWorker();
    }
  }

  private setupPermissionListener() {
    // Vérifier périodiquement les changements de permission
    setInterval(() => {
      if (this.permission !== Notification.permission) {
        this.permission = Notification.permission;
        this.onPermissionChange();
      }
    }, 1000);
  }

  private onPermissionChange() {
    console.log('Permission de notification changée:', this.permission);
    
    if (this.permission === 'granted' && this.notificationQueue.length > 0) {
      this.processQueue();
    }
  }

  private async initializeServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker enregistré:', registration);
        
        // Écouter les messages du service worker
        navigator.serviceWorker.addEventListener('message', this.handleServiceWorkerMessage);
        
        return registration;
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement du Service Worker:', error);
        return null;
      }
    }
    return null;
  }

  private handleServiceWorkerMessage = (event: MessageEvent) => {
    const { type, data } = event.data;
    
    switch (type) {
      case 'notification-click':
        this.handleNotificationClick(data);
        break;
      case 'notification-close':
        this.handleNotificationClose(data);
        break;
      default:
        console.log('Message Service Worker non géré:', event.data);
    }
  };

  private handleNotificationClick(data: any) {
    console.log('Notification cliquée:', data);
    
    // Naviguer vers la page appropriée selon le type de notification
    if (data.type === 'price-alert') {
      window.location.href = `/etf/${data.symbol}`;
    } else if (data.type === 'signal') {
      window.location.href = '/signals';
    } else if (data.type === 'portfolio') {
      window.location.href = '/portfolio';
    }
  }

  private handleNotificationClose(data: any) {
    console.log('Notification fermée:', data);
  }

  /**
   * Demander la permission pour les notifications
   */
  public async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported) {
      throw new Error('Les notifications ne sont pas supportées par ce navigateur');
    }

    if (this.permission === 'granted') {
      return this.permission;
    }

    try {
      this.permission = await Notification.requestPermission();
      return this.permission;
    } catch (error) {
      console.error('Erreur lors de la demande de permission:', error);
      throw error;
    }
  }

  /**
   * Envoyer une notification simple
   */
  public async sendNotification(data: NotificationData): Promise<void> {
    if (!this.isSupported) {
      console.warn('Notifications non supportées, affichage en console:', data);
      return;
    }

    if (this.permission !== 'granted') {
      // Ajouter à la queue si permission pas encore accordée
      this.notificationQueue.push(data);
      
      // Essayer de demander la permission
      try {
        await this.requestPermission();
      } catch (error) {
        console.error('Permission refusée:', error);
        return;
      }
    }

    if (this.permission === 'granted') {
      this.showNotification(data);
    }
  }

  private showNotification(data: NotificationData) {
    const options: NotificationOptions = {
      body: data.body,
      icon: data.icon || '/logo192.png',
      badge: data.badge || '/favicon.ico',
      tag: data.tag,
      data: data.data,
      requireInteraction: true,
      actions: data.actions
    };

    const notification = new Notification(data.title, options);

    // Gérer les événements de notification
    notification.onclick = () => {
      this.handleNotificationClick(data.data || {});
      notification.close();
    };

    notification.onclose = () => {
      this.handleNotificationClose(data.data || {});
    };

    notification.onerror = (error) => {
      console.error('Erreur notification:', error);
    };

    // Auto-fermer après 10 secondes
    setTimeout(() => {
      notification.close();
    }, 10000);
  }

  private async processQueue() {
    if (this.isProcessingQueue || this.notificationQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;

    while (this.notificationQueue.length > 0) {
      const notification = this.notificationQueue.shift();
      if (notification) {
        this.showNotification(notification);
        // Délai entre les notifications pour éviter le spam
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    this.isProcessingQueue = false;
  }

  /**
   * Notifications spécialisées pour l'application Trading ETF
   */

  public async sendPriceAlert(symbol: string, price: number, change: number, targetPrice: number) {
    const direction = change > 0 ? '📈' : '📉';
    const changeText = change > 0 ? 'hausse' : 'baisse';
    
    await this.sendNotification({
      title: `${direction} Alerte Prix - ${symbol}`,
      body: `Prix actuel: ${price}€ (${changeText} de ${Math.abs(change).toFixed(2)}%)\nPrix cible: ${targetPrice}€`,
      icon: '/logo192.png',
      tag: `price-alert-${symbol}`,
      data: {
        type: 'price-alert',
        symbol,
        price,
        change,
        targetPrice
      },
      actions: [
        {
          action: 'view',
          title: 'Voir ETF'
        },
        {
          action: 'dismiss',
          title: 'Ignorer'
        }
      ]
    });
  }

  public async sendTradingSignal(signal: any) {
    const emoji = signal.signal_type === 'BUY' ? '🟢' : '🔴';
    
    await this.sendNotification({
      title: `${emoji} Signal de Trading - ${signal.etf_symbol}`,
      body: `${signal.signal_type} - Confiance: ${signal.confidence}%\nStratégie: ${signal.strategy}`,
      icon: '/logo192.png',
      tag: `signal-${signal.etf_symbol}`,
      data: {
        type: 'signal',
        signal
      },
      actions: [
        {
          action: 'view-signals',
          title: 'Voir Signaux'
        },
        {
          action: 'view-etf',
          title: 'Voir ETF'
        }
      ]
    });
  }

  public async sendPortfolioUpdate(portfolioValue: number, change: number, changePercent: number) {
    const emoji = change > 0 ? '📈' : '📉';
    const direction = change > 0 ? 'hausse' : 'baisse';
    
    await this.sendNotification({
      title: `${emoji} Mise à jour Portfolio`,
      body: `Valeur: ${portfolioValue.toFixed(2)}€\n${direction.charAt(0).toUpperCase() + direction.slice(1)} de ${Math.abs(changePercent).toFixed(2)}% (${change > 0 ? '+' : ''}${change.toFixed(2)}€)`,
      icon: '/logo192.png',
      tag: 'portfolio-update',
      data: {
        type: 'portfolio',
        value: portfolioValue,
        change,
        changePercent
      }
    });
  }

  public async sendMarketAlert(marketStatus: string, message: string) {
    const emoji = marketStatus === 'bullish' ? '🐂' : marketStatus === 'bearish' ? '🐻' : '⚖️';
    
    await this.sendNotification({
      title: `${emoji} Alerte Marché`,
      body: message,
      icon: '/logo192.png',
      tag: 'market-alert',
      data: {
        type: 'market',
        status: marketStatus
      }
    });
  }

  /**
   * Getters pour l'état du service
   */
  public get isNotificationSupported(): boolean {
    return this.isSupported;
  }

  public get notificationPermission(): NotificationPermission {
    return this.permission;
  }

  public get pendingNotifications(): number {
    return this.notificationQueue.length;
  }

  /**
   * Tester les notifications
   */
  public async testNotification() {
    await this.sendNotification({
      title: '🧪 Test de Notification',
      body: 'Ceci est une notification de test de l\'application Trading ETF',
      icon: '/logo192.png',
      tag: 'test-notification',
      data: {
        type: 'test',
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Nettoyer les ressources
   */
  public cleanup() {
    this.notificationQueue = [];
    
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.removeEventListener('message', this.handleServiceWorkerMessage);
    }
  }
}

// Export de l'instance singleton
export const notificationService = NotificationService.getInstance();