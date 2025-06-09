"""
Service de génération de signaux de trading automatisés
Implémente les algorithmes mentionnés dans le cahier des charges
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.technical_indicators import TechnicalAnalysisService, TechnicalIndicators
from app.models.signal import SignalType
from app.core.database import get_db

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    """Force du signal de trading"""
    WEAK = "weak"
    MODERATE = "moderate" 
    STRONG = "strong"
    VERY_STRONG = "very_strong"

@dataclass
class TradingSignal:
    """Signal de trading généré"""
    etf_isin: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0-100%
    price_target: Optional[float]
    stop_loss: Optional[float]
    technical_score: float
    risk_score: float
    entry_price: float
    reasons: List[str]  # Justifications du signal
    timestamp: datetime

class TradingSignalGenerator:
    """Service principal de génération de signaux"""
    
    def __init__(self):
        self.technical_service = TechnicalAnalysisService()
        self.logger = logging.getLogger(__name__)
        
    def generate_signal(self, df: pd.DataFrame, etf_isin: str, symbol: str) -> Optional[TradingSignal]:
        """
        Génère un signal de trading pour un ETF donné
        
        Args:
            df: DataFrame avec données historiques OHLCV
            etf_isin: ISIN de l'ETF
            symbol: Symbole de l'ETF
            
        Returns:
            TradingSignal ou None si pas de signal
        """
        try:
            if df.empty or len(df) < 50:
                return None
                
            # Calculer tous les indicateurs techniques
            indicators = self.technical_service.calculate_all_indicators(df)
            
            # Analyser les différents types de signaux
            breakout_signal = self._analyze_breakout(df, indicators)
            mean_reversion_signal = self._analyze_mean_reversion(df, indicators)
            momentum_signal = self._analyze_momentum(df, indicators)
            
            # Sélectionner le meilleur signal
            best_signal = self._select_best_signal([
                breakout_signal,
                mean_reversion_signal, 
                momentum_signal
            ])
            
            if best_signal:
                # Calculer price target et stop loss
                current_price = float(df['close'].iloc[-1])
                price_target, stop_loss = self._calculate_targets(
                    current_price, best_signal.signal_type, indicators
                )
                
                # Calculer le score de risque
                risk_score = self._calculate_risk_score(indicators, df)
                
                return TradingSignal(
                    etf_isin=etf_isin,
                    symbol=symbol,
                    signal_type=best_signal.signal_type,
                    strength=best_signal.strength,
                    confidence=best_signal.confidence,
                    price_target=price_target,
                    stop_loss=stop_loss,
                    technical_score=indicators.technical_score or 50,
                    risk_score=risk_score,
                    entry_price=current_price,
                    reasons=best_signal.reasons,
                    timestamp=datetime.now()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur génération signal pour {symbol}: {e}")
            return None
    
    def _analyze_breakout(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """Analyse les signaux de cassure (breakout)"""
        try:
            current_price = float(df['close'].iloc[-1])
            volume_avg = df['volume'].tail(20).mean()
            current_volume = float(df['volume'].iloc[-1])
            
            reasons = []
            confidence = 0
            signal_type = None
            strength = SignalStrength.WEAK
            
            # Cassure des bandes de Bollinger avec volume
            if all([indicators.bollinger_upper, indicators.bollinger_lower]):
                if current_price > indicators.bollinger_upper and current_volume > volume_avg * 1.5:
                    signal_type = SignalType.BUY
                    confidence += 30
                    reasons.append("Cassure bande Bollinger supérieure avec volume")
                    strength = SignalStrength.MODERATE
                elif current_price < indicators.bollinger_lower and current_volume > volume_avg * 1.5:
                    signal_type = SignalType.SELL
                    confidence += 30
                    reasons.append("Cassure bande Bollinger inférieure avec volume")
                    strength = SignalStrength.MODERATE
            
            # Cassure de résistance/support avec moyennes mobiles
            if indicators.sma_20 and indicators.sma_50:
                if (current_price > indicators.sma_20 > indicators.sma_50 and 
                    indicators.rsi and indicators.rsi > 50):
                    if signal_type == SignalType.BUY:
                        confidence += 25
                        strength = SignalStrength.STRONG
                    elif signal_type is None:
                        signal_type = SignalType.BUY
                        confidence += 20
                    reasons.append("Cassure au-dessus moyennes mobiles alignées")
                    
                elif (current_price < indicators.sma_20 < indicators.sma_50 and 
                      indicators.rsi and indicators.rsi < 50):
                    if signal_type == SignalType.SELL:
                        confidence += 25
                        strength = SignalStrength.STRONG
                    elif signal_type is None:
                        signal_type = SignalType.SELL
                        confidence += 20
                    reasons.append("Cassure en-dessous moyennes mobiles alignées")
            
            # Volume exceptionnel
            if current_volume > volume_avg * 2:
                confidence += 15
                reasons.append("Volume exceptionnel")
                if strength == SignalStrength.STRONG:
                    strength = SignalStrength.VERY_STRONG
            
            if signal_type and confidence >= 30:
                return TradingSignal(
                    etf_isin="", symbol="", signal_type=signal_type,
                    strength=strength, confidence=min(95, confidence),
                    price_target=None, stop_loss=None, technical_score=0,
                    risk_score=0, entry_price=current_price, reasons=reasons,
                    timestamp=datetime.now()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur analyse breakout: {e}")
            return None
    
    def _analyze_mean_reversion(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """Analyse les signaux de retour à la moyenne"""
        try:
            current_price = float(df['close'].iloc[-1])
            reasons = []
            confidence = 0
            signal_type = None
            strength = SignalStrength.WEAK
            
            # RSI oversold/overbought
            if indicators.rsi:
                if indicators.rsi < 30:
                    signal_type = SignalType.BUY
                    confidence += 35
                    reasons.append(f"RSI oversold ({indicators.rsi:.1f})")
                    strength = SignalStrength.MODERATE
                elif indicators.rsi > 70:
                    signal_type = SignalType.SELL
                    confidence += 35
                    reasons.append(f"RSI overbought ({indicators.rsi:.1f})")
                    strength = SignalStrength.MODERATE
            
            # Stochastique oversold/overbought
            if indicators.stochastic_k:
                if indicators.stochastic_k < 20 and signal_type == SignalType.BUY:
                    confidence += 20
                    reasons.append(f"Stochastique oversold ({indicators.stochastic_k:.1f})")
                    strength = SignalStrength.STRONG
                elif indicators.stochastic_k > 80 and signal_type == SignalType.SELL:
                    confidence += 20
                    reasons.append(f"Stochastique overbought ({indicators.stochastic_k:.1f})")
                    strength = SignalStrength.STRONG
            
            # Williams %R confirmation
            if indicators.williams_r:
                if indicators.williams_r < -80 and signal_type == SignalType.BUY:
                    confidence += 15
                    reasons.append("Williams %R oversold")
                elif indicators.williams_r > -20 and signal_type == SignalType.SELL:
                    confidence += 15
                    reasons.append("Williams %R overbought")
            
            # Position relative aux bandes de Bollinger
            if all([indicators.bollinger_upper, indicators.bollinger_lower, indicators.bollinger_middle]):
                bb_position = (current_price - indicators.bollinger_lower) / (
                    indicators.bollinger_upper - indicators.bollinger_lower
                )
                
                if bb_position < 0.1 and signal_type == SignalType.BUY:
                    confidence += 15
                    reasons.append("Prix proche bande Bollinger inférieure")
                elif bb_position > 0.9 and signal_type == SignalType.SELL:
                    confidence += 15
                    reasons.append("Prix proche bande Bollinger supérieure")
            
            # MACD divergence (signaux précoces)
            if all([indicators.macd, indicators.macd_signal]):
                if (indicators.macd < indicators.macd_signal and 
                    indicators.macd > indicators.macd_signal and
                    signal_type == SignalType.BUY):
                    confidence += 10
                    reasons.append("MACD signal haussier")
                elif (indicators.macd > indicators.macd_signal and 
                      indicators.macd < indicators.macd_signal and
                      signal_type == SignalType.SELL):
                    confidence += 10
                    reasons.append("MACD signal baissier")
            
            if signal_type and confidence >= 40:
                return TradingSignal(
                    etf_isin="", symbol="", signal_type=signal_type,
                    strength=strength, confidence=min(95, confidence),
                    price_target=None, stop_loss=None, technical_score=0,
                    risk_score=0, entry_price=current_price, reasons=reasons,
                    timestamp=datetime.now()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur analyse mean reversion: {e}")
            return None
    
    def _analyze_momentum(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """Analyse les signaux de momentum"""
        try:
            current_price = float(df['close'].iloc[-1])
            recent_prices = df['close'].tail(5)
            price_trend = (current_price - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
            
            reasons = []
            confidence = 0
            signal_type = None
            strength = SignalStrength.WEAK
            
            # Tendance de prix forte
            if price_trend > 2:
                signal_type = SignalType.BUY
                confidence += 25
                reasons.append(f"Momentum haussier fort (+{price_trend:.1f}%)")
                strength = SignalStrength.MODERATE
            elif price_trend < -2:
                signal_type = SignalType.SELL
                confidence += 25
                reasons.append(f"Momentum baissier fort ({price_trend:.1f}%)")
                strength = SignalStrength.MODERATE
            
            # ROC confirmation
            if indicators.roc:
                if indicators.roc > 5 and signal_type == SignalType.BUY:
                    confidence += 20
                    reasons.append(f"ROC positif fort ({indicators.roc:.1f}%)")
                    strength = SignalStrength.STRONG
                elif indicators.roc < -5 and signal_type == SignalType.SELL:
                    confidence += 20
                    reasons.append(f"ROC négatif fort ({indicators.roc:.1f}%)")
                    strength = SignalStrength.STRONG
            
            # MACD momentum
            if all([indicators.macd, indicators.macd_signal, indicators.macd_histogram]):
                if (indicators.macd > indicators.macd_signal and 
                    indicators.macd_histogram > 0 and
                    signal_type == SignalType.BUY):
                    confidence += 20
                    reasons.append("MACD momentum haussier")
                    
                elif (indicators.macd < indicators.macd_signal and 
                      indicators.macd_histogram < 0 and
                      signal_type == SignalType.SELL):
                    confidence += 20
                    reasons.append("MACD momentum baissier")
            
            # Alignement moyennes mobiles
            if all([indicators.ema_20, indicators.sma_20, indicators.sma_50]):
                if (indicators.ema_20 > indicators.sma_20 > indicators.sma_50 and
                    signal_type == SignalType.BUY):
                    confidence += 15
                    reasons.append("Moyennes mobiles alignées haussier")
                    if strength == SignalStrength.STRONG:
                        strength = SignalStrength.VERY_STRONG
                        
                elif (indicators.ema_20 < indicators.sma_20 < indicators.sma_50 and
                      signal_type == SignalType.SELL):
                    confidence += 15
                    reasons.append("Moyennes mobiles alignées baissier")
                    if strength == SignalStrength.STRONG:
                        strength = SignalStrength.VERY_STRONG
            
            # Volume momentum
            volume_trend = df['volume'].tail(5).mean() / df['volume'].tail(20).mean()
            if volume_trend > 1.5:
                confidence += 10
                reasons.append("Volume en augmentation")
            
            if signal_type and confidence >= 35:
                return TradingSignal(
                    etf_isin="", symbol="", signal_type=signal_type,
                    strength=strength, confidence=min(95, confidence),
                    price_target=None, stop_loss=None, technical_score=0,
                    risk_score=0, entry_price=current_price, reasons=reasons,
                    timestamp=datetime.now()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur analyse momentum: {e}")
            return None
    
    def _select_best_signal(self, signals: List[Optional[TradingSignal]]) -> Optional[TradingSignal]:
        """Sélectionne le meilleur signal parmi une liste"""
        valid_signals = [s for s in signals if s is not None]
        
        if not valid_signals:
            return None
            
        # Trier par confiance puis par force
        strength_order = {
            SignalStrength.VERY_STRONG: 4,
            SignalStrength.STRONG: 3,
            SignalStrength.MODERATE: 2,
            SignalStrength.WEAK: 1
        }
        
        valid_signals.sort(
            key=lambda x: (x.confidence, strength_order[x.strength]),
            reverse=True
        )
        
        return valid_signals[0]
    
    def _calculate_targets(self, current_price: float, signal_type: SignalType, 
                          indicators: TechnicalIndicators) -> Tuple[Optional[float], Optional[float]]:
        """Calcule price target et stop loss"""
        try:
            if signal_type == SignalType.BUY:
                # Price target basé sur ATR et résistances
                atr_multiplier = 2.0
                if indicators.atr:
                    price_target = current_price + (indicators.atr * atr_multiplier)
                else:
                    price_target = current_price * 1.03  # +3% par défaut
                
                # Stop loss plus conservateur
                stop_loss_multiplier = 1.0
                if indicators.atr:
                    stop_loss = current_price - (indicators.atr * stop_loss_multiplier)
                else:
                    stop_loss = current_price * 0.98  # -2% par défaut
                    
            elif signal_type == SignalType.SELL:
                # Price target en baisse
                atr_multiplier = 2.0
                if indicators.atr:
                    price_target = current_price - (indicators.atr * atr_multiplier)
                else:
                    price_target = current_price * 0.97  # -3% par défaut
                
                # Stop loss pour short
                stop_loss_multiplier = 1.0
                if indicators.atr:
                    stop_loss = current_price + (indicators.atr * stop_loss_multiplier)
                else:
                    stop_loss = current_price * 1.02  # +2% par défaut
            else:
                return None, None
            
            return price_target, stop_loss
            
        except Exception as e:
            self.logger.error(f"Erreur calcul targets: {e}")
            return None, None
    
    def _calculate_risk_score(self, indicators: TechnicalIndicators, df: pd.DataFrame) -> float:
        """Calcule un score de risque (0-100, plus élevé = plus risqué)"""
        try:
            risk_score = 50  # Score de base
            
            # Volatilité (ATR)
            if indicators.volatility_score:
                volatility_component = (indicators.volatility_score - 50) * 0.6
                risk_score += volatility_component
            
            # Trend strength (tendance faible = plus risqué)
            if indicators.trend_strength:
                trend_component = (50 - indicators.trend_strength) * 0.3
                risk_score += trend_component
            
            # Volume analysis
            volume_ratio = df['volume'].tail(5).mean() / df['volume'].tail(20).mean()
            if volume_ratio < 0.7:  # Volume faible = plus risqué
                risk_score += 10
            elif volume_ratio > 1.5:  # Volume fort = moins risqué
                risk_score -= 5
            
            # RSI extreme values
            if indicators.rsi:
                if indicators.rsi > 80 or indicators.rsi < 20:
                    risk_score += 15  # Conditions extremes = plus risqué
            
            return max(0, min(100, risk_score))
            
        except Exception:
            return 50

    def generate_signals_for_etfs(self, etf_data_list: List[Dict]) -> List[TradingSignal]:
        """Génère des signaux pour une liste d'ETFs"""
        signals = []
        
        for etf_data in etf_data_list:
            try:
                # Simuler des données historiques pour l'exemple
                # En production, récupérer les vraies données depuis la DB ou l'API
                df = self._create_sample_data()
                
                signal = self.generate_signal(
                    df=df,
                    etf_isin=etf_data.get('isin', ''),
                    symbol=etf_data.get('symbol', '')
                )
                
                if signal:
                    signals.append(signal)
                    
            except Exception as e:
                self.logger.error(f"Erreur génération signal pour {etf_data.get('symbol')}: {e}")
                continue
        
        # Trier par confiance décroissante
        signals.sort(key=lambda x: x.confidence, reverse=True)
        return signals[:10]  # Retourner les 10 meilleurs signaux
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Crée des données d'exemple pour les tests"""
        dates = pd.date_range(start='2024-01-01', end='2024-06-08', freq='D')
        n_days = len(dates)
        
        # Générer des prix réalistes avec tendance et volatilité
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, n_days)  # Rendements journaliers
        prices = [100]  # Prix initial
        
        for i in range(1, n_days):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(new_price)
        
        # Créer OHLC à partir du close
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'volume': [int(np.random.normal(1000000, 200000)) for _ in range(n_days)]
        })
        
        # Assurer que high >= close >= low et open
        df['high'] = df[['high', 'close', 'open']].max(axis=1)
        df['low'] = df[['low', 'close', 'open']].min(axis=1)
        
        return df

def get_signal_generator_service() -> TradingSignalGenerator:
    """Factory function pour le service de génération de signaux"""
    return TradingSignalGenerator()