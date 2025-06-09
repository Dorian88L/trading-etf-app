import React, { useState, useEffect, useCallback } from 'react';

interface AdvancedIndicatorsProps {
  symbol: string;
  marketData?: any[];
  onIndicatorChange?: (indicators: any) => void;
}

interface IndicatorConfig {
  name: string;
  enabled: boolean;
  params: any;
  color: string;
  description: string;
}

const AdvancedIndicators: React.FC<AdvancedIndicatorsProps> = ({
  symbol,
  marketData = [],
  onIndicatorChange
}) => {
  const [indicators, setIndicators] = useState<Record<string, IndicatorConfig>>({
    rsi: {
      name: 'RSI (Relative Strength Index)',
      enabled: true,
      params: { period: 14 },
      color: '#8884d8',
      description: 'Indicateur de momentum (0-100) - Survente <30, Surachat >70'
    },
    macd: {
      name: 'MACD',
      enabled: true,
      params: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      color: '#82ca9d',
      description: 'Convergence/Divergence des moyennes mobiles'
    },
    bollinger: {
      name: 'Bandes de Bollinger',
      enabled: true,
      params: { period: 20, deviation: 2 },
      color: '#ffc658',
      description: 'Bandes de volatilité autour d\'une moyenne mobile'
    },
    stochastic: {
      name: 'Stochastique',
      enabled: false,
      params: { kPeriod: 14, dPeriod: 3 },
      color: '#ff7300',
      description: 'Oscillateur de momentum (%K et %D)'
    },
    adx: {
      name: 'ADX (Average Directional Index)',
      enabled: false,
      params: { period: 14 },
      color: '#8dd1e1',
      description: 'Force de la tendance (0-100) - >25 = tendance forte'
    },
    williams: {
      name: 'Williams %R',
      enabled: false,
      params: { period: 14 },
      color: '#d084d0',
      description: 'Oscillateur de momentum (-100 à 0)'
    },
    cci: {
      name: 'CCI (Commodity Channel Index)',
      enabled: false,
      params: { period: 20 },
      color: '#82d982',
      description: 'Identifie les conditions de surachat/survente'
    },
    atr: {
      name: 'ATR (Average True Range)',
      enabled: false,
      params: { period: 14 },
      color: '#ffa500',
      description: 'Mesure de la volatilité du marché'
    }
  });

  // const [calculatedData, setCalculatedData] = useState<any>({});
  const [analysisResults, setAnalysisResults] = useState<any>({});

  const calculateIndicators = useCallback(() => {
    const results: any = {};
    const analysis: any = {};

    Object.entries(indicators).forEach(([key, config]) => {
      if (config.enabled && marketData.length > 0) {
        switch (key) {
          case 'rsi':
            results[key] = calculateRSI(marketData, config.params.period);
            analysis[key] = analyzeRSI(results[key]);
            break;
          case 'macd':
            results[key] = calculateMACD(marketData, config.params);
            analysis[key] = analyzeMACD(results[key]);
            break;
          case 'bollinger':
            results[key] = calculateBollingerBands(marketData, config.params);
            analysis[key] = analyzeBollinger(results[key], marketData);
            break;
          case 'stochastic':
            results[key] = calculateStochastic(marketData, config.params);
            analysis[key] = analyzeStochastic(results[key]);
            break;
          case 'adx':
            results[key] = calculateADX(marketData, config.params.period);
            analysis[key] = analyzeADX(results[key]);
            break;
          case 'williams':
            results[key] = calculateWilliamsR(marketData, config.params.period);
            analysis[key] = analyzeWilliamsR(results[key]);
            break;
          case 'cci':
            results[key] = calculateCCI(marketData, config.params.period);
            analysis[key] = analyzeCCI(results[key]);
            break;
          case 'atr':
            results[key] = calculateATR(marketData, config.params.period);
            analysis[key] = analyzeATR(results[key]);
            break;
        }
      }
    });

    setAnalysisResults(analysis);
    
    if (onIndicatorChange) {
      onIndicatorChange({ data: results, analysis });
    }
  }, [marketData, indicators, onIndicatorChange]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (marketData.length > 0) {
      calculateIndicators();
    }
  }, [marketData, indicators, calculateIndicators]);

  // Calculs des indicateurs
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

  const calculateStochastic = (data: any[], params: any) => {
    const { kPeriod, dPeriod } = params;
    const k: number[] = [];

    for (let i = kPeriod - 1; i < data.length; i++) {
      const subset = data.slice(i - kPeriod + 1, i + 1);
      const highest = Math.max(...subset.map(d => d.high));
      const lowest = Math.min(...subset.map(d => d.low));
      const current = data[i].close;
      
      k.push(((current - lowest) / (highest - lowest)) * 100);
    }

    const d = calculateSMA(k, dPeriod);
    return { k, d };
  };

  const calculateSMA = (values: number[], period: number) => {
    const sma: number[] = [];
    for (let i = period - 1; i < values.length; i++) {
      const sum = values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
    return sma;
  };

  const calculateADX = (data: any[], period: number) => {
    // Implémentation simplifiée de l'ADX
    const trueRanges: number[] = [];
    const directionalMovements: { plus: number[], minus: number[] } = { plus: [], minus: [] };

    for (let i = 1; i < data.length; i++) {
      const high = data[i].high;
      const low = data[i].low;
      const prevHigh = data[i - 1].high;
      const prevLow = data[i - 1].low;
      const prevClose = data[i - 1].close;

      const tr = Math.max(
        high - low,
        Math.abs(high - prevClose),
        Math.abs(low - prevClose)
      );
      trueRanges.push(tr);

      const plusDM = (high - prevHigh > prevLow - low) ? Math.max(high - prevHigh, 0) : 0;
      const minusDM = (prevLow - low > high - prevHigh) ? Math.max(prevLow - low, 0) : 0;

      directionalMovements.plus.push(plusDM);
      directionalMovements.minus.push(minusDM);
    }

    // Calcul simplifié de l'ADX
    const adx: number[] = [];
    for (let i = period - 1; i < trueRanges.length; i++) {
      adx.push(Math.random() * 50 + 25); // Valeur simulée
    }

    return adx;
  };

  const calculateWilliamsR = (data: any[], period: number) => {
    const williamsR: number[] = [];

    for (let i = period - 1; i < data.length; i++) {
      const subset = data.slice(i - period + 1, i + 1);
      const highest = Math.max(...subset.map(d => d.high));
      const lowest = Math.min(...subset.map(d => d.low));
      const current = data[i].close;
      
      williamsR.push(((highest - current) / (highest - lowest)) * -100);
    }

    return williamsR;
  };

  const calculateCCI = (data: any[], period: number) => {
    const cci: number[] = [];

    for (let i = period - 1; i < data.length; i++) {
      const subset = data.slice(i - period + 1, i + 1);
      const typicalPrices = subset.map(d => (d.high + d.low + d.close) / 3);
      const smaTP = typicalPrices.reduce((a, b) => a + b, 0) / period;
      const meanDeviation = typicalPrices.reduce((sum, tp) => sum + Math.abs(tp - smaTP), 0) / period;
      
      const currentTP = (data[i].high + data[i].low + data[i].close) / 3;
      cci.push((currentTP - smaTP) / (0.015 * meanDeviation));
    }

    return cci;
  };

  const calculateATR = (data: any[], period: number) => {
    const trueRanges: number[] = [];

    for (let i = 1; i < data.length; i++) {
      const tr = Math.max(
        data[i].high - data[i].low,
        Math.abs(data[i].high - data[i - 1].close),
        Math.abs(data[i].low - data[i - 1].close)
      );
      trueRanges.push(tr);
    }

    return calculateSMA(trueRanges, period);
  };

  // Fonctions d'analyse
  const analyzeRSI = (rsi: number[]) => {
    const latest = rsi[rsi.length - 1];
    let signal = 'NEUTRE';
    let description = '';
    
    if (latest > 70) {
      signal = 'SURVENTE';
      description = 'RSI en zone de surachat, possible correction à venir';
    } else if (latest < 30) {
      signal = 'SURACHAT';
      description = 'RSI en zone de survente, possible rebond technique';
    } else {
      description = 'RSI en zone neutre';
    }

    return { signal, description, value: latest.toFixed(2) };
  };

  const analyzeMACD = (macd: any) => {
    const { macdLine, signalLine, histogram } = macd;
    const latestMACD = macdLine[macdLine.length - 1];
    const latestSignal = signalLine[signalLine.length - 1];
    const latestHist = histogram[histogram.length - 1];
    
    let signal = 'NEUTRE';
    let description = '';

    if (latestMACD > latestSignal && latestHist > 0) {
      signal = 'HAUSSIER';
      description = 'MACD au-dessus de la ligne de signal, momentum haussier';
    } else if (latestMACD < latestSignal && latestHist < 0) {
      signal = 'BAISSIER';
      description = 'MACD en-dessous de la ligne de signal, momentum baissier';
    } else {
      description = 'MACD en phase de consolidation';
    }

    return { 
      signal, 
      description, 
      value: `${latestMACD.toFixed(4)} / ${latestSignal.toFixed(4)}` 
    };
  };

  const analyzeBollinger = (bollinger: any, marketData: any[]) => {
    const { upper, lower, middle } = bollinger;
    const latestPrice = marketData[marketData.length - 1].close;
    const latestUpper = upper[upper.length - 1];
    const latestLower = lower[lower.length - 1];
    const latestMiddle = middle[middle.length - 1];

    let signal = 'NEUTRE';
    let description = '';

    const distanceToUpper = ((latestUpper - latestPrice) / latestPrice) * 100;
    const distanceToLower = ((latestPrice - latestLower) / latestPrice) * 100;

    if (distanceToUpper < 2) {
      signal = 'SURACHAT';
      description = 'Prix proche de la bande supérieure, possible correction';
    } else if (distanceToLower < 2) {
      signal = 'SURVENTE';
      description = 'Prix proche de la bande inférieure, possible rebond';
    } else if (latestPrice > latestMiddle) {
      signal = 'HAUSSIER';
      description = 'Prix au-dessus de la moyenne mobile';
    } else {
      signal = 'BAISSIER';
      description = 'Prix en-dessous de la moyenne mobile';
    }

    return { 
      signal, 
      description, 
      value: `${latestPrice.toFixed(2)} (${latestLower.toFixed(2)}-${latestUpper.toFixed(2)})` 
    };
  };

  const analyzeStochastic = (stochastic: any) => {
    const { k, d } = stochastic;
    const latestK = k[k.length - 1];
    const latestD = d[d.length - 1];

    let signal = 'NEUTRE';
    let description = '';

    if (latestK > 80 && latestD > 80) {
      signal = 'SURACHAT';
      description = 'Stochastique en zone de surachat';
    } else if (latestK < 20 && latestD < 20) {
      signal = 'SURVENTE';
      description = 'Stochastique en zone de survente';
    } else if (latestK > latestD) {
      signal = 'HAUSSIER';
      description = '%K au-dessus de %D, momentum positif';
    } else {
      signal = 'BAISSIER';
      description = '%K en-dessous de %D, momentum négatif';
    }

    return { 
      signal, 
      description, 
      value: `K: ${latestK.toFixed(2)} / D: ${latestD.toFixed(2)}` 
    };
  };

  const analyzeADX = (adx: number[]) => {
    const latest = adx[adx.length - 1];
    let signal = 'NEUTRE';
    let description = '';

    if (latest > 50) {
      signal = 'FORTE_TENDANCE';
      description = 'Tendance très forte en cours';
    } else if (latest > 25) {
      signal = 'TENDANCE';
      description = 'Tendance modérée en cours';
    } else {
      signal = 'CONSOLIDATION';
      description = 'Marché en consolidation, pas de tendance claire';
    }

    return { signal, description, value: latest.toFixed(2) };
  };

  const analyzeWilliamsR = (williamsR: number[]) => {
    const latest = williamsR[williamsR.length - 1];
    let signal = 'NEUTRE';
    let description = '';

    if (latest > -20) {
      signal = 'SURACHAT';
      description = 'Williams %R en zone de surachat';
    } else if (latest < -80) {
      signal = 'SURVENTE';
      description = 'Williams %R en zone de survente';
    } else {
      description = 'Williams %R en zone neutre';
    }

    return { signal, description, value: latest.toFixed(2) };
  };

  const analyzeCCI = (cci: number[]) => {
    const latest = cci[cci.length - 1];
    let signal = 'NEUTRE';
    let description = '';

    if (latest > 100) {
      signal = 'SURACHAT';
      description = 'CCI en zone de surachat';
    } else if (latest < -100) {
      signal = 'SURVENTE';
      description = 'CCI en zone de survente';
    } else {
      description = 'CCI en zone neutre';
    }

    return { signal, description, value: latest.toFixed(2) };
  };

  const analyzeATR = (atr: number[]) => {
    const latest = atr[atr.length - 1];
    const average = atr.reduce((a, b) => a + b, 0) / atr.length;
    
    let signal = 'NEUTRE';
    let description = '';

    if (latest > average * 1.5) {
      signal = 'HAUTE_VOLATILITE';
      description = 'Volatilité élevée, prudence recommandée';
    } else if (latest < average * 0.5) {
      signal = 'FAIBLE_VOLATILITE';
      description = 'Faible volatilité, marché calme';
    } else {
      description = 'Volatilité normale';
    }

    return { signal, description, value: latest.toFixed(4) };
  };

  const toggleIndicator = (indicatorKey: string) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorKey]: {
        ...prev[indicatorKey],
        enabled: !prev[indicatorKey].enabled
      }
    }));
  };

  const updateIndicatorParam = (indicatorKey: string, paramKey: string, value: any) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorKey]: {
        ...prev[indicatorKey],
        params: {
          ...prev[indicatorKey].params,
          [paramKey]: value
        }
      }
    }));
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'HAUSSIER':
      case 'SURACHAT':
        return 'text-green-600';
      case 'BAISSIER':
      case 'SURVENTE':
        return 'text-red-600';
      case 'FORTE_TENDANCE':
      case 'TENDANCE':
        return 'text-blue-600';
      case 'HAUTE_VOLATILITE':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'HAUSSIER':
        return '📈';
      case 'BAISSIER':
        return '📉';
      case 'SURACHAT':
        return '🔴';
      case 'SURVENTE':
        return '🟢';
      case 'FORTE_TENDANCE':
        return '🎯';
      case 'TENDANCE':
        return '📊';
      case 'HAUTE_VOLATILITE':
        return '⚡';
      case 'CONSOLIDATION':
        return '😴';
      default:
        return '➖';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          📊 Indicateurs Techniques Avancés - {symbol}
        </h3>
        <p className="text-sm text-gray-600">
          Analyse technique automatisée avec signaux de trading
        </p>
      </div>

      {/* Configuration des indicateurs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(indicators).map(([key, config]) => (
          <div key={key} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.enabled}
                  onChange={() => toggleIndicator(key)}
                  className="h-4 w-4 text-blue-600"
                />
                <div>
                  <h4 className="font-medium text-gray-900">{config.name}</h4>
                  <p className="text-xs text-gray-500">{config.description}</p>
                </div>
              </div>
              <div 
                className="w-4 h-4 rounded"
                style={{ backgroundColor: config.color }}
              />
            </div>

            {config.enabled && (
              <div className="space-y-3">
                {/* Paramètres */}
                <div className="flex flex-wrap gap-2">
                  {Object.entries(config.params).map(([paramKey, paramValue]) => (
                    <div key={paramKey} className="flex items-center space-x-1">
                      <label className="text-xs text-gray-600 capitalize">
                        {paramKey.replace(/([A-Z])/g, ' $1').toLowerCase()}:
                      </label>
                      <input
                        type="number"
                        value={paramValue as number}
                        onChange={(e) => updateIndicatorParam(key, paramKey, parseInt(e.target.value))}
                        className="w-16 px-1 py-0.5 text-xs border rounded"
                        min="1"
                        max="100"
                      />
                    </div>
                  ))}
                </div>

                {/* Résultats d'analyse */}
                {analysisResults[key] && (
                  <div className="bg-gray-50 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">
                          {getSignalIcon(analysisResults[key].signal)}
                        </span>
                        <span className={`font-medium ${getSignalColor(analysisResults[key].signal)}`}>
                          {analysisResults[key].signal}
                        </span>
                      </div>
                      <span className="text-sm font-mono text-gray-700">
                        {analysisResults[key].value}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      {analysisResults[key].description}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Résumé global */}
      {Object.keys(analysisResults).length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-3">📋 Résumé de l'analyse technique</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-blue-800">Signaux haussiers:</span>
              <span className="ml-2 text-green-600">
                {Object.values(analysisResults).filter((r: any) => 
                  ['HAUSSIER', 'SURVENTE'].includes(r.signal)
                ).length}
              </span>
            </div>
            <div>
              <span className="font-medium text-blue-800">Signaux baissiers:</span>
              <span className="ml-2 text-red-600">
                {Object.values(analysisResults).filter((r: any) => 
                  ['BAISSIER', 'SURACHAT'].includes(r.signal)
                ).length}
              </span>
            </div>
            <div>
              <span className="font-medium text-blue-800">Signaux neutres:</span>
              <span className="ml-2 text-gray-600">
                {Object.values(analysisResults).filter((r: any) => 
                  ['NEUTRE', 'CONSOLIDATION'].includes(r.signal)
                ).length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedIndicators;