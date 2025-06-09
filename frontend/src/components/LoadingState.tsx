import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import ErrorDisplay from './ErrorDisplay';
import { UserFriendlyError } from '../utils/errorHandler';

interface LoadingStateProps {
  loading?: boolean;
  error?: UserFriendlyError | null;
  children: React.ReactNode;
  onRetry?: () => void;
  onErrorDismiss?: () => void;
  loadingComponent?: React.ReactNode;
  emptyStateComponent?: React.ReactNode;
  isEmpty?: boolean;
  className?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  loading = false,
  error = null,
  children,
  onRetry,
  onErrorDismiss,
  loadingComponent,
  emptyStateComponent,
  isEmpty = false,
  className = ''
}) => {
  // Composant de chargement par défaut
  const defaultLoadingComponent = (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center space-y-4">
        <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
        <p className="text-gray-600 text-sm">Chargement en cours...</p>
      </div>
    </div>
  );

  // Composant d'état vide par défaut
  const defaultEmptyStateComponent = (
    <div className="text-center py-12">
      <div className="mx-auto h-12 w-12 text-gray-400">
        <svg
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune donnée</h3>
      <p className="mt-1 text-sm text-gray-500">
        Il n'y a actuellement aucune donnée à afficher.
      </p>
    </div>
  );

  return (
    <div className={className}>
      {/* Affichage d'erreur */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={onRetry}
          onDismiss={onErrorDismiss}
          className="mb-4"
        />
      )}

      {/* État de chargement */}
      {loading && (loadingComponent || defaultLoadingComponent)}

      {/* État vide */}
      {!loading && !error && isEmpty && (emptyStateComponent || defaultEmptyStateComponent)}

      {/* Contenu normal */}
      {!loading && !error && !isEmpty && children}
    </div>
  );
};

export default LoadingState;