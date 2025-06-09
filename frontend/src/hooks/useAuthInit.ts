import { useEffect } from 'react';
import { useAppDispatch } from './redux';
import { fetchUserProfile, clearAuth } from '../store/slices/authSlice';
import { getAuthToken } from '../services/api';

export const useAuthInit = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const initializeAuth = async () => {
      // Check if user has a stored access token
      const token = getAuthToken();
      
      if (token) {
        try {
          // Try to fetch user profile with existing token
          await dispatch(fetchUserProfile()).unwrap();
        } catch (error) {
          // If token is invalid, clear auth state
          console.warn('Token invalid, clearing auth state');
          dispatch(clearAuth());
        }
      }
    };

    initializeAuth();
  }, [dispatch]);
};