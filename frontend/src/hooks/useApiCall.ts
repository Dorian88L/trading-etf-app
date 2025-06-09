import { useState, useCallback, useRef, useEffect } from 'react';
import { handleApiError, UserFriendlyError, isRetryableError, ApiError } from '../utils/errorHandler';

interface UseApiCallOptions {
  retryAttempts?: number;
  retryDelay?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: UserFriendlyError) => void;
  autoRetry?: boolean;
}

interface UseApiCallReturn<T> {
  data: T | null;
  loading: boolean;
  error: UserFriendlyError | null;
  execute: (...args: any[]) => Promise<T | null>;
  retry: () => Promise<T | null>;
  reset: () => void;
  lastAttempt: Date | null;
  attemptCount: number;
}

export function useApiCall<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiCallOptions = {}
): UseApiCallReturn<T> {
  const {
    retryAttempts = 3,
    retryDelay = 1000,
    onSuccess,
    onError,
    autoRetry = false
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<UserFriendlyError | null>(null);
  const [lastAttempt, setLastAttempt] = useState<Date | null>(null);
  const [attemptCount, setAttemptCount] = useState(0);

  const lastArgsRef = useRef<any[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const executeCall = useCallback(async (
    args: any[] = [],
    attempt: number = 1
  ): Promise<T | null> => {
    setLoading(true);
    setLastAttempt(new Date());
    setAttemptCount(attempt);

    try {
      const result = await apiFunction(...args);
      
      // Succès
      setData(result);
      setError(null);
      setLoading(false);
      
      onSuccess?.(result);
      return result;
      
    } catch (err) {
      const userError = handleApiError(err);
      const apiError = err as ApiError;
      
      // Vérifier s'il faut retry automatiquement
      const shouldRetry = autoRetry && 
                         attempt < retryAttempts && 
                         isRetryableError(apiError);

      if (shouldRetry) {
        // Retry avec délai exponentiel
        const delay = retryDelay * Math.pow(2, attempt - 1);
        
        timeoutRef.current = setTimeout(() => {
          executeCall(args, attempt + 1);
        }, delay);
        
        return null;
      } else {
        // Erreur finale
        setError(userError);
        setData(null);
        setLoading(false);
        
        onError?.(userError);
        return null;
      }
    }
  }, [apiFunction, retryAttempts, retryDelay, onSuccess, onError, autoRetry]);

  const execute = useCallback(async (...args: any[]): Promise<T | null> => {
    lastArgsRef.current = args;
    setAttemptCount(0);
    
    // Annuler tout retry en cours
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    return executeCall(args, 1);
  }, [executeCall]);

  const retry = useCallback(async (): Promise<T | null> => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    return executeCall(lastArgsRef.current, 1);
  }, [executeCall]);

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    setData(null);
    setError(null);
    setLoading(false);
    setLastAttempt(null);
    setAttemptCount(0);
    lastArgsRef.current = [];
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    retry,
    reset,
    lastAttempt,
    attemptCount
  };
}

export default useApiCall;