/**
 * Gestionnaire d'erreurs centralisé pour l'application Trading ETF
 * Fournit des messages d'erreur utilisateur-friendly et la gestion des erreurs API
 */

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface UserFriendlyError {
  title: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

class ErrorHandler {
  private errorLog: ApiError[] = [];
  private maxLogSize = 100;

  /**
   * Transforme une erreur API en message utilisateur-friendly
   */
  public handleApiError(error: any): UserFriendlyError {
    const apiError = this.parseError(error);
    this.logError(apiError);

    return this.getUserFriendlyMessage(apiError);
  }

  /**
   * Parse une erreur pour extraire les informations utiles
   */
  private parseError(error: any): ApiError {
    const timestamp = new Date().toISOString();

    // Erreur Axios/Fetch
    if (error.response) {
      return {
        status: error.response.status,
        code: error.response.data?.code || 'API_ERROR',
        message: error.response.data?.detail || error.response.data?.message || error.message,
        details: error.response.data,
        timestamp
      };
    }

    // Erreur réseau
    if (error.request) {
      return {
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Impossible de contacter le serveur',
        details: { originalError: error.message },
        timestamp
      };
    }

    // Erreur JavaScript
    return {
      status: 500,
      code: 'CLIENT_ERROR',
      message: error.message || 'Une erreur inattendue s\'est produite',
      details: { stack: error.stack },
      timestamp
    };
  }

  /**
   * Convertit une erreur API en message utilisateur-friendly
   */
  private getUserFriendlyMessage(apiError: ApiError): UserFriendlyError {
    switch (apiError.status) {
      case 401:
        return {
          title: '🔐 Authentification requise',
          message: 'Veuillez vous connecter pour accéder à cette fonctionnalité.',
          severity: 'warning',
          actions: [
            {
              label: 'Se connecter',
              action: () => window.location.href = '/login'
            }
          ]
        };

      case 403:
        return {
          title: '🚫 Accès refusé',
          message: 'Vous n\'avez pas les permissions nécessaires pour cette action.',
          severity: 'error'
        };

      case 404:
        return {
          title: '🔍 Ressource introuvable',
          message: 'La donnée demandée n\'existe pas ou n\'est plus disponible.',
          severity: 'warning'
        };

      case 422:
        return {
          title: '⚠️ Données invalides',
          message: this.formatValidationErrors(apiError.details),
          severity: 'warning'
        };

      case 429:
        return {
          title: '⏰ Trop de requêtes',
          message: 'Veuillez patienter quelques instants avant de réessayer.',
          severity: 'warning',
          actions: [
            {
              label: 'Réessayer dans 30s',
              action: () => setTimeout(() => window.location.reload(), 30000)
            }
          ]
        };

      case 500:
        return {
          title: '🔧 Erreur serveur',
          message: 'Une erreur technique s\'est produite. Notre équipe a été notifiée.',
          severity: 'error',
          actions: [
            {
              label: 'Actualiser la page',
              action: () => window.location.reload()
            }
          ]
        };

      case 503:
        return {
          title: '🚧 Service temporairement indisponible',
          message: 'Le service est en maintenance. Veuillez réessayer dans quelques minutes.',
          severity: 'warning'
        };

      case 0:
        return {
          title: '🌐 Problème de connexion',
          message: 'Vérifiez votre connexion internet et réessayez.',
          severity: 'error',
          actions: [
            {
              label: 'Réessayer',
              action: () => window.location.reload()
            }
          ]
        };

      default:
        return {
          title: '❌ Erreur inattendue',
          message: apiError.message || 'Une erreur s\'est produite. Veuillez réessayer.',
          severity: 'error',
          actions: [
            {
              label: 'Actualiser',
              action: () => window.location.reload()
            }
          ]
        };
    }
  }

  /**
   * Formate les erreurs de validation
   */
  private formatValidationErrors(details: any): string {
    if (!details) return 'Les données fournies ne sont pas valides.';

    if (Array.isArray(details)) {
      return details.map(error => 
        `${error.loc ? error.loc.join('.') + ': ' : ''}${error.msg}`
      ).join(', ');
    }

    if (typeof details === 'object' && details.detail) {
      return Array.isArray(details.detail) 
        ? details.detail.map((d: any) => d.msg || d).join(', ')
        : details.detail;
    }

    return 'Données invalides.';
  }

  /**
   * Enregistre l'erreur dans le log local
   */
  private logError(apiError: ApiError): void {
    this.errorLog.unshift(apiError);
    
    // Maintenir la taille du log
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }

    // Log en console en développement
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', apiError);
    }
  }

  /**
   * Récupère le log des erreurs
   */
  public getErrorLog(): ApiError[] {
    return [...this.errorLog];
  }

  /**
   * Efface le log des erreurs
   */
  public clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Détermine si une erreur est récupérable
   */
  public isRetryableError(error: ApiError): boolean {
    return [408, 429, 500, 502, 503, 504].includes(error.status);
  }

  /**
   * Suggestions d'actions basées sur le type d'erreur
   */
  public getSuggestions(error: ApiError): string[] {
    const suggestions: string[] = [];

    switch (error.status) {
      case 0:
        suggestions.push('Vérifiez votre connexion internet');
        suggestions.push('Vérifiez que le serveur est accessible');
        break;
      case 401:
        suggestions.push('Reconnectez-vous à votre compte');
        suggestions.push('Vérifiez que votre session n\'a pas expiré');
        break;
      case 403:
        suggestions.push('Contactez un administrateur');
        suggestions.push('Vérifiez vos permissions');
        break;
      case 404:
        suggestions.push('Vérifiez l\'URL ou l\'identifiant');
        suggestions.push('La ressource a peut-être été supprimée');
        break;
      case 422:
        suggestions.push('Vérifiez les données saisies');
        suggestions.push('Tous les champs requis sont-ils remplis ?');
        break;
      case 429:
        suggestions.push('Attendez quelques secondes avant de réessayer');
        suggestions.push('Réduisez la fréquence de vos requêtes');
        break;
      case 500:
        suggestions.push('Réessayez dans quelques minutes');
        suggestions.push('Contactez le support si le problème persiste');
        break;
      case 503:
        suggestions.push('Le service est temporairement indisponible');
        suggestions.push('Réessayez dans quelques minutes');
        break;
      default:
        suggestions.push('Actualisez la page');
        suggestions.push('Réessayez votre action');
    }

    return suggestions;
  }

  /**
   * Génère un rapport d'erreur pour le débogage
   */
  public generateErrorReport(): string {
    const recentErrors = this.errorLog.slice(0, 10);
    const errorCounts = this.getErrorStatistics();

    return `
=== RAPPORT D'ERREURS TRADING ETF ===
Généré le: ${new Date().toLocaleString()}

Erreurs récentes (10 dernières):
${recentErrors.map(error => 
  `[${error.timestamp}] ${error.status} ${error.code}: ${error.message}`
).join('\n')}

Statistiques:
${Object.entries(errorCounts).map(([code, count]) => 
  `${code}: ${count} occurrences`
).join('\n')}

Total des erreurs: ${this.errorLog.length}
    `.trim();
  }

  /**
   * Statistiques des erreurs
   */
  private getErrorStatistics(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    this.errorLog.forEach(error => {
      stats[error.code] = (stats[error.code] || 0) + 1;
    });

    return stats;
  }
}

// Instance singleton
export const errorHandler = new ErrorHandler();

// Utilitaires d'export
export const handleApiError = (error: any) => errorHandler.handleApiError(error);
export const getErrorLog = () => errorHandler.getErrorLog();
export const clearErrorLog = () => errorHandler.clearErrorLog();
export const isRetryableError = (error: ApiError) => errorHandler.isRetryableError(error);
export const getSuggestions = (error: ApiError) => errorHandler.getSuggestions(error);
export const generateErrorReport = () => errorHandler.generateErrorReport();