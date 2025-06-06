import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
);

interface MarketDataPoint {
  timestamp: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
}

interface TechnicalIndicator {
  timestamp: string;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  bb_upper?: number;
  bb_lower?: number;
  bb_middle?: number;
}

interface AdvancedChartProps {
  data: MarketDataPoint[];
  indicators?: TechnicalIndicator[];
  etfName: string;
  chartType?: 'line' | 'candlestick' | 'volume';
  showIndicators?: boolean;
  height?: number;
}

const AdvancedChart: React.FC<AdvancedChartProps> = ({
  data,
  indicators,
  etfName,
  chartType = 'line',
  showIndicators = true,
  height = 400
}) => {
  const [selectedIndicators, setSelectedIndicators] = useState({
    sma20: true,
    sma50: true,
    rsi: false,
    macd: false,
    bollinger: false
  });

  // Préparer les données pour le graphique principal
  const chartData = {
    labels: data.map(d => new Date(d.timestamp)),
    datasets: [
      {
        label: `${etfName} - Prix`,
        data: data.map(d => d.close_price),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: chartType === 'line',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 5,
      },
      // SMA 20
      ...(selectedIndicators.sma20 && indicators ? [{
        label: 'SMA 20',
        data: indicators.map(i => i.sma_20),
        borderColor: '#f59e0b',
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        tension: 0.1,
      }] : []),
      // SMA 50
      ...(selectedIndicators.sma50 && indicators ? [{
        label: 'SMA 50',
        data: indicators.map(i => i.sma_50),
        borderColor: '#ef4444',
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderDash: [10, 5],
        pointRadius: 0,
        tension: 0.1,
      }] : []),
      // Bollinger Bands
      ...(selectedIndicators.bollinger && indicators ? [
        {
          label: 'BB Supérieure',
          data: indicators.map(i => i.bb_upper),
          borderColor: '#9ca3af',
          backgroundColor: 'rgba(156, 163, 175, 0.1)',
          borderWidth: 1,
          pointRadius: 0,
          fill: '+1',
        },
        {
          label: 'BB Inférieure',
          data: indicators.map(i => i.bb_lower),
          borderColor: '#9ca3af',
          backgroundColor: 'rgba(156, 163, 175, 0.1)',
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
        }
      ] : []),
    ]
  };

  // Données pour les graphiques des indicateurs
  const rsiData = selectedIndicators.rsi && indicators ? {
    labels: indicators.map(i => new Date(i.timestamp)),
    datasets: [{
      label: 'RSI',
      data: indicators.map(i => i.rsi),
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      borderWidth: 2,
      fill: true,
      pointRadius: 0,
    }]
  } : null;

  const volumeData = {
    labels: data.map(d => new Date(d.timestamp)),
    datasets: [{
      label: 'Volume',
      data: data.map(d => d.volume),
      backgroundColor: 'rgba(34, 197, 94, 0.6)',
      borderColor: '#22c55e',
      borderWidth: 1,
    }]
  };

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          boxWidth: 12,
          font: {
            size: 11
          }
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: function(context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'EUR'
              }).format(context.parsed.y);
            }
            return label;
          }
        }
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day',
          displayFormats: {
            day: 'dd/MM'
          }
        },
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 10
          }
        }
      },
      y: {
        beginAtZero: false,
        grid: {
          color: 'rgba(156, 163, 175, 0.3)',
        },
        ticks: {
          callback: function(value: any) {
            return new Intl.NumberFormat('fr-FR', {
              style: 'currency',
              currency: 'EUR',
              minimumFractionDigits: 2
            }).format(value);
          },
          font: {
            size: 10
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
  };

  const rsiOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        type: 'time',
        display: false,
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(156, 163, 175, 0.3)',
        },
        ticks: {
          font: {
            size: 10
          }
        }
      }
    },
  };

  const volumeOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        type: 'time',
        display: false,
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(156, 163, 175, 0.3)',
        },
        ticks: {
          callback: function(value: any) {
            return new Intl.NumberFormat('fr-FR', {
              notation: 'compact'
            }).format(value);
          },
          font: {
            size: 10
          }
        }
      }
    },
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* Header avec contrôles */}
      <div className="flex flex-wrap items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Analyse Technique - {etfName}
        </h3>
        
        {showIndicators && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedIndicators(prev => ({ ...prev, sma20: !prev.sma20 }))}
              className={`px-2 py-1 text-xs rounded ${
                selectedIndicators.sma20 
                  ? 'bg-yellow-100 text-yellow-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              SMA 20
            </button>
            <button
              onClick={() => setSelectedIndicators(prev => ({ ...prev, sma50: !prev.sma50 }))}
              className={`px-2 py-1 text-xs rounded ${
                selectedIndicators.sma50 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              SMA 50
            </button>
            <button
              onClick={() => setSelectedIndicators(prev => ({ ...prev, bollinger: !prev.bollinger }))}
              className={`px-2 py-1 text-xs rounded ${
                selectedIndicators.bollinger 
                  ? 'bg-gray-200 text-gray-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              Bollinger
            </button>
            <button
              onClick={() => setSelectedIndicators(prev => ({ ...prev, rsi: !prev.rsi }))}
              className={`px-2 py-1 text-xs rounded ${
                selectedIndicators.rsi 
                  ? 'bg-purple-100 text-purple-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              RSI
            </button>
          </div>
        )}
      </div>

      {/* Graphique principal */}
      <div style={{ height: `${height}px` }} className="mb-4">
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Graphique RSI */}
      {selectedIndicators.rsi && rsiData && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-700">RSI (14)</h4>
            <div className="flex gap-2 text-xs">
              <span className="text-red-600">Survente: &lt;30</span>
              <span className="text-green-600">Surachat: &gt;70</span>
            </div>
          </div>
          <div style={{ height: '120px' }}>
            <Line data={rsiData} options={rsiOptions} />
          </div>
          {/* Lignes de référence RSI */}
          <div className="relative">
            <div className="absolute inset-0 pointer-events-none">
              <div className="h-full border-l-2 border-red-300 border-dashed" style={{ left: '30%' }}></div>
              <div className="h-full border-l-2 border-green-300 border-dashed" style={{ left: '70%' }}></div>
            </div>
          </div>
        </div>
      )}

      {/* Graphique Volume */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Volume</h4>
        <div style={{ height: '100px' }}>
          <Bar data={volumeData} options={volumeOptions} />
        </div>
      </div>

      {/* Statistiques rapides */}
      {data.length > 0 && (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <div className="text-xs text-gray-500">Prix actuel</div>
            <div className="text-sm font-semibold text-gray-900">
              {new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'EUR'
              }).format(data[data.length - 1].close_price)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">Variation</div>
            <div className={`text-sm font-semibold ${
              data.length > 1 && data[data.length - 1].close_price > data[data.length - 2].close_price
                ? 'text-green-600' 
                : 'text-red-600'
            }`}>
              {data.length > 1 ? (
                `${((data[data.length - 1].close_price - data[data.length - 2].close_price) / data[data.length - 2].close_price * 100).toFixed(2)}%`
              ) : '0.00%'}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">Volume</div>
            <div className="text-sm font-semibold text-gray-900">
              {new Intl.NumberFormat('fr-FR', {
                notation: 'compact'
              }).format(data[data.length - 1].volume)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">Amplitude</div>
            <div className="text-sm font-semibold text-gray-900">
              {((data[data.length - 1].high_price - data[data.length - 1].low_price) / data[data.length - 1].low_price * 100).toFixed(2)}%
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedChart;