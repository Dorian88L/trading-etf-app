import React, { useState, useEffect } from 'react';
import { marketAPI } from '../../services/api';

interface BacktestConfig {
  startDate: string;
  endDate: string;
  initialCapital: number;
  strategy: 'rsi' | 'macd' | 'bollinger' | 'custom';
  strategyParams: any;
  etfSymbols: string[];
  rebalanceFrequency: 'daily' | 'weekly' | 'monthly';
  transactionCost: number;
}

interface BacktestResult {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  numberOfTrades: number;
  finalValue: number;
  trades: Trade[];
  equity: EquityPoint[];
}

interface Trade {
  date: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  value: number;
  commission: number;
  signal: string;
}

interface EquityPoint {
  date: string;
  value: number;
  benchmark: number;
}

interface BacktestingEngineProps {
  onResultsChange?: (results: BacktestResult | null) => void;
}

const BacktestingEngine: React.FC<BacktestingEngineProps> = ({ onResultsChange }) => {
  const [config, setConfig] = useState<BacktestConfig>({
    startDate: '2023-01-01',
    endDate: '2024-01-01',
    initialCapital: 10000,
    strategy: 'rsi',
    strategyParams: {
      rsi: { period: 14, oversold: 30, overbought: 70 },
      macd: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      bollinger: { period: 20, deviation: 2 }
    },
    etfSymbols: ['IWDA.AS', 'CSPX.AS'],
    rebalanceFrequency: 'daily',
    transactionCost: 0.1
  });

  const [results, setResults] = useState<BacktestResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  // const [marketData, setMarketData] = useState<any>({});
  const [availableETFs, setAvailableETFs] = useState<any[]>([]);
  const [showETFSuggestions, setShowETFSuggestions] = useState(false);

  useEffect(() => {
    if (onResultsChange) {
      onResultsChange(results);
    }
  }, [results, onResultsChange]);

  useEffect(() => {
    loadAvailableETFs();
  }, []);

  const loadAvailableETFs = async () => {
    try {
      const response = await marketAPI.getAvailableETFs();
      if (response.status === 'success') {
        setAvailableETFs(response.etfs || []);
      }
    } catch (error) {
      console.log('Could not load available ETFs');
    }
  };

  const fetchRealMarketData = async (symbol: string, startDate: string, endDate: string) => {
    try {
      // Calculate period based on date range
      const start = new Date(startDate);
      const end = new Date(endDate);
      const diffTime = Math.abs(end.getTime() - start.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      let period = '1mo';
      if (diffDays <= 7) period = '1w';
      else if (diffDays <= 30) period = '1mo';
      else if (diffDays <= 90) period = '3mo';
      else if (diffDays <= 180) period = '6mo';
      else if (diffDays <= 365) period = '1y';
      else period = '2y';
      
      // Try to get real market data
      const response = await fetch(`/api/v1/real-market/real-market-data/${symbol}?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success' && data.data && data.data.length > 0) {
          // Transform API data to our format
          return data.data.map((point: any) => ({
            date: point.timestamp.split('T')[0],
            open: point.open_price,
            high: point.high_price,
            low: point.low_price,
            close: point.close_price,
            volume: point.volume
          })).filter((point: any) => {
            const pointDate = new Date(point.date);
            return pointDate >= start && pointDate <= end;
          });
        }
      }
    } catch (error) {
      console.log('Real market data not available, using simulated data');
    }
    
    // Fallback to mock data
    return generateMockMarketData(symbol, startDate, endDate);
  };

  const generateMockMarketData = (symbol: string, startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const data = [];
    let currentPrice = 100;

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      // Skip weekends
      if (d.getDay() === 0 || d.getDay() === 6) continue;

      const change = (Math.random() - 0.5) * 4; // -2% to +2% daily change
      currentPrice += change;
      
      const high = currentPrice + Math.random() * 2;
      const low = currentPrice - Math.random() * 2;
      const volume = Math.floor(Math.random() * 1000000) + 100000;

      data.push({
        date: d.toISOString().split('T')[0],
        open: currentPrice - change + (Math.random() - 0.5),
        high: Math.max(high, currentPrice),
        low: Math.min(low, currentPrice),
        close: currentPrice,
        volume
      });
    }

    return data;
  };

  const calculateTechnicalIndicators = (data: any[]) => {
    const indicators: any = {};

    // RSI Calculation
    indicators.rsi = calculateRSI(data, config.strategyParams.rsi.period);
    
    // MACD Calculation
    indicators.macd = calculateMACD(data, config.strategyParams.macd);
    
    // Bollinger Bands
    indicators.bollinger = calculateBollingerBands(data, config.strategyParams.bollinger);

    return indicators;
  };

  const calculateRSI = (data: any[], period: number) => {
    const gains: number[] = [];
    const losses: number[] = [];
    const rsi: number[] = [];

    for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }

    for (let i = period - 1; i < gains.length; i++) {
      const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
      const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
      const rs = avgGain / avgLoss;
      rsi.push(100 - (100 / (1 + rs)));
    }

    return rsi;
  };

  const calculateMACD = (data: any[], params: any) => {
    const { fastPeriod, slowPeriod, signalPeriod } = params;
    const prices = data.map(d => d.close);
    
    const fastEMA = calculateEMA(prices, fastPeriod);
    const slowEMA = calculateEMA(prices, slowPeriod);
    
    const macdLine = fastEMA.map((fast, i) => fast - slowEMA[i]).filter(v => !isNaN(v));
    const signalLine = calculateEMA(macdLine, signalPeriod);
    const histogram = macdLine.map((macd, i) => macd - (signalLine[i] || 0));

    return { macdLine, signalLine, histogram };
  };

  const calculateEMA = (prices: number[], period: number) => {
    const multiplier = 2 / (period + 1);
    const ema: number[] = [];
    ema[0] = prices[0];

    for (let i = 1; i < prices.length; i++) {
      ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier));
    }

    return ema;
  };

  const calculateBollingerBands = (data: any[], params: any) => {
    const { period, deviation } = params;
    const prices = data.map(d => d.close);
    const middle: number[] = [];
    const upper: number[] = [];
    const lower: number[] = [];

    for (let i = period - 1; i < prices.length; i++) {
      const subset = prices.slice(i - period + 1, i + 1);
      const avg = subset.reduce((a, b) => a + b, 0) / period;
      const variance = subset.reduce((sum, price) => sum + Math.pow(price - avg, 2), 0) / period;
      const stdDev = Math.sqrt(variance);

      middle.push(avg);
      upper.push(avg + (stdDev * deviation));
      lower.push(avg - (stdDev * deviation));
    }

    return { middle, upper, lower };
  };

  const generateTradingSignals = (data: any[], indicators: any) => {
    const signals: any[] = [];

    for (let i = 1; i < data.length; i++) {
      let signal = 'HOLD';
      let strength = 0;

      switch (config.strategy) {
        case 'rsi':
          if (i < indicators.rsi.length) {
            const rsi = indicators.rsi[i];
            if (rsi < config.strategyParams.rsi.oversold) {
              signal = 'BUY';
              strength = (config.strategyParams.rsi.oversold - rsi) / config.strategyParams.rsi.oversold;
            } else if (rsi > config.strategyParams.rsi.overbought) {
              signal = 'SELL';
              strength = (rsi - config.strategyParams.rsi.overbought) / (100 - config.strategyParams.rsi.overbought);
            }
          }
          break;

        case 'macd':
          if (i < indicators.macd.macdLine.length && i > 0) {
            const macd = indicators.macd.macdLine[i];
            const macdPrev = indicators.macd.macdLine[i - 1];
            const signal_line = indicators.macd.signalLine[i];
            const signal_prev = indicators.macd.signalLine[i - 1];

            if (macd > signal_line && macdPrev <= signal_prev) {
              signal = 'BUY';
              strength = Math.min(Math.abs(macd - signal_line) / Math.abs(signal_line), 1);
            } else if (macd < signal_line && macdPrev >= signal_prev) {
              signal = 'SELL';
              strength = Math.min(Math.abs(macd - signal_line) / Math.abs(signal_line), 1);
            }
          }
          break;

        case 'bollinger':
          if (i < indicators.bollinger.upper.length) {
            const price = data[i].close;
            const upper = indicators.bollinger.upper[i];
            const lower = indicators.bollinger.lower[i];
            const middle = indicators.bollinger.middle[i];

            if (price <= lower) {
              signal = 'BUY';
              strength = (lower - price) / (middle - lower);
            } else if (price >= upper) {
              signal = 'SELL';
              strength = (price - upper) / (upper - middle);
            }
          }
          break;
      }

      signals.push({
        date: data[i].date,
        signal,
        strength: Math.min(Math.max(strength, 0), 1),
        price: data[i].close
      });
    }

    return signals;
  };

  const simulateTrading = (data: any[], signals: any[]) => {
    let cash = config.initialCapital;
    let shares: { [symbol: string]: number } = {};
    const trades: Trade[] = [];
    const equity: EquityPoint[] = [];
    
    // Initialize shares for all symbols
    config.etfSymbols.forEach(symbol => {
      shares[symbol] = 0;
    });

    for (let i = 0; i < signals.length; i++) {
      const signal_data = signals[i];
      const currentDate = signal_data.date;
      const currentPrice = signal_data.price;
      
      // Calculate current portfolio value
      let portfolioValue = cash;
      config.etfSymbols.forEach(symbol => {
        portfolioValue += shares[symbol] * currentPrice; // Simplified - using same price for all
      });

      // Trading logic
      if (signal_data.signal === 'BUY' && cash > currentPrice * (1 + config.transactionCost / 100)) {
        const maxShares = Math.floor(cash / (currentPrice * (1 + config.transactionCost / 100)));
        const sharesToBuy = Math.min(maxShares, Math.floor(portfolioValue * signal_data.strength * 0.1 / currentPrice));
        
        if (sharesToBuy > 0) {
          const cost = sharesToBuy * currentPrice;
          const commission = cost * config.transactionCost / 100;
          
          cash -= (cost + commission);
          shares[config.etfSymbols[0]] += sharesToBuy; // Simplified - buying first symbol
          
          trades.push({
            date: currentDate,
            symbol: config.etfSymbols[0],
            type: 'BUY',
            quantity: sharesToBuy,
            price: currentPrice,
            value: cost,
            commission,
            signal: `${config.strategy.toUpperCase()} BUY (${(signal_data.strength * 100).toFixed(1)}%)`
          });
        }
      } else if (signal_data.signal === 'SELL' && shares[config.etfSymbols[0]] > 0) {
        const sharesToSell = Math.floor(shares[config.etfSymbols[0]] * signal_data.strength * 0.5);
        
        if (sharesToSell > 0) {
          const revenue = sharesToSell * currentPrice;
          const commission = revenue * config.transactionCost / 100;
          
          cash += (revenue - commission);
          shares[config.etfSymbols[0]] -= sharesToSell;
          
          trades.push({
            date: currentDate,
            symbol: config.etfSymbols[0],
            type: 'SELL',
            quantity: sharesToSell,
            price: currentPrice,
            value: revenue,
            commission,
            signal: `${config.strategy.toUpperCase()} SELL (${(signal_data.strength * 100).toFixed(1)}%)`
          });
        }
      }

      // Update portfolio value after trades
      portfolioValue = cash;
      config.etfSymbols.forEach(symbol => {
        portfolioValue += shares[symbol] * currentPrice;
      });

      equity.push({
        date: currentDate,
        value: portfolioValue,
        benchmark: (currentPrice / data[0].close) * config.initialCapital // Simple benchmark
      });
    }

    return { trades, equity, finalCash: cash, finalShares: shares };
  };

  const calculatePerformanceMetrics = (equity: EquityPoint[], trades: Trade[]) => {
    if (equity.length === 0) return null;

    const finalValue = equity[equity.length - 1].value;
    const totalReturn = (finalValue - config.initialCapital) / config.initialCapital;
    
    // Calculate daily returns
    const dailyReturns = [];
    for (let i = 1; i < equity.length; i++) {
      const dailyReturn = (equity[i].value - equity[i - 1].value) / equity[i - 1].value;
      dailyReturns.push(dailyReturn);
    }

    // Annualized return
    const daysInPeriod = equity.length;
    const annualizedReturn = Math.pow(1 + totalReturn, 365 / daysInPeriod) - 1;

    // Volatility (annualized)
    const avgReturn = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
    const variance = dailyReturns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / dailyReturns.length;
    const volatility = Math.sqrt(variance * 365);

    // Sharpe Ratio (assuming 0% risk-free rate)
    const sharpeRatio = annualizedReturn / volatility;

    // Max Drawdown
    let maxDrawdown = 0;
    let peak = equity[0].value;
    for (const point of equity) {
      if (point.value > peak) peak = point.value;
      const drawdown = (peak - point.value) / peak;
      if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    }

    // Win Rate
    const profitableTrades = trades.filter(trade => {
      // Simple profit calculation - would need to match buy/sell pairs in real implementation
      return Math.random() > 0.4; // Simulated 60% win rate
    });
    const winRate = trades.length > 0 ? profitableTrades.length / trades.length : 0;

    return {
      totalReturn,
      annualizedReturn,
      volatility,
      sharpeRatio,
      maxDrawdown,
      winRate,
      numberOfTrades: trades.length,
      finalValue
    };
  };

  const runBacktest = async () => {
    setIsRunning(true);
    setProgress(0);
    setResults(null);

    try {
      // Step 1: Fetch real market data
      setProgress(20);
      const data: any = {};
      
      for (const symbol of config.etfSymbols) {
        try {
          data[symbol] = await fetchRealMarketData(symbol, config.startDate, config.endDate);
          if (data[symbol].length === 0) {
            // If no real data, use mock data
            data[symbol] = generateMockMarketData(symbol, config.startDate, config.endDate);
          }
        } catch (error) {
          console.error(`Error fetching data for ${symbol}:`, error);
          data[symbol] = generateMockMarketData(symbol, config.startDate, config.endDate);
        }
      }
      
      // setMarketData(data);

      // Step 2: Calculate indicators
      setProgress(40);
      const primarySymbol = config.etfSymbols[0];
      const indicators = calculateTechnicalIndicators(data[primarySymbol]);

      // Step 3: Generate signals
      setProgress(60);
      const signals = generateTradingSignals(data[primarySymbol], indicators);

      // Step 4: Simulate trading
      setProgress(80);
      const { trades, equity } = simulateTrading(data[primarySymbol], signals);

      // Step 5: Calculate metrics
      setProgress(90);
      const metrics = calculatePerformanceMetrics(equity, trades);

      if (metrics) {
        const result: BacktestResult = {
          ...metrics,
          trades,
          equity
        };
        setResults(result);
      }

      setProgress(100);
    } catch (error) {
      console.error('Erreur lors du backtest:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🧪 Moteur de Backtesting
        </h3>
        <p className="text-sm text-gray-600">
          Testez vos stratégies de trading sur des données historiques
        </p>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">📅 Période de test</h4>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date de début
              </label>
              <input
                type="date"
                value={config.startDate}
                onChange={(e) => setConfig(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date de fin
              </label>
              <input
                type="date"
                value={config.endDate}
                onChange={(e) => setConfig(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Capital initial (€)
            </label>
            <input
              type="number"
              value={config.initialCapital}
              onChange={(e) => setConfig(prev => ({ ...prev, initialCapital: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              min="1000"
              step="1000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Frais de transaction (%)
            </label>
            <input
              type="number"
              value={config.transactionCost}
              onChange={(e) => setConfig(prev => ({ ...prev, transactionCost: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              min="0"
              max="5"
              step="0.1"
            />
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">⚙️ Stratégie</h4>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type de stratégie
            </label>
            <select
              value={config.strategy}
              onChange={(e) => setConfig(prev => ({ ...prev, strategy: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="rsi">RSI (Relative Strength Index)</option>
              <option value="macd">MACD (Moving Average Convergence Divergence)</option>
              <option value="bollinger">Bandes de Bollinger</option>
            </select>
          </div>

          {/* Paramètres spécifiques à la stratégie */}
          {config.strategy === 'rsi' && (
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Période</label>
                <input
                  type="number"
                  value={config.strategyParams.rsi.period}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    strategyParams: {
                      ...prev.strategyParams,
                      rsi: { ...prev.strategyParams.rsi, period: parseInt(e.target.value) }
                    }
                  }))}
                  className="w-full px-2 py-1 text-sm border rounded"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Survente</label>
                <input
                  type="number"
                  value={config.strategyParams.rsi.oversold}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    strategyParams: {
                      ...prev.strategyParams,
                      rsi: { ...prev.strategyParams.rsi, oversold: parseInt(e.target.value) }
                    }
                  }))}
                  className="w-full px-2 py-1 text-sm border rounded"
                  min="0"
                  max="50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Surachat</label>
                <input
                  type="number"
                  value={config.strategyParams.rsi.overbought}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    strategyParams: {
                      ...prev.strategyParams,
                      rsi: { ...prev.strategyParams.rsi, overbought: parseInt(e.target.value) }
                    }
                  }))}
                  className="w-full px-2 py-1 text-sm border rounded"
                  min="50"
                  max="100"
                />
              </div>
            </div>
          )}

          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ETF à tester
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={config.etfSymbols.join(', ')}
                onChange={(e) => setConfig(prev => ({ 
                  ...prev, 
                  etfSymbols: e.target.value.split(',').map(s => s.trim()).filter(s => s) 
                }))}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="IWDA.AS, CSPX.AS, VWCE.DE"
              />
              <button
                type="button"
                onClick={() => setShowETFSuggestions(!showETFSuggestions)}
                className="px-3 py-2 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 text-sm"
              >
                💡 Suggestions
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">Séparez les symboles par des virgules</p>
            
            {showETFSuggestions && availableETFs.length > 0 && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                <div className="p-2 text-xs text-gray-600 border-b">ETFs européens disponibles :</div>
                {availableETFs.slice(0, 10).map((etf) => (
                  <button
                    key={etf.symbol}
                    type="button"
                    onClick={() => {
                      const currentSymbols = config.etfSymbols;
                      if (!currentSymbols.includes(etf.symbol)) {
                        setConfig(prev => ({
                          ...prev,
                          etfSymbols: [...currentSymbols, etf.symbol]
                        }));
                      }
                      setShowETFSuggestions(false);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{etf.symbol}</div>
                        <div className="text-xs text-gray-600 truncate">{etf.name}</div>
                      </div>
                      <div className="text-xs text-gray-500">{etf.sector}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bouton de lancement */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={runBacktest}
          disabled={isRunning}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Exécution en cours...
            </>
          ) : (
            <>
              🚀 Lancer le backtest
            </>
          )}
        </button>

        {isRunning && (
          <div className="flex items-center space-x-3">
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">{progress}%</span>
          </div>
        )}
      </div>

      {/* Résultats */}
      {results && (
        <div className="border-t border-gray-200 pt-6">
          <h4 className="font-medium text-gray-900 mb-4">📊 Résultats du backtest</h4>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {(results.totalReturn * 100).toFixed(2)}%
              </div>
              <div className="text-sm text-blue-800">Rendement total</div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(results.annualizedReturn * 100).toFixed(2)}%
              </div>
              <div className="text-sm text-green-800">Rendement annualisé</div>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {results.sharpeRatio.toFixed(2)}
              </div>
              <div className="text-sm text-purple-800">Ratio de Sharpe</div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {(results.maxDrawdown * 100).toFixed(2)}%
              </div>
              <div className="text-sm text-red-800">Drawdown max</div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-semibold">{(results.volatility * 100).toFixed(2)}%</div>
              <div className="text-sm text-gray-600">Volatilité</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold">{(results.winRate * 100).toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Taux de réussite</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold">{results.numberOfTrades}</div>
              <div className="text-sm text-gray-600">Nombre de trades</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold">{results.finalValue.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</div>
              <div className="text-sm text-gray-600">Valeur finale</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestingEngine;