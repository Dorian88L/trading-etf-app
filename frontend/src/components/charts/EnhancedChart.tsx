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

      // Récupérer les données historiques réelles depuis la nouvelle API
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8443';
      
      // Mapper le timeframe vers la période d'API
      const periodMap: { [key: string]: string } = {
        '1H': '1d',
        '4H': '5d', 
        '1D': '1mo',
        '1W': '3mo',
        '1M': '1y'
      };
      
      const period = periodMap[timeframe] || '1mo';
      
      try {
        const response = await fetch(`${apiUrl}/api/v1/historical/etf/${symbol}/historical?period=${period}&include_indicators=true`);

        if (response.ok) {
          const data = await response.json();
          
          if (data.historical_data && data.historical_data.length > 0) {
            // Convertir les données au format attendu
            const formattedData: MarketData[] = data.historical_data.map((point: any) => ({
              date: new Date(point.timestamp).toISOString().split('T')[0],
              open: point.open_price,
              high: point.high_price,
              low: point.low_price,
              close: point.close_price,
              volume: point.volume
            }));
            
            setMarketData(formattedData);
            
            // Convertir les indicateurs techniques s'ils sont disponibles
            if (data.technical_indicators) {
              const convertedIndicators = convertApiIndicators(data.technical_indicators, formattedData.length);
              setIndicators(convertedIndicators);
            } else {
              // Calculer les indicateurs de base localement
              const basicIndicators = calculateBasicIndicators(formattedData);
              setIndicators(basicIndicators);
            }
            
            console.log(`✅ Chargé ${formattedData.length} points de données pour ${symbol}`);
            return;
          }
        }
        
        throw new Error(`Pas de données disponibles pour ${symbol}`);
        
      } catch (apiError) {
        console.error('Erreur API:', apiError);
        setError(`Impossible de charger les données pour ${symbol}. Vérifiez que le symbole est correct.`);
        setMarketData([]);
        setIndicators(null);
      }

    } catch (err: any) {
      console.error('Erreur chargement données graphique:', err);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const convertApiIndicators = (apiIndicators: any, dataLength: number): TechnicalIndicators => {
    // Créer des arrays avec la valeur de l'indicateur répétée
    const createArray = (value: number | null, length: number) => {
      if (value === null || value === undefined) return new Array(length).fill(0);
      return new Array(length).fill(value);
    };

    return {
      sma20: createArray(apiIndicators.sma_20, dataLength),
      sma50: createArray(apiIndicators.sma_50, dataLength),
      sma200: createArray(apiIndicators.sma_200, dataLength),
      ema20: createArray(apiIndicators.ema_20, dataLength),
      rsi: createArray(apiIndicators.rsi, dataLength),
      macd: createArray(apiIndicators.macd, dataLength),
      macdSignal: createArray(apiIndicators.macd_signal, dataLength),
      macdHistogram: createArray(apiIndicators.macd_histogram, dataLength),
      bbUpper: createArray(apiIndicators.bb_upper, dataLength),
      bbLower: createArray(apiIndicators.bb_lower, dataLength),
      bbMiddle: createArray(apiIndicators.bb_middle, dataLength),
      atr: createArray(apiIndicators.atr, dataLength),
      obv: createArray(apiIndicators.obv, dataLength),
      vwap: createArray(apiIndicators.vwap, dataLength),
      stochK: createArray(apiIndicators.stoch_k, dataLength),
      stochD: createArray(apiIndicators.stoch_d, dataLength),
      williams: createArray(apiIndicators.williams_r, dataLength),
      cci: new Array(dataLength).fill(0) // CCI pas encore implémenté dans l'API
    };
  };

  const calculateBasicIndicators = (data: MarketData[]): TechnicalIndicators => {
    const closes = data.map(d => d.close);
    const length = data.length;
    
    // Calculs simplifiés des moyennes mobiles
    const sma20 = calculateSMA(closes, 20);
    const sma50 = calculateSMA(closes, 50);
    const sma200 = calculateSMA(closes, 200);
    
    return {
      sma20,
      sma50,
      sma200,
      ema20: calculateEMA(closes, 20),
      rsi: new Array(length).fill(50), // RSI neutre par défaut
      macd: new Array(length).fill(0),
      macdSignal: new Array(length).fill(0),
      macdHistogram: new Array(length).fill(0),
      bbUpper: closes.map(c => c * 1.02),
      bbLower: closes.map(c => c * 0.98),
      bbMiddle: sma20,
      atr: new Array(length).fill(2),
      obv: new Array(length).fill(0),
      vwap: closes, // VWAP simplifié = close
      stochK: new Array(length).fill(50),
      stochD: new Array(length).fill(50),
      williams: new Array(length).fill(-50),
      cci: new Array(length).fill(0)
    };
  };

  const calculateSMA = (prices: number[], period: number): number[] => {
    const sma = [];
    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1) {
        sma.push(prices[i]);
      } else {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        sma.push(sum / period);
      }
    }
    return sma;
  };

  const calculateEMA = (prices: number[], period: number): number[] => {
    const ema = [];
    const multiplier = 2 / (period + 1);
    
    ema[0] = prices[0];
    
    for (let i = 1; i < prices.length; i++) {
      ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier));
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