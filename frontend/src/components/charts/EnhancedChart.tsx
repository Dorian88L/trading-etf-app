import React, { useState, useEffect, useRef } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import { Chart, Line, Bar } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface MarketData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TechnicalIndicators {
  sma20: number[];
  sma50: number[];
  sma200: number[];
  ema20: number[];
  rsi: number[];
  macd: number[];
  macdSignal: number[];
  macdHistogram: number[];
  bbUpper: number[];
  bbLower: number[];
  bbMiddle: number[];
  atr: number[];
  obv: number[];
  vwap: number[];
  stochK: number[];
  stochD: number[];
  williams: number[];
  cci: number[];
}

interface EnhancedChartProps {
  symbol: string;
  timeframe?: '1H' | '4H' | '1D' | '1W' | '1M';
  height?: number;
}

const EnhancedChart: React.FC<EnhancedChartProps> = ({ 
  symbol, 
  timeframe = '1D', 
  height = 400 
}) => {
  const chartRef = useRef<any>(null);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [indicators, setIndicators] = useState<TechnicalIndicators | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['sma20', 'sma50', 'volume']);
  const [chartType, setChartType] = useState<'candlestick' | 'line' | 'area'>('line');

  const availableIndicators = [
    { id: 'sma20', name: 'SMA 20', color: '#3B82F6', type: 'overlay' },
    { id: 'sma50', name: 'SMA 50', color: '#EF4444', type: 'overlay' },
    { id: 'sma200', name: 'SMA 200', color: '#10B981', type: 'overlay' },
    { id: 'ema20', name: 'EMA 20', color: '#8B5CF6', type: 'overlay' },
    { id: 'bollinger', name: 'Bollinger Bands', color: '#F59E0B', type: 'overlay' },
    { id: 'vwap', name: 'VWAP', color: '#EC4899', type: 'overlay' },
    { id: 'rsi', name: 'RSI', color: '#6366F1', type: 'oscillator' },
    { id: 'macd', name: 'MACD', color: '#14B8A6', type: 'oscillator' },
    { id: 'stochastic', name: 'Stochastic', color: '#F97316', type: 'oscillator' },
    { id: 'williams', name: 'Williams %R', color: '#84CC16', type: 'oscillator' },
    { id: 'cci', name: 'CCI', color: '#06B6D4', type: 'oscillator' },
    { id: 'volume', name: 'Volume', color: '#64748B', type: 'volume' },
    { id: 'obv', name: 'OBV', color: '#DC2626', type: 'volume' }
  ];

  useEffect(() => {
    loadChartData();
  }, [symbol, timeframe]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      setError('');

      // Tentative de récupération des vraies données
      try {
        const response = await fetch(`/api/v1/market/historical/${symbol}?timeframe=${timeframe}&limit=100`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setMarketData(data.market_data || []);
          setIndicators(data.indicators || null);
          return;
        }
      } catch (apiError) {
        console.log('API non disponible, génération de données mockées');
      }

      // Fallback avec données mockées
      const mockData = generateMockData();
      setMarketData(mockData.data);
      setIndicators(mockData.indicators);

    } catch (err: any) {
      console.error('Erreur chargement données graphique:', err);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = () => {
    const days = 100;
    const basePrice = 100;
    const data: MarketData[] = [];
    const indicators: TechnicalIndicators = {
      sma20: [], sma50: [], sma200: [], ema20: [], rsi: [], macd: [], macdSignal: [],
      macdHistogram: [], bbUpper: [], bbLower: [], bbMiddle: [], atr: [], obv: [],
      vwap: [], stochK: [], stochD: [], williams: [], cci: []
    };

    let price = basePrice;
    let obvValue = 0;

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));

      // Simulation prix avec tendance et volatilité
      const trend = Math.sin(i / 20) * 0.5;
      const volatility = (Math.random() - 0.5) * 4;
      price = Math.max(price + trend + volatility, price * 0.95);

      const open = price + (Math.random() - 0.5) * 2;
      const high = Math.max(open, price) + Math.random() * 2;
      const low = Math.min(open, price) - Math.random() * 2;
      const close = low + Math.random() * (high - low);
      const volume = Math.floor(Math.random() * 2000000) + 500000;

      data.push({
        date: date.toISOString(),
        open,
        high,
        low,
        close,
        volume
      });

      // Calcul des indicateurs techniques
      if (i >= 19) {
        // SMA 20
        const sma20 = data.slice(i - 19, i + 1).reduce((sum, d) => sum + d.close, 0) / 20;
        indicators.sma20.push(sma20);
      } else {
        indicators.sma20.push(close);
      }

      if (i >= 49) {
        // SMA 50
        const sma50 = data.slice(i - 49, i + 1).reduce((sum, d) => sum + d.close, 0) / 50;
        indicators.sma50.push(sma50);
      } else {
        indicators.sma50.push(close);
      }

      if (i >= 199) {
        // SMA 200
        const sma200 = data.slice(i - 199, i + 1).reduce((sum, d) => sum + d.close, 0) / 200;
        indicators.sma200.push(sma200);
      } else {
        indicators.sma200.push(close);
      }

      // EMA 20
      if (i === 0) {
        indicators.ema20.push(close);
      } else {
        const multiplier = 2 / (20 + 1);
        const ema = (close - indicators.ema20[i - 1]) * multiplier + indicators.ema20[i - 1];
        indicators.ema20.push(ema);
      }

      // RSI
      if (i >= 14) {
        const gains = [];
        const losses = [];
        for (let j = i - 13; j <= i; j++) {
          const change = data[j].close - data[j - 1].close;
          if (change > 0) gains.push(change);
          else losses.push(Math.abs(change));
        }
        const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / gains.length : 0;
        const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / losses.length : 0;
        const rs = avgGain / (avgLoss || 1);
        const rsi = 100 - (100 / (1 + rs));
        indicators.rsi.push(rsi);
      } else {
        indicators.rsi.push(50);
      }

      // MACD
      if (i >= 25) {
        const ema12 = calculateEMA(data.slice(0, i + 1).map(d => d.close), 12);
        const ema26 = calculateEMA(data.slice(0, i + 1).map(d => d.close), 26);
        const macd = ema12[ema12.length - 1] - ema26[ema26.length - 1];
        indicators.macd.push(macd);
        
        // Signal line (EMA 9 of MACD)
        if (indicators.macd.length >= 9) {
          const signal = calculateEMA(indicators.macd.slice(-9), 9);
          indicators.macdSignal.push(signal[signal.length - 1]);
          indicators.macdHistogram.push(macd - signal[signal.length - 1]);
        } else {
          indicators.macdSignal.push(macd);
          indicators.macdHistogram.push(0);
        }
      } else {
        indicators.macd.push(0);
        indicators.macdSignal.push(0);
        indicators.macdHistogram.push(0);
      }

      // Bollinger Bands
      if (i >= 19) {
        const sma = indicators.sma20[indicators.sma20.length - 1];
        const prices = data.slice(i - 19, i + 1).map(d => d.close);
        const variance = prices.reduce((sum, price) => sum + Math.pow(price - sma, 2), 0) / 20;
        const stdDev = Math.sqrt(variance);
        indicators.bbUpper.push(sma + 2 * stdDev);
        indicators.bbLower.push(sma - 2 * stdDev);
        indicators.bbMiddle.push(sma);
      } else {
        indicators.bbUpper.push(close * 1.02);
        indicators.bbLower.push(close * 0.98);
        indicators.bbMiddle.push(close);
      }

      // ATR
      if (i > 0) {
        const tr = Math.max(
          high - low,
          Math.abs(high - data[i - 1].close),
          Math.abs(low - data[i - 1].close)
        );
        if (i >= 14) {
          const atr = data.slice(i - 13, i + 1).reduce((sum, d, idx) => {
            const prevClose = idx > 0 ? data[i - 13 + idx - 1].close : d.open;
            const tr = Math.max(d.high - d.low, Math.abs(d.high - prevClose), Math.abs(d.low - prevClose));
            return sum + tr;
          }, 0) / 14;
          indicators.atr.push(atr);
        } else {
          indicators.atr.push(tr);
        }
      } else {
        indicators.atr.push(1);
      }

      // OBV
      if (i > 0) {
        if (close > data[i - 1].close) {
          obvValue += volume;
        } else if (close < data[i - 1].close) {
          obvValue -= volume;
        }
      }
      indicators.obv.push(obvValue);

      // VWAP
      if (i === 0) {
        indicators.vwap.push(close);
      } else {
        const totalVolume = data.slice(0, i + 1).reduce((sum, d) => sum + d.volume, 0);
        const totalVolumePrice = data.slice(0, i + 1).reduce((sum, d) => sum + ((d.high + d.low + d.close) / 3) * d.volume, 0);
        indicators.vwap.push(totalVolumePrice / totalVolume);
      }

      // Stochastic
      if (i >= 13) {
        const highestHigh = Math.max(...data.slice(i - 13, i + 1).map(d => d.high));
        const lowestLow = Math.min(...data.slice(i - 13, i + 1).map(d => d.low));
        const stochK = ((close - lowestLow) / (highestHigh - lowestLow)) * 100;
        indicators.stochK.push(stochK);
        
        if (indicators.stochK.length >= 3) {
          const stochD = indicators.stochK.slice(-3).reduce((a, b) => a + b, 0) / 3;
          indicators.stochD.push(stochD);
        } else {
          indicators.stochD.push(stochK);
        }
      } else {
        indicators.stochK.push(50);
        indicators.stochD.push(50);
      }

      // Williams %R
      if (i >= 13) {
        const highestHigh = Math.max(...data.slice(i - 13, i + 1).map(d => d.high));
        const lowestLow = Math.min(...data.slice(i - 13, i + 1).map(d => d.low));
        const williams = ((highestHigh - close) / (highestHigh - lowestLow)) * -100;
        indicators.williams.push(williams);
      } else {
        indicators.williams.push(-50);
      }

      // CCI
      if (i >= 19) {
        const typicalPrices = data.slice(i - 19, i + 1).map(d => (d.high + d.low + d.close) / 3);
        const smaTP = typicalPrices.reduce((a, b) => a + b, 0) / 20;
        const meanDeviation = typicalPrices.reduce((sum, tp) => sum + Math.abs(tp - smaTP), 0) / 20;
        const cci = (((high + low + close) / 3) - smaTP) / (0.015 * meanDeviation);
        indicators.cci.push(cci);
      } else {
        indicators.cci.push(0);
      }

      price = close;
    }

    return { data, indicators };
  };

  const calculateEMA = (prices: number[], period: number): number[] => {
    const multiplier = 2 / (period + 1);
    const ema = [prices[0]];
    
    for (let i = 1; i < prices.length; i++) {
      ema.push((prices[i] - ema[i - 1]) * multiplier + ema[i - 1]);
    }
    
    return ema;
  };

  const getMainChartData = () => {
    if (!marketData.length) return null;

    const labels = marketData.map(d => new Date(d.date).toLocaleDateString());
    const datasets = [];

    // Prix de clôture
    datasets.push({
      label: 'Prix',
      data: marketData.map(d => d.close),
      borderColor: '#1F2937',
      backgroundColor: 'rgba(31, 41, 55, 0.1)',
      borderWidth: 2,
      fill: chartType === 'area',
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4,
    });

    // Indicateurs overlay
    if (indicators) {
      selectedIndicators.forEach(indicatorId => {
        const indicator = availableIndicators.find(i => i.id === indicatorId);
        if (!indicator || indicator.type !== 'overlay') return;

        switch (indicatorId) {
          case 'sma20':
            datasets.push({
              label: 'SMA 20',
              data: indicators.sma20,
              borderColor: indicator.color,
              borderWidth: 1,
              fill: false,
              pointRadius: 0,
            });
            break;
          case 'sma50':
            datasets.push({
              label: 'SMA 50',
              data: indicators.sma50,
              borderColor: indicator.color,
              borderWidth: 1,
              fill: false,
              pointRadius: 0,
            });
            break;
          case 'sma200':
            datasets.push({
              label: 'SMA 200',
              data: indicators.sma200,
              borderColor: indicator.color,
              borderWidth: 1,
              fill: false,
              pointRadius: 0,
            });
            break;
          case 'ema20':
            datasets.push({
              label: 'EMA 20',
              data: indicators.ema20,
              borderColor: indicator.color,
              borderWidth: 1,
              fill: false,
              pointRadius: 0,
            });
            break;
          case 'bollinger':
            datasets.push(
              {
                label: 'BB Upper',
                data: indicators.bbUpper,
                borderColor: indicator.color,
                backgroundColor: `${indicator.color}20`,
                borderWidth: 1,
                fill: '+1',
                pointRadius: 0,
              },
              {
                label: 'BB Lower',
                data: indicators.bbLower,
                borderColor: indicator.color,
                borderWidth: 1,
                fill: false,
                pointRadius: 0,
              }
            );
            break;
          case 'vwap':
            datasets.push({
              label: 'VWAP',
              data: indicators.vwap,
              borderColor: indicator.color,
              borderWidth: 2,
              borderDash: [5, 5],
              fill: false,
              pointRadius: 0,
            });
            break;
        }
      });
    }

    return { labels, datasets };
  };

  const getVolumeChartData = () => {
    if (!marketData.length || !selectedIndicators.includes('volume')) return null;

    const labels = marketData.map(d => new Date(d.date).toLocaleDateString());
    const datasets = [{
      label: 'Volume',
      data: marketData.map(d => d.volume),
      backgroundColor: marketData.map((d, i) => 
        i === 0 ? '#64748B' : d.close > marketData[i - 1].close ? '#10B981' : '#EF4444'
      ),
      borderWidth: 0,
    }];

    if (indicators && selectedIndicators.includes('obv')) {
      datasets.push({
        label: 'OBV',
        data: indicators.obv,
        type: 'line' as const,
        borderColor: '#DC2626',
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        borderWidth: 2,
        yAxisID: 'y1',
        pointRadius: 0,
      } as any);
    }

    return { labels, datasets };
  };

  const getOscillatorChartData = () => {
    if (!indicators) return null;

    const oscillatorIndicators = selectedIndicators.filter(id => 
      availableIndicators.find(i => i.id === id)?.type === 'oscillator'
    );

    if (oscillatorIndicators.length === 0) return null;

    const labels = marketData.map(d => new Date(d.date).toLocaleDateString());
    const datasets: any[] = [];

    oscillatorIndicators.forEach(indicatorId => {
      const indicator = availableIndicators.find(i => i.id === indicatorId);
      if (!indicator) return;

      switch (indicatorId) {
        case 'rsi':
          datasets.push({
            label: 'RSI',
            data: indicators.rsi,
            borderColor: indicator.color,
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
          } as any);
          break;
        case 'macd':
          datasets.push(
            {
              label: 'MACD',
              data: indicators.macd,
              borderColor: indicator.color,
              backgroundColor: 'rgba(20, 184, 166, 0.1)',
              borderWidth: 2,
              pointRadius: 0,
              type: 'line' as const,
            } as any,
            {
              label: 'Signal',
              data: indicators.macdSignal,
              borderColor: '#F59E0B',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              borderWidth: 1,
              pointRadius: 0,
              type: 'line' as const,
            } as any,
            {
              label: 'Histogram',
              data: indicators.macdHistogram,
              backgroundColor: indicators.macdHistogram.map(v => v >= 0 ? '#10B981' : '#EF4444'),
              borderWidth: 0,
              type: 'bar' as const,
            } as any
          );
          break;
        case 'stochastic':
          datasets.push(
            {
              label: 'Stoch %K',
              data: indicators.stochK,
              borderColor: indicator.color,
              backgroundColor: 'rgba(249, 115, 22, 0.1)',
              borderWidth: 2,
              pointRadius: 0,
            } as any,
            {
              label: 'Stoch %D',
              data: indicators.stochD,
              borderColor: '#DC2626',
              backgroundColor: 'rgba(220, 38, 38, 0.1)',
              borderWidth: 1,
              pointRadius: 0,
            } as any
          );
          break;
        case 'williams':
          datasets.push({
            label: 'Williams %R',
            data: indicators.williams,
            borderColor: indicator.color,
            backgroundColor: 'rgba(132, 204, 22, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
          } as any);
          break;
        case 'cci':
          datasets.push({
            label: 'CCI',
            data: indicators.cci,
            borderColor: indicator.color,
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
          } as any);
          break;
      }
    });

    return { labels, datasets };
  };

  const toggleIndicator = (indicatorId: string) => {
    setSelectedIndicators(prev => 
      prev.includes(indicatorId)
        ? prev.filter(id => id !== indicatorId)
        : [...prev, indicatorId]
    );
  };

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      x: {
        type: 'category',
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      y1: {
        type: 'linear',
        display: false,
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
      },
    },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du graphique...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  const mainChartData = getMainChartData();
  const volumeChartData = getVolumeChartData();
  const oscillatorChartData = getOscillatorChartData();

  return (
    <div className="space-y-4">
      {/* Contrôles */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Timeframe:</span>
            {['1H', '4H', '1D', '1W', '1M'].map(tf => (
              <button
                key={tf}
                onClick={() => {}}
                className={`px-3 py-1 text-sm rounded ${
                  timeframe === tf
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Type:</span>
            {[
              { id: 'line', name: 'Ligne' },
              { id: 'area', name: 'Aire' },
              { id: 'candlestick', name: 'Chandeliers' }
            ].map(type => (
              <button
                key={type.id}
                onClick={() => setChartType(type.id as any)}
                className={`px-3 py-1 text-sm rounded ${
                  chartType === type.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {type.name}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="text-sm font-medium text-gray-700 mb-2 block">Indicateurs:</span>
          <div className="flex flex-wrap gap-2">
            {availableIndicators.map(indicator => (
              <button
                key={indicator.id}
                onClick={() => toggleIndicator(indicator.id)}
                className={`px-3 py-1 text-sm rounded border ${
                  selectedIndicators.includes(indicator.id)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
                style={selectedIndicators.includes(indicator.id) ? {} : { borderColor: indicator.color }}
              >
                <span
                  className="inline-block w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: indicator.color }}
                ></span>
                {indicator.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Graphique principal */}
      {mainChartData && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {symbol} - {timeframe}
          </h3>
          <div style={{ height: height }}>
            <Line ref={chartRef} data={mainChartData} options={chartOptions} />
          </div>
        </div>
      )}

      {/* Graphique de volume */}
      {volumeChartData && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Volume</h3>
          <div style={{ height: 150 }}>
            <Bar 
              data={volumeChartData} 
              options={{
                ...chartOptions,
                scales: {
                  ...chartOptions.scales,
                  y1: {
                    ...chartOptions.scales.y1,
                    display: selectedIndicators.includes('obv'),
                  }
                }
              }} 
            />
          </div>
        </div>
      )}

      {/* Graphiques des oscillateurs */}
      {oscillatorChartData && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Oscillateurs</h3>
          <div style={{ height: 200 }}>
            <Line 
              data={oscillatorChartData} 
              options={{
                ...chartOptions,
                scales: {
                  ...chartOptions.scales,
                  y: {
                    ...chartOptions.scales.y,
                    beginAtZero: false,
                  }
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedChart;