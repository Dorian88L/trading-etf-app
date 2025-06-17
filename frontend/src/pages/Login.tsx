import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { loginUser } from '../store/slices/authSlice';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [debugInfo, setDebugInfo] = useState('');
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Login form submitted with:', { email });
    setDebugInfo('Tentative de connexion...');
    
    try {
      const result = await dispatch(loginUser({ email, password }));
      console.log('Login result:', result);
      setDebugInfo(`Résultat: ${JSON.stringify(result, null, 2)}`);
    } catch (error) {
      console.error('Login error:', error);
      setDebugInfo(`Erreur: ${JSON.stringify(error, null, 2)}`);
    }
  };
  
  // Test direct de l'API
  const testDirectAPI = async () => {
    setDebugInfo('Test direct de l\'API...');
    try {
      const formData = new URLSearchParams();
      formData.append('username', email || 'admin@investeclaire.fr');
      formData.append('password', password || 'Admin123#');
      
      const response = await fetch('https://api.investeclaire.fr/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
      });
      
      const data = await response.json();
      setDebugInfo(`Test direct - Status: ${response.status}, Data: ${JSON.stringify(data, null, 2)}`);
      console.log('Direct API test:', { status: response.status, data });
    } catch (error) {
      setDebugInfo(`Test direct - Erreur: ${error}`);
      console.error('Direct API error:', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Welcome to TradingETF - Your AI-powered ETF trading assistant
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="input mt-1"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="input mt-1"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="bg-danger-50 border border-danger-200 text-danger-600 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          {debugInfo && (
            <div className="bg-blue-50 border border-blue-200 text-blue-600 px-4 py-3 rounded text-xs">
              <strong>Debug:</strong><br/>
              <pre className="whitespace-pre-wrap">{debugInfo}</pre>
            </div>
          )}

          <div className="space-y-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary"
            >
              {isLoading ? 'Signing in...' : 'Sign in (Redux)'}
            </button>
            
            <button
              type="button"
              onClick={testDirectAPI}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
            >
              Test Direct API
            </button>
          </div>

          <div className="text-center">
            <span className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
                Sign up
              </Link>
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;