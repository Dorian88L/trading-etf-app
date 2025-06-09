"""
Service d'analyse technique avec calculs d'indicateurs réels
Implémente les indicateurs mentionnés dans le cahier des charges
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class TechnicalIndicators:
    """Structure pour stocker tous les indicateurs techniques"""
    # Moyennes mobiles
    sma_20: float = None
    sma_50: float = None  
    sma_200: float = None
    ema_20: float = None
    ema_50: float = None
    
    # Oscillateurs
    rsi: float = None
    macd: float = None
    macd_signal: float = None
    macd_histogram: float = None
    stochastic_k: float = None
    stochastic_d: float = None
    
    # Volatilité 
    bollinger_upper: float = None
    bollinger_middle: float = None
    bollinger_lower: float = None
    atr: float = None
    
    # Volume
    obv: float = None
    vwap: float = None
    
    # Momentum
    roc: float = None
    williams_r: float = None
    
    # Scores composites
    technical_score: float = None
    trend_strength: float = None
    volatility_score: float = None

class TechnicalAnalysisService:
    """Service principal d'analyse technique"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_all_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        Calcule tous les indicateurs techniques pour un DataFrame de prix
        
        Args:
            df: DataFrame avec colonnes ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            TechnicalIndicators: Objet contenant tous les indicateurs
        """
        try:
            if df.empty or len(df) < 200:
                self.logger.warning("Pas assez de données pour calculer tous les indicateurs")
                return TechnicalIndicators()
                
            indicators = TechnicalIndicators()
            
            # Moyennes mobiles
            indicators.sma_20 = self.calculate_sma(df['close'], 20)
            indicators.sma_50 = self.calculate_sma(df['close'], 50)
            indicators.sma_200 = self.calculate_sma(df['close'], 200)
            indicators.ema_20 = self.calculate_ema(df['close'], 20)
            indicators.ema_50 = self.calculate_ema(df['close'], 50)
            
            # Oscillateurs
            indicators.rsi = self.calculate_rsi(df['close'], 14)
            macd_data = self.calculate_macd(df['close'])
            indicators.macd = macd_data['macd']
            indicators.macd_signal = macd_data['signal']
            indicators.macd_histogram = macd_data['histogram']
            
            stoch_data = self.calculate_stochastic(df['high'], df['low'], df['close'])
            indicators.stochastic_k = stoch_data['k']
            indicators.stochastic_d = stoch_data['d']
            
            # Volatilité
            bollinger_data = self.calculate_bollinger_bands(df['close'])
            indicators.bollinger_upper = bollinger_data['upper']
            indicators.bollinger_middle = bollinger_data['middle']
            indicators.bollinger_lower = bollinger_data['lower']
            indicators.atr = self.calculate_atr(df['high'], df['low'], df['close'])
            
            # Volume  
            indicators.obv = self.calculate_obv(df['close'], df['volume'])
            indicators.vwap = self.calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
            
            # Momentum
            indicators.roc = self.calculate_roc(df['close'], 12)
            indicators.williams_r = self.calculate_williams_r(df['high'], df['low'], df['close'])
            
            # Scores composites
            indicators.technical_score = self.calculate_technical_score(indicators)
            indicators.trend_strength = self.calculate_trend_strength(indicators)
            indicators.volatility_score = self.calculate_volatility_score(indicators)
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Erreur calcul indicateurs techniques: {e}")
            return TechnicalIndicators()
    
    def calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calcule la moyenne mobile simple"""
        try:
            if len(prices) >= period:
                return float(prices.tail(period).mean())
            return None
        except Exception:
            return None
    
    def calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calcule la moyenne mobile exponentielle"""
        try:
            if len(prices) >= period:
                return float(prices.ewm(span=period).mean().iloc[-1])
            return None
        except Exception:
            return None
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcule l'indice de force relative (RSI)"""
        try:
            if len(prices) < period + 1:
                return None
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1])
        except Exception:
            return None
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calcule MACD, signal et histogramme"""
        try:
            if len(prices) < slow + signal:
                return {'macd': None, 'signal': None, 'histogram': None}
                
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]),
                'signal': float(signal_line.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
        except Exception:
            return {'macd': None, 'signal': None, 'histogram': None}
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict:
        """Calcule l'oscillateur stochastique"""
        try:
            if len(close) < k_period:
                return {'k': None, 'd': None}
                
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k': float(k_percent.iloc[-1]),
                'd': float(d_percent.iloc[-1])
            }
        except Exception:
            return {'k': None, 'd': None}
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """Calcule les bandes de Bollinger"""
        try:
            if len(prices) < period:
                return {'upper': None, 'middle': None, 'lower': None}
                
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'upper': float(upper_band.iloc[-1]),
                'middle': float(sma.iloc[-1]),
                'lower': float(lower_band.iloc[-1])
            }
        except Exception:
            return {'upper': None, 'middle': None, 'lower': None}
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calcule l'Average True Range (ATR)"""
        try:
            if len(close) < period + 1:
                return None
                
            high_low = high - low
            high_close_prev = np.abs(high - close.shift(1))
            low_close_prev = np.abs(low - close.shift(1))
            
            true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            atr = pd.Series(true_range).rolling(window=period).mean()
            
            return float(atr.iloc[-1])
        except Exception:
            return None
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> float:
        """Calcule l'On-Balance Volume (OBV)"""
        try:
            if len(close) < 2:
                return None
                
            obv = [0]
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.append(obv[-1] + volume.iloc[i])
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.append(obv[-1] - volume.iloc[i])
                else:
                    obv.append(obv[-1])
                    
            return float(obv[-1])
        except Exception:
            return None
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> float:
        """Calcule le Volume Weighted Average Price (VWAP)"""
        try:
            typical_price = (high + low + close) / 3
            cumulative_tp_volume = (typical_price * volume).cumsum()
            cumulative_volume = volume.cumsum()
            
            vwap = cumulative_tp_volume / cumulative_volume
            return float(vwap.iloc[-1])
        except Exception:
            return None
    
    def calculate_roc(self, prices: pd.Series, period: int = 12) -> float:
        """Calcule le Rate of Change (ROC)"""
        try:
            if len(prices) < period + 1:
                return None
                
            roc = ((prices.iloc[-1] - prices.iloc[-period-1]) / prices.iloc[-period-1]) * 100
            return float(roc)
        except Exception:
            return None
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calcule Williams %R"""
        try:
            if len(close) < period:
                return None
                
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high.iloc[-1] - close.iloc[-1]) / 
                                (highest_high.iloc[-1] - lowest_low.iloc[-1]))
            return float(williams_r)
        except Exception:
            return None
    
    def calculate_technical_score(self, indicators: TechnicalIndicators) -> float:
        """
        Calcule un score technique composite (0-100)
        Plus le score est élevé, plus les signaux sont bullish
        """
        try:
            score = 0
            weight_sum = 0
            
            # Score RSI (poids: 20%)
            if indicators.rsi is not None:
                if indicators.rsi < 30:
                    score += 20  # Oversold = bullish
                elif indicators.rsi > 70:
                    score += 0   # Overbought = bearish
                else:
                    score += 10  # Neutral
                weight_sum += 20
            
            # Score MACD (poids: 25%)
            if indicators.macd is not None and indicators.macd_signal is not None:
                if indicators.macd > indicators.macd_signal:
                    score += 25  # MACD au-dessus du signal = bullish
                weight_sum += 25
            
            # Score moyennes mobiles (poids: 30%)
            if all([indicators.sma_20, indicators.sma_50, indicators.ema_20]):
                ma_score = 0
                if indicators.sma_20 > indicators.sma_50:
                    ma_score += 15  # Court terme > long terme
                if indicators.ema_20 > indicators.sma_20:
                    ma_score += 15  # EMA > SMA = momentum
                score += ma_score
                weight_sum += 30
            
            # Score stochastique (poids: 15%)
            if indicators.stochastic_k is not None:
                if indicators.stochastic_k < 20:
                    score += 15  # Oversold
                elif indicators.stochastic_k > 80:
                    score += 0   # Overbought
                else:
                    score += 7.5  # Neutral
                weight_sum += 15
            
            # Score Williams %R (poids: 10%)
            if indicators.williams_r is not None:
                if indicators.williams_r < -80:
                    score += 10  # Oversold
                elif indicators.williams_r > -20:
                    score += 0   # Overbought
                else:
                    score += 5   # Neutral
                weight_sum += 10
            
            if weight_sum > 0:
                return (score / weight_sum) * 100
            return 50  # Score neutre par défaut
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score technique: {e}")
            return 50
    
    def calculate_trend_strength(self, indicators: TechnicalIndicators) -> float:
        """Calcule la force de la tendance (0-100)"""
        try:
            if not all([indicators.sma_20, indicators.sma_50, indicators.ema_20]):
                return 50
                
            trend_score = 0
            
            # Alignement des moyennes mobiles
            if indicators.ema_20 > indicators.sma_20 > indicators.sma_50:
                trend_score += 40  # Tendance haussière forte
            elif indicators.ema_20 < indicators.sma_20 < indicators.sma_50:
                trend_score += 10  # Tendance baissière
            else:
                trend_score += 25  # Tendance mixte
            
            # MACD
            if indicators.macd is not None and indicators.macd_signal is not None:
                if indicators.macd > indicators.macd_signal and indicators.macd > 0:
                    trend_score += 30  # MACD positif et au-dessus du signal
                elif indicators.macd > indicators.macd_signal:
                    trend_score += 20  # MACD au-dessus du signal seulement
                else:
                    trend_score += 10
            
            # ROC pour le momentum
            if indicators.roc is not None:
                if indicators.roc > 5:
                    trend_score += 30  # Momentum fort
                elif indicators.roc > 0:
                    trend_score += 20  # Momentum positif
                else:
                    trend_score += 10
            
            return min(100, trend_score)
            
        except Exception:
            return 50
    
    def calculate_volatility_score(self, indicators: TechnicalIndicators) -> float:
        """Calcule un score de volatilité (0-100, plus élevé = plus volatil)"""
        try:
            volatility_score = 50  # Score de base
            
            # ATR pour la volatilité absolue
            if indicators.atr is not None and indicators.bollinger_middle is not None:
                atr_percent = (indicators.atr / indicators.bollinger_middle) * 100
                if atr_percent > 3:
                    volatility_score += 30  # Très volatil
                elif atr_percent > 1.5:
                    volatility_score += 15  # Modérément volatil
                else:
                    volatility_score -= 10  # Peu volatil
            
            # Largeur des bandes de Bollinger
            if all([indicators.bollinger_upper, indicators.bollinger_lower, indicators.bollinger_middle]):
                bb_width = ((indicators.bollinger_upper - indicators.bollinger_lower) / 
                           indicators.bollinger_middle) * 100
                if bb_width > 8:
                    volatility_score += 20
                elif bb_width < 4:
                    volatility_score -= 15
            
            return max(0, min(100, volatility_score))
            
        except Exception:
            return 50

def get_technical_analysis_service() -> TechnicalAnalysisService:
    """Factory function pour le service d'analyse technique"""
    return TechnicalAnalysisService()