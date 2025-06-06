import React, { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { setUser } from '../store/slices/authSlice';
import { userAPI, getAuthToken } from '../services/api';

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const token = getAuthToken();
    if (token && !user) {
      // Try to get user profile with existing token
      userAPI.getProfile()
        .then((userData) => {
          dispatch(setUser(userData));
        })
        .catch(() => {
          // Token is invalid, redirect to login
        });
    }
  }, [dispatch, user]);

  if (!isAuthenticated && !getAuthToken()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;