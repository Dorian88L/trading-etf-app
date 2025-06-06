import React from 'react';
import { 
  ChartBarIcon, 
  TrendingUpIcon, 
  CurrencyDollarIcon,
  BellIcon 
} from '@heroicons/react/24/outline';

const Dashboard: React.FC = () => {
  // Mock data for demonstration
  const stats = [
    {
      name: 'Portfolio Value',
      value: '€125,430',
      change: '+2.1%',
      changeType: 'positive',
      icon: CurrencyDollarIcon,
    },
    {
      name: 'Active Signals',
      value: '12',
      change: '+3',
      changeType: 'positive',
      icon: TrendingUpIcon,
    },
    {
      name: 'Today P&L',
      value: '€1,250',
      change: '+0.8%',
      changeType: 'positive',
      icon: ChartBarIcon,
    },
    {
      name: 'Alerts',
      value: '5',
      change: 'New',
      changeType: 'neutral',
      icon: BellIcon,
    },
  ];

  const recentSignals = [
    {
      id: '1',
      etf: 'Lyxor CAC 40',
      isin: 'FR0010296061',
      signal: 'BUY',
      confidence: 85,
      price: '€52.30',
      time: '2h ago'
    },
    {
      id: '2',
      etf: 'iShares Core MSCI World',
      isin: 'IE00B4L5Y983',
      signal: 'SELL',
      confidence: 78,
      price: '€71.45',
      time: '4h ago'
    },
    {
      id: '3',
      etf: 'Xtrackers EURO STOXX 50',
      isin: 'LU0290358497',
      signal: 'HOLD',
      confidence: 65,
      price: '€45.20',
      time: '6h ago'
    },
  ];

  const getSignalBadgeClass = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'badge-success';
      case 'SELL':
        return 'badge-danger';
      case 'HOLD':
        return 'badge-warning';
      default:
        return 'badge-gray';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Welcome back! Here's your trading overview.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-gray-900">
                    {stat.value}
                  </p>
                  <p className={`ml-2 text-sm font-medium ${
                    stat.changeType === 'positive' 
                      ? 'text-success-600' 
                      : stat.changeType === 'negative'
                      ? 'text-danger-600'
                      : 'text-gray-500'
                  }`}>
                    {stat.change}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Signals */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Signals</h3>
            <button className="btn-secondary text-sm">View All</button>
          </div>
          <div className="space-y-4">
            {recentSignals.map((signal) => (
              <div key={signal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className={`badge ${getSignalBadgeClass(signal.signal)}`}>
                      {signal.signal}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {signal.etf}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-sm text-gray-500">
                      Confidence: {signal.confidence}%
                    </span>
                    <span className="text-sm text-gray-500">
                      {signal.price}
                    </span>
                  </div>
                </div>
                <span className="text-xs text-gray-400">{signal.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Market Overview */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Market Overview</h3>
            <button className="btn-secondary text-sm">Details</button>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">CAC 40</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">7,425.30</span>
                <span className="text-xs text-success-600 ml-2">+1.2%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">MSCI World</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">3,250.80</span>
                <span className="text-xs text-success-600 ml-2">+0.8%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">S&P 500</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">4,800.15</span>
                <span className="text-xs text-danger-600 ml-2">-0.3%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">EURO STOXX 50</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">4,200.60</span>
                <span className="text-xs text-success-600 ml-2">+0.5%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;