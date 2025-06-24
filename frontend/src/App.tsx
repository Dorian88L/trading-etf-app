import React from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from './store';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ETFList from './pages/ETFList';
import ETFDetail from './pages/ETFDetail';
import ETFSelection from './pages/ETFSelection';
import ETFScoring from './pages/ETFScoring';
import Portfolio from './pages/Portfolio';
import Signals from './pages/Signals';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import Documentation from './pages/Documentation';
import Backtesting from './pages/Backtesting';
import MarketMonitoring from './pages/MarketMonitoring';
import Login from './pages/Login';
import Register from './pages/Register';
import ProtectedRoute from './components/ProtectedRoute';
import { useAppSelector } from './hooks/redux';
import { useAuthInit } from './hooks/useAuthInit';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
    },
  },
});

function AppRoutes() {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  
  // Initialize authentication on app start
  useAuthInit();

  return (
    <Routes>
      {/* Public routes */}
      <Route 
        path="/login" 
        element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} 
      />
      <Route 
        path="/register" 
        element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} 
      />
      
      {/* Protected routes */}
      <Route path="/" element={<ProtectedRoute />}>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="etfs" element={<ETFList />} />
          <Route path="etf/:symbol" element={<ETFDetail />} />
          <Route path="etf-selection" element={<ETFSelection />} />
          <Route path="scoring" element={<ETFScoring />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="signals" element={<Signals />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="backtesting" element={<Backtesting />} />
          <Route path="monitoring" element={<MarketMonitoring />} />
          <Route path="settings" element={<Settings />} />
          <Route path="documentation" element={<Documentation />} />
        </Route>
      </Route>
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="App min-h-screen bg-gray-50">
            <AppRoutes />
          </div>
        </Router>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
