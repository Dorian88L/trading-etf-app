import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Technical analysis engine for ETF signals"""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=window).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicators"""
        ema_fast = TechnicalAnalyzer.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalyzer.calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        macd_signal = TechnicalAnalyzer.calculate_ema(macd, signal)
        macd_histogram = macd - macd_signal
        
        return {
            "macd": macd,
            "signal": macd_signal,
            "histogram": macd_histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = TechnicalAnalyzer.calculate_sma(prices, window)
        std = prices.rolling(window=window).std()
        
        return {
            "upper": sma + (std * num_std),
            "middle": sma,
            "lower": sma - (std * num_std)
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()
    
    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'stoch_k': k_percent,
            'stoch_d': d_percent
        }
    
    @staticmethod
    def calculate_rate_of_change(close: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Rate of Change (Momentum)"""
        return ((close / close.shift(period)) - 1) * 100
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (ADX)"""
        # Calculate True Range and Directional Movement
        tr = TechnicalAnalyzer.calculate_atr(high, low, close, 1) * period
        
        dm_plus = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0)
        dm_minus = np.where((low.diff().abs() > high.diff()) & (low.diff() < 0), low.diff().abs(), 0)
        
        dm_plus_series = pd.Series(dm_plus, index=high.index)
        dm_minus_series = pd.Series(dm_minus, index=low.index)
        
        # Calculate smoothed values
        tr_smooth = tr.rolling(window=period).mean()
        dm_plus_smooth = dm_plus_series.rolling(window=period).mean()
        dm_minus_smooth = dm_minus_series.rolling(window=period).mean()
        
        # Calculate DI+ and DI-
        di_plus = 100 * dm_plus_smooth / tr_smooth
        di_minus = 100 * dm_minus_smooth / tr_smooth
        
        # Calculate DX and ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On Balance Volume"""
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    def analyze_etf(self, market_data: pd.DataFrame) -> Dict:
        """Complete technical analysis for an ETF"""
        if market_data.empty or len(market_data) < 50:
            return {}
        
        close = market_data['close_price']
        high = market_data['high_price']
        low = market_data['low_price']
        volume = market_data['volume']
        
        # Moving averages
        sma_20 = self.calculate_sma(close, 20)
        sma_50 = self.calculate_sma(close, 50)
        sma_200 = self.calculate_sma(close, 200)
        ema_20 = self.calculate_ema(close, 20)
        ema_50 = self.calculate_ema(close, 50)
        
        # Oscillators
        rsi = self.calculate_rsi(close)
        macd_data = self.calculate_macd(close)
        
        # Bands and volatility
        bb_data = self.calculate_bollinger_bands(close)
        atr = self.calculate_atr(high, low, close)
        
        # Volume indicators
        obv = self.calculate_obv(close, volume)
        vwap = self.calculate_vwap(high, low, close, volume)
        
        # Additional indicators
        williams_r = self.calculate_williams_r(high, low, close)
        stoch_data = self.calculate_stochastic(high, low, close)
        roc = self.calculate_rate_of_change(close)
        adx = self.calculate_adx(high, low, close)
        
        # Get latest values
        latest_idx = market_data.index[-1]
        
        return {
            'timestamp': latest_idx,
            'sma_20': float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            'sma_50': float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
            'sma_200': float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else None,
            'ema_20': float(ema_20.iloc[-1]) if not pd.isna(ema_20.iloc[-1]) else None,
            'ema_50': float(ema_50.iloc[-1]) if not pd.isna(ema_50.iloc[-1]) else None,
            'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            'macd': float(macd_data['macd'].iloc[-1]) if not pd.isna(macd_data['macd'].iloc[-1]) else None,
            'macd_signal': float(macd_data['signal'].iloc[-1]) if not pd.isna(macd_data['signal'].iloc[-1]) else None,
            'macd_histogram': float(macd_data['histogram'].iloc[-1]) if not pd.isna(macd_data['histogram'].iloc[-1]) else None,
            'bb_upper': float(bb_data['upper'].iloc[-1]) if not pd.isna(bb_data['upper'].iloc[-1]) else None,
            'bb_middle': float(bb_data['middle'].iloc[-1]) if not pd.isna(bb_data['middle'].iloc[-1]) else None,
            'bb_lower': float(bb_data['lower'].iloc[-1]) if not pd.isna(bb_data['lower'].iloc[-1]) else None,
            'atr': float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None,
            'obv': int(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else None,
            'vwap': float(vwap.iloc[-1]) if not pd.isna(vwap.iloc[-1]) else None,
            'williams_r': float(williams_r.iloc[-1]) if not pd.isna(williams_r.iloc[-1]) else None,
            'stoch_k': float(stoch_data['stoch_k'].iloc[-1]) if not pd.isna(stoch_data['stoch_k'].iloc[-1]) else None,
            'stoch_d': float(stoch_data['stoch_d'].iloc[-1]) if not pd.isna(stoch_data['stoch_d'].iloc[-1]) else None,
            'roc': float(roc.iloc[-1]) if not pd.isna(roc.iloc[-1]) else None,
            'adx': float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None,
        }


class SignalGenerator:
    """Generate trading signals based on technical analysis"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
    
    def generate_signal(self, etf_isin: str, market_data: pd.DataFrame, technical_data: Dict) -> Optional[Dict]:
        """Generate trading signal for ETF"""
        if not technical_data or len(market_data) < 50:
            return None
        
        current_price = market_data['close_price'].iloc[-1]
        
        # Technical score calculation
        technical_score = self._calculate_technical_score(technical_data, current_price)
        
        # Fundamental score (simplified)
        fundamental_score = self._calculate_fundamental_score(etf_isin)
        
        # Risk score
        risk_score = self._calculate_risk_score(technical_data, market_data)
        
        # Overall confidence
        confidence = (technical_score * 0.5 + fundamental_score * 0.3 + risk_score * 0.2)
        
        # Signal determination
        signal_type = self._determine_signal_type(technical_data, confidence)
        
        # Price targets
        price_target, stop_loss = self._calculate_targets(current_price, technical_data, signal_type)
        
        return {
            'etf_isin': etf_isin,
            'signal_type': signal_type,
            'confidence': round(confidence, 2),
            'technical_score': round(technical_score, 2),
            'fundamental_score': round(fundamental_score, 2),
            'risk_score': round(risk_score, 2),
            'price_target': price_target,
            'stop_loss': stop_loss,
            'current_price': float(current_price),
            'williams_r': technical_data.get('williams_r'),
            'stoch_k': technical_data.get('stoch_k'),
            'stoch_d': technical_data.get('stoch_d'),
            'roc': technical_data.get('roc'),
            'adx': technical_data.get('adx')
        }
    
    def _calculate_technical_score(self, tech_data: Dict, current_price: float) -> float:
        """Calculate technical analysis score (0-100)"""
        score = 50.0  # Neutral starting point
        
        # RSI analysis
        if tech_data.get('rsi'):
            rsi = tech_data['rsi']
            if rsi < 30:
                score += 15  # Oversold - bullish
            elif rsi > 70:
                score -= 15  # Overbought - bearish
            elif 40 <= rsi <= 60:
                score += 5   # Neutral zone - slightly positive
        
        # MACD analysis
        if tech_data.get('macd') and tech_data.get('macd_signal'):
            if tech_data['macd'] > tech_data['macd_signal']:
                score += 10  # MACD above signal - bullish
            else:
                score -= 10  # MACD below signal - bearish
        
        # Moving average analysis
        if tech_data.get('sma_20') and tech_data.get('sma_50'):
            if tech_data['sma_20'] > tech_data['sma_50']:
                score += 10  # Short MA above long MA - bullish
            else:
                score -= 10  # Short MA below long MA - bearish
        
        # Price vs moving averages
        if tech_data.get('ema_20'):
            if current_price > tech_data['ema_20']:
                score += 5   # Price above EMA20 - bullish
            else:
                score -= 5   # Price below EMA20 - bearish
        
        # Bollinger Bands analysis
        if all(k in tech_data for k in ['bb_upper', 'bb_lower', 'bb_middle']):
            if current_price < tech_data['bb_lower']:
                score += 10  # Price below lower band - oversold
            elif current_price > tech_data['bb_upper']:
                score -= 10  # Price above upper band - overbought
        
        # Williams %R analysis
        if tech_data.get('williams_r'):
            williams_r = tech_data['williams_r']
            if williams_r < -80:
                score += 8  # Oversold
            elif williams_r > -20:
                score -= 8  # Overbought
        
        # Stochastic analysis
        if tech_data.get('stoch_k'):
            stoch_k = tech_data['stoch_k']
            if stoch_k < 20:
                score += 8  # Oversold
            elif stoch_k > 80:
                score -= 8  # Overbought
        
        # ADX trend strength
        if tech_data.get('adx'):
            adx = tech_data['adx']
            if adx > 25:  # Strong trend
                score += 5
            elif adx < 20:  # Weak trend
                score -= 3
        
        # Rate of Change momentum
        if tech_data.get('roc'):
            roc = tech_data['roc']
            if roc > 5:
                score += 8  # Strong positive momentum
            elif roc < -5:
                score -= 8  # Strong negative momentum
        
        return max(0, min(100, score))
    
    def _calculate_fundamental_score(self, etf_isin: str) -> float:
        """Calculate fundamental score (simplified)"""
        # This would normally include ETF-specific metrics like:
        # - Expense ratio
        # - AUM size
        # - Tracking error
        # - Sector allocation
        # For now, return a base score
        return 60.0
    
    def _calculate_risk_score(self, tech_data: Dict, market_data: pd.DataFrame) -> float:
        """Calculate risk score (0-100, higher = lower risk)"""
        score = 50.0
        
        # Volatility analysis using ATR
        if tech_data.get('atr') and len(market_data) > 20:
            recent_avg_price = market_data['close_price'].tail(20).mean()
            volatility_ratio = tech_data['atr'] / recent_avg_price
            
            if volatility_ratio < 0.02:
                score += 20  # Low volatility - lower risk
            elif volatility_ratio > 0.05:
                score -= 20  # High volatility - higher risk
        
        # Trend consistency analysis
        if tech_data.get('adx'):
            adx = tech_data['adx']
            if adx > 30:  # Very strong trend = higher predictability
                score += 15
            elif adx > 25:  # Strong trend
                score += 10
            elif adx < 15:  # No clear trend = higher risk
                score -= 10
        
        # Volume consistency
        if len(market_data) > 10:
            volume_cv = market_data['volume'].tail(10).std() / market_data['volume'].tail(10).mean()
            if volume_cv < 0.3:
                score += 10  # Consistent volume - lower risk
            elif volume_cv > 0.7:
                score -= 10  # Erratic volume - higher risk
        
        return max(0, min(100, score))
    
    def _determine_signal_type(self, tech_data: Dict, confidence: float) -> str:
        """Determine signal type based on analysis"""
        # Enhanced signal determination with multiple indicators
        buy_signals = 0
        sell_signals = 0
        
        # RSI signals
        if tech_data.get('rsi'):
            rsi = tech_data['rsi']
            if rsi < 30:
                buy_signals += 2
            elif rsi > 70:
                sell_signals += 2
        
        # MACD signals
        if tech_data.get('macd') and tech_data.get('macd_signal'):
            if tech_data['macd'] > tech_data['macd_signal']:
                buy_signals += 1
            else:
                sell_signals += 1
        
        # Williams %R signals
        if tech_data.get('williams_r'):
            williams_r = tech_data['williams_r']
            if williams_r < -80:
                buy_signals += 1
            elif williams_r > -20:
                sell_signals += 1
        
        # Stochastic signals
        if tech_data.get('stoch_k'):
            stoch_k = tech_data['stoch_k']
            if stoch_k < 20:
                buy_signals += 1
            elif stoch_k > 80:
                sell_signals += 1
        
        # Final determination based on confidence and signal count
        if confidence >= 75 and buy_signals >= sell_signals:
            return "BUY"
        elif confidence <= 25 or sell_signals > buy_signals + 1:
            return "SELL"
        elif confidence >= 60:
            return "HOLD"
        else:
            return "WAIT"
    
    def _calculate_targets(self, current_price: float, tech_data: Dict, signal_type: str) -> tuple:
        """Calculate price target and stop loss"""
        if signal_type == "BUY":
            # For buy signals, set targets above current price
            if tech_data.get('bb_upper'):
                price_target = tech_data['bb_upper']
            else:
                price_target = current_price * 1.05  # 5% above
            
            if tech_data.get('bb_lower'):
                stop_loss = max(tech_data['bb_lower'], current_price * 0.95)
            else:
                stop_loss = current_price * 0.95  # 5% below
                
        elif signal_type == "SELL":
            # For sell signals, set targets below current price
            if tech_data.get('bb_lower'):
                price_target = tech_data['bb_lower']
            else:
                price_target = current_price * 0.95  # 5% below
            
            stop_loss = current_price * 1.05  # 5% above
            
        else:
            # For HOLD/WAIT, set conservative targets
            price_target = current_price * 1.02  # 2% above
            stop_loss = current_price * 0.98   # 2% below
        
        return round(price_target, 4), round(stop_loss, 4)