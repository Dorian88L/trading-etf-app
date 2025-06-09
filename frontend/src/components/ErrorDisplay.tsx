import React from 'react';
import {
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { UserFriendlyError } from '../utils/errorHandler';

interface ErrorDisplayProps {
  error: UserFriendlyError;
  onDismiss?: () => void;
  onRetry?: () => void;
  className?: string;
  showDismiss?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
  onRetry,
  className = '',
  showDismiss = true
}) => {
  const getIcon = () => {
    switch (error.severity) {
      case 'error':
        return <XCircleIcon className="h-6 w-6 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
      case 'info':
        return <InformationCircleIcon className="h-6 w-6 text-blue-500" />;
      default:
        return <ExclamationTriangleIcon className="h-6 w-6 text-gray-500" />;
    }
  };

  const getBackgroundColor = () => {
    switch (error.severity) {
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getTextColor = () => {
    switch (error.severity) {
      case 'error':
        return 'text-red-800';
      case 'warning':
        return 'text-yellow-800';
      case 'info':
        return 'text-blue-800';
      default:
        return 'text-gray-800';
    }
  };

  return (
    <div className={`rounded-lg border p-4 ${getBackgroundColor()} ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${getTextColor()}`}>
            {error.title}
          </h3>
          
          <div className={`mt-2 text-sm ${getTextColor()}`}>
            <p>{error.message}</p>
          </div>

          {(error.actions || onRetry || showDismiss) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {/* Actions personnalisées */}
              {error.actions?.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    error.severity === 'error'
                      ? 'text-red-700 bg-red-100 hover:bg-red-200 focus:ring-red-500'
                      : error.severity === 'warning'
                      ? 'text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:ring-yellow-500'
                      : 'text-blue-700 bg-blue-100 hover:bg-blue-200 focus:ring-blue-500'
                  }`}
                >
                  {action.label}
                </button>
              ))}

              {/* Bouton de retry */}
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    error.severity === 'error'
                      ? 'text-red-700 bg-red-100 hover:bg-red-200 focus:ring-red-500'
                      : error.severity === 'warning'
                      ? 'text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:ring-yellow-500'
                      : 'text-blue-700 bg-blue-100 hover:bg-blue-200 focus:ring-blue-500'
                  }`}
                >
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                  Réessayer
                </button>
              )}

              {/* Bouton de fermeture */}
              {showDismiss && onDismiss && (
                <button
                  onClick={onDismiss}
                  className={`inline-flex items-center px-3 py-2 border text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    error.severity === 'error'
                      ? 'border-red-300 text-red-700 bg-white hover:bg-red-50 focus:ring-red-500'
                      : error.severity === 'warning'
                      ? 'border-yellow-300 text-yellow-700 bg-white hover:bg-yellow-50 focus:ring-yellow-500'
                      : 'border-blue-300 text-blue-700 bg-white hover:bg-blue-50 focus:ring-blue-500'
                  }`}
                >
                  Fermer
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;