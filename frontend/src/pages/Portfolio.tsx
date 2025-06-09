import React, { useState, useEffect } from 'react';
import { portfolioAPI } from '../services/api';

interface Position {
  id: string;
  etf_isin: string;
  symbol?: string;
  name?: string;
  quantity: number;
  average_price: number;
  current_price?: number;
  market_value?: number;
  unrealized_gain_loss?: number;
  unrealized_gain_loss_percent?: number;
  sector?: string;
  created_at: string;
  updated_at: string;
}

interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
  cash_balance: number;
  day_change: number;
  day_change_percent: number;
  positions_count: number;
}

interface Transaction {
  id: string;
  portfolio_id: string;
  etf_isin: string;
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  fees: number;
  total_amount: number;
  created_at: string;
  status?: string;
}

interface PortfolioData {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

const Portfolio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'positions' | 'transactions' | 'analytics'>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  
  // Portfolio data
  const [portfolios, setPortfolios] = useState<PortfolioData[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
  const [summary, setSummary] = useState<PortfolioSummary>({
    total_value: 0,
    total_cost: 0,
    total_gain_loss: 0,
    total_gain_loss_percent: 0,
    cash_balance: 0,
    day_change: 0,
    day_change_percent: 0,
    positions_count: 0
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [rebalanceDate, setRebalanceDate] = useState<string>('');

  // Load portfolios on component mount
  useEffect(() => {
    loadPortfolios();
  }, []);

  // Load portfolio data when selected portfolio changes
  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioData(selectedPortfolio);
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Try to get portfolios from the portfolio management system first
      try {
        const response = await fetch('/api/v1/portfolio-management/portfolios', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success' && data.data && data.data.length > 0) {
            setPortfolios(data.data);
            setSelectedPortfolio(data.data[0].id);
            return;
          }
        }
      } catch (managementError) {
        console.log('Portfolio management API not available, trying legacy API');
      }
      
      // Fallback to legacy API
      const response = await portfolioAPI.getPortfolios();
      
      if (response && response.length > 0) {
        setPortfolios(response);
        setSelectedPortfolio(response[0].id);
      } else {
        // Create a default portfolio if none exists
        const newPortfolio = await portfolioAPI.createPortfolio('Portfolio Principal');
        setPortfolios([newPortfolio]);
        setSelectedPortfolio(newPortfolio.id);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des portfolios:', err);
      setError('Erreur lors du chargement des portfolios. ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolioData = async (portfolioId: string) => {
    try {
      setLoading(true);
      setError('');

      // Try portfolio management API first
      try {
        const detailsResponse = await fetch(`/api/v1/portfolio-management/portfolios/${portfolioId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (detailsResponse.ok) {
          const detailsData = await detailsResponse.json();
          if (detailsData.status === 'success') {
            const portfolioData = detailsData.data;
            
            // Set summary data from portfolio management API
            setSummary({
              total_value: portfolioData.metrics.total_value,
              total_cost: portfolioData.metrics.total_invested,
              total_gain_loss: portfolioData.metrics.unrealized_pnl,
              total_gain_loss_percent: portfolioData.metrics.unrealized_pnl_percent,
              cash_balance: 5000, // TODO: Implement cash tracking
              day_change: 0, // TODO: Calculate daily change
              day_change_percent: 0,
              positions_count: portfolioData.metrics.positions_count
            });
            
            // Transform positions data
            const transformedPositions = portfolioData.positions.map((pos: any) => ({
              id: pos.id,
              etf_isin: pos.etf_isin,
              symbol: pos.etf_symbol,
              name: pos.etf_name,
              quantity: pos.quantity,
              average_price: pos.average_price,
              current_price: pos.current_price,
              market_value: pos.current_value,
              unrealized_gain_loss: pos.unrealized_pnl,
              unrealized_gain_loss_percent: pos.unrealized_pnl_percent,
              sector: pos.sector,
              created_at: pos.opened_at,
              updated_at: pos.updated_at
            }));
            
            setPositions(transformedPositions);
            
            // Load transactions
            const transactionsResponse = await fetch(`/api/v1/portfolio-management/portfolios/${portfolioId}/transactions?limit=100`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (transactionsResponse.ok) {
              const transactionsData = await transactionsResponse.json();
              if (transactionsData.status === 'success') {
                const transformedTransactions = transactionsData.data.map((tx: any) => ({
                  id: tx.id,
                  portfolio_id: portfolioId,
                  etf_isin: tx.etf_isin,
                  transaction_type: tx.type,
                  quantity: tx.quantity,
                  price: tx.price,
                  fees: tx.fees,
                  total_amount: tx.total_amount,
                  created_at: tx.executed_at,
                  status: 'COMPLETED'
                }));
                setTransactions(transformedTransactions);
              }
            }
            
            return;
          }
        }
      } catch (managementError) {
        console.log('Portfolio management API not available, using legacy API');
      }

      // Fallback to legacy API
      const [summaryData, positionsData, transactionsData] = await Promise.all([
        portfolioAPI.getPortfolioSummary(portfolioId).catch(() => null),
        portfolioAPI.getPortfolioPositions(portfolioId).catch(() => []),
        portfolioAPI.getPortfolioTransactions(portfolioId).catch(() => [])
      ]);

      // Set summary data
      if (summaryData) {
        setSummary(summaryData);
      } else {
        // Calculate summary from positions if API doesn't return it
        const totalValue = positionsData.reduce((sum: number, pos: Position) => 
          sum + (pos.market_value || pos.quantity * pos.average_price), 0
        );
        const totalCost = positionsData.reduce((sum: number, pos: Position) => 
          sum + (pos.quantity * pos.average_price), 0
        );
        
        setSummary({
          total_value: totalValue,
          total_cost: totalCost,
          total_gain_loss: totalValue - totalCost,
          total_gain_loss_percent: totalCost > 0 ? ((totalValue - totalCost) / totalCost) * 100 : 0,
          cash_balance: 5000, // Default cash balance
          day_change: 0,
          day_change_percent: 0,
          positions_count: positionsData.length
        });
      }

      setPositions(positionsData || []);
      setTransactions(transactionsData || []);

    } catch (err: any) {
      console.error('Erreur lors du chargement des données du portfolio:', err);
      setError('Erreur lors du chargement des données. ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const refreshPortfolio = async () => {
    if (selectedPortfolio) {
      await loadPortfolioData(selectedPortfolio);
    }
  };

  const handleRebalance = async () => {
    if (!rebalanceDate) {
      alert('Veuillez sélectionner une date de rééquilibrage');
      return;
    }
    
    // Simulate rebalancing - in real app this would call an API
    setLoading(true);
    try {
      // Here you would implement actual rebalancing logic
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('Rééquilibrage programmé avec succès !');
      setRebalanceDate('');
    } catch (err) {
      alert('Erreur lors du rééquilibrage');
    } finally {
      setLoading(false);
    }
  };

  const createNewTransaction = async () => {
    // Open transaction creation modal
    const etfSymbol = prompt('Symbole ETF (ex: SPY):');
    if (!etfSymbol) return;
    
    const quantity = parseFloat(prompt('Quantité:') || '0');
    if (quantity <= 0) {
      alert('Quantité invalide');
      return;
    }
    
    const price = parseFloat(prompt('Prix par part:') || '0');
    if (price <= 0) {
      alert('Prix invalide');
      return;
    }
    
    try {
      // Try portfolio management API first
      const response = await fetch(`/api/v1/portfolio-management/portfolios/${selectedPortfolio}/positions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          etf_isin: etfSymbol, // TODO: Convert symbol to ISIN
          etf_symbol: etfSymbol,
          quantity,
          price,
          fees: 0
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          alert('Transaction créée avec succès!');
          await loadPortfolioData(selectedPortfolio);
          return;
        }
      }
      
      // Fallback to legacy API
      await portfolioAPI.createTransaction({
        portfolio_id: selectedPortfolio,
        etf_isin: etfSymbol, // TODO: Convert symbol to ISIN
        transaction_type: 'BUY',
        quantity,
        price,
        fees: 0
      });
      
      alert('Transaction créée avec succès!');
      await loadPortfolioData(selectedPortfolio);
    } catch (error: any) {
      console.error('Erreur création transaction:', error);
      alert('Erreur lors de la création de la transaction: ' + (error.message || 'Erreur inconnue'));
    }
  };

  const formatCurrency = (value: number) => {
    return value.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number) => {
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  if (loading && positions.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du portfolio...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-red-800 font-medium">Erreur</h3>
              <p className="text-red-600">{error}</p>
              <button 
                onClick={loadPortfolios}
                className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Réessayer
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">💼 Mon Portfolio</h1>
          <p className="text-gray-600 mt-2">
            Gérez et suivez vos investissements en temps réel
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {portfolios.length > 1 && (
            <select
              value={selectedPortfolio}
              onChange={(e) => setSelectedPortfolio(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              {portfolios.map(portfolio => (
                <option key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </option>
              ))}
            </select>
          )}
          <button
            onClick={refreshPortfolio}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <span>🔄</span>
            )}
            Actualiser
          </button>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Valeur totale</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary.total_value)}
              </p>
            </div>
            <div className="text-3xl">💰</div>
          </div>
          <div className={`mt-2 text-sm ${getPerformanceColor(summary.day_change)}`}>
            {formatPercentage(summary.day_change_percent)} aujourd'hui
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Gain/Perte total</p>
              <p className={`text-2xl font-bold ${getPerformanceColor(summary.total_gain_loss)}`}>
                {formatCurrency(summary.total_gain_loss)}
              </p>
            </div>
            <div className="text-3xl">
              {summary.total_gain_loss >= 0 ? '📈' : '📉'}
            </div>
          </div>
          <div className={`mt-2 text-sm ${getPerformanceColor(summary.total_gain_loss_percent)}`}>
            {formatPercentage(summary.total_gain_loss_percent)}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Liquidités</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary.cash_balance)}
              </p>
            </div>
            <div className="text-3xl">💵</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Disponible pour investir
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Positions</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.positions_count}
              </p>
            </div>
            <div className="text-3xl">🎯</div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            ETFs en portefeuille
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 Vue d'ensemble
            </button>
            <button
              onClick={() => setActiveTab('positions')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'positions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💼 Positions ({positions.length})
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'transactions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📋 Transactions
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📈 Analyse
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Portfolio Allocation */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🥧 Répartition du portefeuille</h3>
                {positions.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">📭</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune position</h3>
                    <p className="text-gray-500">Votre portefeuille est vide. Commencez par ajouter des ETFs.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      {positions.map(position => {
                        const marketValue = position.market_value || (position.quantity * position.average_price);
                        const allocation = summary.total_value > 0 ? (marketValue / summary.total_value) * 100 : 0;
                        return (
                          <div key={position.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center space-x-3">
                              <div className="font-medium text-gray-900">{position.symbol || position.etf_isin}</div>
                              <div className="text-sm text-gray-600">{position.name || 'ETF'}</div>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">{allocation.toFixed(1)}%</div>
                              <div className="text-sm text-gray-600">{formatCurrency(marketValue)}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">Métriques de performance</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Rendement total:</span>
                          <span className={`font-medium ${getPerformanceColor(summary.total_gain_loss)}`}>
                            {formatPercentage(summary.total_gain_loss_percent)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Nombre de positions:</span>
                          <span className="font-medium">{positions.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Allocation en liquidités:</span>
                          <span className="font-medium">
                            {summary.total_value > 0 ? ((summary.cash_balance / summary.total_value) * 100).toFixed(1) : 0}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Actions rapides</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">💫 Rééquilibrage automatique</h4>
                    <p className="text-sm text-blue-700 mb-3">
                      Programmez un rééquilibrage de votre portefeuille
                    </p>
                    <div className="space-y-2">
                      <input
                        type="date"
                        value={rebalanceDate}
                        onChange={(e) => setRebalanceDate(e.target.value)}
                        className="w-full px-3 py-2 border border-blue-300 rounded text-sm"
                        min={new Date().toISOString().split('T')[0]}
                      />
                      <button
                        onClick={handleRebalance}
                        disabled={!rebalanceDate || loading}
                        className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                      >
                        Programmer
                      </button>
                    </div>
                  </div>

                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-2">📊 Analyse de performance</h4>
                    <p className="text-sm text-green-700 mb-3">
                      Analysez la performance de vos investissements
                    </p>
                    <button
                      onClick={() => setActiveTab('analytics')}
                      className="w-full px-3 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                    >
                      Voir l'analyse
                    </button>
                  </div>

                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h4 className="font-medium text-purple-900 mb-2">🎯 Nouvelle transaction</h4>
                    <p className="text-sm text-purple-700 mb-3">
                      Ajoutez une nouvelle transaction à votre portefeuille
                    </p>
                    <button 
                      onClick={createNewTransaction}
                      className="w-full px-3 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
                    >
                      Créer une transaction
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'positions' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">💼 Vos positions actuelles</h3>
              
              {positions.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📭</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune position</h3>
                  <p className="text-gray-500">Votre portefeuille est vide. Commencez par ajouter des ETFs.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ETF
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantité
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Prix moyen
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Prix actuel
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Valeur de marché
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Gain/Perte
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date d'ajout
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {positions.map((position) => {
                        const marketValue = position.market_value || (position.quantity * position.average_price);
                        const gainLoss = position.unrealized_gain_loss || 0;
                        const gainLossPercent = position.unrealized_gain_loss_percent || 0;
                        
                        return (
                          <tr key={position.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <div className="font-medium text-gray-900">{position.symbol || position.etf_isin}</div>
                                <div className="text-sm text-gray-500">{position.name || 'ETF'}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {position.quantity}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(position.average_price)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {position.current_price ? formatCurrency(position.current_price) : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {formatCurrency(marketValue)}
                            </td>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getPerformanceColor(gainLoss)}`}>
                              {formatCurrency(gainLoss)}
                              {gainLossPercent !== 0 && (
                                <div className="text-xs">
                                  {formatPercentage(gainLossPercent)}
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(position.created_at).toLocaleDateString('fr-FR')}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'transactions' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">📋 Historique des transactions</h3>
                <button 
                  onClick={createNewTransaction}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  + Nouvelle transaction
                </button>
              </div>
              
              {transactions.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📋</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune transaction</h3>
                  <p className="text-gray-500">Aucune transaction enregistrée pour ce portefeuille.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ETF
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantité
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Prix
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Frais
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {transactions.map((transaction) => (
                        <tr key={transaction.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(transaction.created_at).toLocaleDateString('fr-FR')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              transaction.transaction_type === 'BUY' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {transaction.transaction_type === 'BUY' ? '📈 ACHAT' : '📉 VENTE'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {transaction.etf_isin}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {transaction.quantity}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(transaction.price)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatCurrency(transaction.fees)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(transaction.total_amount || (transaction.quantity * transaction.price + transaction.fees))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">📈 Analyse de performance</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-medium text-gray-900 mb-4">📊 Métriques de performance</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Rendement total:</span>
                      <span className={`font-medium ${getPerformanceColor(summary.total_gain_loss)}`}>
                        {formatPercentage(summary.total_gain_loss_percent)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Valeur du portefeuille:</span>
                      <span className="font-medium text-gray-900">{formatCurrency(summary.total_value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Coût total:</span>
                      <span className="font-medium text-gray-900">{formatCurrency(summary.total_cost)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Liquidités:</span>
                      <span className="font-medium text-gray-900">{formatCurrency(summary.cash_balance)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Nombre de positions:</span>
                      <span className="font-medium text-gray-900">{positions.length}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-medium text-gray-900 mb-4">🎯 Répartition des investissements</h4>
                  <div className="space-y-3">
                    {positions.length === 0 ? (
                      <p className="text-gray-500 text-sm">Aucune position à analyser</p>
                    ) : (
                      positions.slice(0, 5).map(position => {
                        const marketValue = position.market_value || (position.quantity * position.average_price);
                        const allocation = summary.total_value > 0 ? (marketValue / summary.total_value) * 100 : 0;
                        
                        return (
                          <div key={position.id} className="flex justify-between items-center">
                            <span className="text-sm text-gray-700">{position.symbol || position.etf_isin}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium">{allocation.toFixed(1)}%</span>
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${Math.min(allocation, 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 className="font-medium text-blue-900 mb-3">💡 Recommandations</h4>
                <div className="space-y-2 text-sm text-blue-800">
                  {summary.total_gain_loss >= 0 ? (
                    <p>• Votre portefeuille performe bien avec un rendement de +{summary.total_gain_loss_percent.toFixed(1)}%</p>
                  ) : (
                    <p>• Votre portefeuille est en perte de {summary.total_gain_loss_percent.toFixed(1)}%. Considérez une réévaluation de votre stratégie.</p>
                  )}
                  
                  {positions.length === 0 && (
                    <p>• Commencez par ajouter des ETFs à votre portefeuille pour diversifier vos investissements</p>
                  )}
                  
                  {positions.length > 0 && positions.length < 3 && (
                    <p>• Considérez diversifier votre portefeuille en ajoutant plus d'ETFs dans différents secteurs</p>
                  )}
                  
                  {summary.cash_balance > summary.total_value * 0.2 && (
                    <p>• Vous avez beaucoup de liquidités ({((summary.cash_balance / summary.total_value) * 100).toFixed(1)}%). Considérez les investir.</p>
                  )}
                  
                  <p>• Planifiez un rééquilibrage régulier pour maintenir votre allocation cible</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Portfolio;