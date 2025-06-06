"""
Système de signaux avancé selon le cahier des charges
- Scoring 0-100 avec algorithmes multiples
- Breakout, Mean Reversion, Momentum, Arbitrage statistique
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL" 
    HOLD = "HOLD"
    WAIT = "WAIT"

class AlgorithmType(str, Enum):
    BREAKOUT = "BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    STATISTICAL_ARBITRAGE = "STATISTICAL_ARBITRAGE"

@dataclass
class TechnicalScore:
    """Score technique détaillé"""
    rsi_score: float = 0.0
    macd_score: float = 0.0
    bollinger_score: float = 0.0
    volume_score: float = 0.0
    momentum_score: float = 0.0
    moving_average_score: float = 0.0
    williams_r_score: float = 0.0
    stochastic_score: float = 0.0
    
    @property
    def total_score(self) -> float:
        """Score technique total pondéré"""
        weights = {
            'rsi': 0.15,
            'macd': 0.15,
            'bollinger': 0.15,
            'volume': 0.10,
            'momentum': 0.15,
            'moving_average': 0.15,
            'williams_r': 0.10,
            'stochastic': 0.05
        }
        
        total = (
            self.rsi_score * weights['rsi'] +
            self.macd_score * weights['macd'] +
            self.bollinger_score * weights['bollinger'] +
            self.volume_score * weights['volume'] +
            self.momentum_score * weights['momentum'] +
            self.moving_average_score * weights['moving_average'] +
            self.williams_r_score * weights['williams_r'] +
            self.stochastic_score * weights['stochastic']
        )
        
        return min(100, max(0, total))

@dataclass
class FundamentalScore:
    """Score fondamental ETF"""
    liquidity_score: float = 0.0
    ter_score: float = 0.0
    aum_score: float = 0.0
    tracking_error_score: float = 0.0
    nav_premium_score: float = 0.0
    
    @property
    def total_score(self) -> float:
        """Score fondamental total"""
        weights = {
            'liquidity': 0.25,
            'ter': 0.20,
            'aum': 0.20,
            'tracking_error': 0.20,
            'nav_premium': 0.15
        }
        
        total = (
            self.liquidity_score * weights['liquidity'] +
            self.ter_score * weights['ter'] +
            self.aum_score * weights['aum'] +
            self.tracking_error_score * weights['tracking_error'] +
            self.nav_premium_score * weights['nav_premium']
        )
        
        return min(100, max(0, total))

@dataclass
class RiskScore:
    """Score de risque"""
    volatility_score: float = 0.0
    correlation_score: float = 0.0
    drawdown_score: float = 0.0
    beta_score: float = 0.0
    
    @property
    def total_score(self) -> float:
        """Score de risque total (plus haut = moins risqué)"""
        weights = {
            'volatility': 0.30,
            'correlation': 0.25,
            'drawdown': 0.25,
            'beta': 0.20
        }
        
        total = (
            self.volatility_score * weights['volatility'] +
            self.correlation_score * weights['correlation'] +
            self.drawdown_score * weights['drawdown'] +
            self.beta_score * weights['beta']
        )
        
        return min(100, max(0, total))

@dataclass
class AdvancedSignal:
    """Signal avancé avec scoring détaillé"""
    etf_isin: str
    signal_type: SignalType
    algorithm_type: AlgorithmType
    confidence: float
    technical_score: TechnicalScore
    fundamental_score: FundamentalScore
    risk_score: RiskScore
    price_target: float
    stop_loss: float
    current_price: float
    expected_return: float
    risk_reward_ratio: float
    holding_period: int  # jours
    justification: str
    timestamp: datetime
    
    @property
    def composite_score(self) -> float:
        """Score composite final (0-100)"""
        weights = {
            'technical': 0.50,
            'fundamental': 0.30,
            'risk': 0.20
        }
        
        return (
            self.technical_score.total_score * weights['technical'] +
            self.fundamental_score.total_score * weights['fundamental'] +
            self.risk_score.total_score * weights['risk']
        )

class AdvancedTechnicalAnalyzer:
    """Analyseur technique avancé"""
    
    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Oscillateur Stochastique"""
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
        """Rate of Change (Momentum)"""
        return ((close / close.shift(period)) - 1) * 100
    
    @staticmethod
    def calculate_volume_profile(close: pd.Series, volume: pd.Series, bins: int = 20) -> Dict:
        """Volume Profile analysis"""
        price_range = close.max() - close.min()
        bin_size = price_range / bins
        
        volume_profile = {}
        for i in range(bins):
            price_level = close.min() + (i * bin_size)
            mask = (close >= price_level) & (close < price_level + bin_size)
            volume_profile[price_level] = volume[mask].sum()
        
        # Point de contrôle du volume (POC)
        poc_price = max(volume_profile, key=volume_profile.get)
        
        return {
            'volume_profile': volume_profile,
            'poc_price': poc_price,
            'value_area_high': None,  # Simplified
            'value_area_low': None
        }

class AdvancedSignalGenerator:
    """Générateur de signaux avancé selon le cahier des charges"""
    
    def __init__(self):
        self.analyzer = AdvancedTechnicalAnalyzer()
        self.min_confidence_threshold = 60.0
    
    def generate_advanced_signal(self, etf_isin: str, market_data: pd.DataFrame, etf_info: Dict) -> Optional[AdvancedSignal]:
        """Génère un signal avancé avec scoring détaillé"""
        
        if len(market_data) < 50:
            return None
        
        try:
            # Calcul des indicateurs techniques avancés
            technical_indicators = self._calculate_all_indicators(market_data)
            
            # Calcul des scores
            technical_score = self._calculate_technical_score(technical_indicators, market_data)
            fundamental_score = self._calculate_fundamental_score(etf_info)
            risk_score = self._calculate_risk_score(market_data, technical_indicators)
            
            # Score composite
            composite_score = (
                technical_score.total_score * 0.50 +
                fundamental_score.total_score * 0.30 +
                risk_score.total_score * 0.20
            )
            
            # Détermination du type de signal et algorithme
            signal_type, algorithm_type = self._determine_signal_algorithm(technical_indicators, composite_score)
            
            if signal_type == SignalType.WAIT:
                return None
            
            # Calcul des objectifs de prix
            current_price = market_data['close_price'].iloc[-1]
            price_target, stop_loss = self._calculate_advanced_targets(
                current_price, technical_indicators, signal_type, algorithm_type
            )
            
            # Calcul du risk/reward et période de détention
            expected_return = self._calculate_expected_return(current_price, price_target, signal_type)
            risk_reward_ratio = self._calculate_risk_reward_ratio(current_price, price_target, stop_loss, signal_type)
            holding_period = self._estimate_holding_period(algorithm_type, technical_indicators)
            
            # Justification du signal
            justification = self._generate_justification(
                signal_type, algorithm_type, technical_score, composite_score
            )
            
            return AdvancedSignal(
                etf_isin=etf_isin,
                signal_type=signal_type,
                algorithm_type=algorithm_type,
                confidence=composite_score,
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                risk_score=risk_score,
                price_target=price_target,
                stop_loss=stop_loss,
                current_price=current_price,
                expected_return=expected_return,
                risk_reward_ratio=risk_reward_ratio,
                holding_period=holding_period,
                justification=justification,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération signal pour {etf_isin}: {e}")
            return None
    
    def _calculate_all_indicators(self, data: pd.DataFrame) -> Dict:
        """Calcule tous les indicateurs techniques"""
        close = data['close_price']
        high = data['high_price']
        low = data['low_price']
        volume = data['volume']
        
        indicators = {}
        
        # Moyennes mobiles
        indicators['sma_20'] = close.rolling(20).mean()
        indicators['sma_50'] = close.rolling(50).mean()
        indicators['sma_200'] = close.rolling(200).mean()
        indicators['ema_12'] = close.ewm(span=12).mean()
        indicators['ema_26'] = close.ewm(span=26).mean()
        
        # Oscillateurs
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
        indicators['macd_signal'] = indicators['macd'].ewm(span=9).mean()
        indicators['macd_histogram'] = indicators['macd'] - indicators['macd_signal']
        
        # Bollinger Bands
        sma_bb = close.rolling(20).mean()
        std_bb = close.rolling(20).std()
        indicators['bb_upper'] = sma_bb + (2 * std_bb)
        indicators['bb_lower'] = sma_bb - (2 * std_bb)
        indicators['bb_middle'] = sma_bb
        
        # Williams %R et Stochastique
        indicators['williams_r'] = self.analyzer.calculate_williams_r(high, low, close)
        stoch = self.analyzer.calculate_stochastic(high, low, close)
        indicators.update(stoch)
        
        # Rate of Change
        indicators['roc'] = self.analyzer.calculate_rate_of_change(close)
        
        # Volume indicators
        indicators['volume_sma'] = volume.rolling(20).mean()
        indicators['volume_ratio'] = volume / indicators['volume_sma']
        
        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        indicators['atr'] = true_range.rolling(14).mean()
        
        return indicators
    
    def _calculate_technical_score(self, indicators: Dict, data: pd.DataFrame) -> TechnicalScore:
        """Calcule le score technique détaillé"""
        
        # RSI Score
        rsi = indicators['rsi'].iloc[-1] if not pd.isna(indicators['rsi'].iloc[-1]) else 50
        if rsi < 30:
            rsi_score = 80 + (30 - rsi)  # Oversold = bullish
        elif rsi > 70:
            rsi_score = 30 - (rsi - 70)  # Overbought = bearish
        else:
            rsi_score = 50 + (50 - rsi) * 0.5  # Neutral zone
        
        # MACD Score
        macd = indicators['macd'].iloc[-1] if not pd.isna(indicators['macd'].iloc[-1]) else 0
        macd_signal = indicators['macd_signal'].iloc[-1] if not pd.isna(indicators['macd_signal'].iloc[-1]) else 0
        macd_score = 60 if macd > macd_signal else 40
        
        # Bollinger Score
        current_price = data['close_price'].iloc[-1]
        bb_upper = indicators['bb_upper'].iloc[-1] if not pd.isna(indicators['bb_upper'].iloc[-1]) else current_price
        bb_lower = indicators['bb_lower'].iloc[-1] if not pd.isna(indicators['bb_lower'].iloc[-1]) else current_price
        
        if current_price < bb_lower:
            bollinger_score = 75  # Oversold
        elif current_price > bb_upper:
            bollinger_score = 25  # Overbought
        else:
            bollinger_score = 50
        
        # Volume Score
        volume_ratio = indicators['volume_ratio'].iloc[-1] if not pd.isna(indicators['volume_ratio'].iloc[-1]) else 1
        volume_score = min(80, 30 + (volume_ratio * 30))
        
        # Momentum Score (ROC)
        roc = indicators['roc'].iloc[-1] if not pd.isna(indicators['roc'].iloc[-1]) else 0
        momentum_score = 50 + min(25, max(-25, roc * 2))
        
        # Moving Average Score
        sma_20 = indicators['sma_20'].iloc[-1] if not pd.isna(indicators['sma_20'].iloc[-1]) else current_price
        sma_50 = indicators['sma_50'].iloc[-1] if not pd.isna(indicators['sma_50'].iloc[-1]) else current_price
        
        ma_score = 50
        if current_price > sma_20 > sma_50:
            ma_score = 75
        elif current_price < sma_20 < sma_50:
            ma_score = 25
        
        # Williams %R Score
        williams_r = indicators['williams_r'].iloc[-1] if not pd.isna(indicators['williams_r'].iloc[-1]) else -50
        if williams_r < -80:
            williams_r_score = 75  # Oversold
        elif williams_r > -20:
            williams_r_score = 25  # Overbought
        else:
            williams_r_score = 50
        
        # Stochastic Score
        stoch_k = indicators['stoch_k'].iloc[-1] if not pd.isna(indicators['stoch_k'].iloc[-1]) else 50
        if stoch_k < 20:
            stochastic_score = 75
        elif stoch_k > 80:
            stochastic_score = 25
        else:
            stochastic_score = 50
        
        return TechnicalScore(
            rsi_score=max(0, min(100, rsi_score)),
            macd_score=max(0, min(100, macd_score)),
            bollinger_score=max(0, min(100, bollinger_score)),
            volume_score=max(0, min(100, volume_score)),
            momentum_score=max(0, min(100, momentum_score)),
            moving_average_score=max(0, min(100, ma_score)),
            williams_r_score=max(0, min(100, williams_r_score)),
            stochastic_score=max(0, min(100, stochastic_score))
        )
    
    def _calculate_fundamental_score(self, etf_info: Dict) -> FundamentalScore:
        """Calcule le score fondamental"""
        
        # Liquidity Score (basé sur l'AUM)
        aum = etf_info.get('aum', 1000000000)  # Default 1B
        if aum > 10000000000:  # > 10B
            liquidity_score = 90
        elif aum > 1000000000:  # > 1B
            liquidity_score = 70
        elif aum > 100000000:  # > 100M
            liquidity_score = 50
        else:
            liquidity_score = 30
        
        # TER Score (Total Expense Ratio)
        ter = etf_info.get('ter', 0.01)
        if ter < 0.005:  # < 0.5%
            ter_score = 90
        elif ter < 0.01:  # < 1%
            ter_score = 70
        elif ter < 0.02:  # < 2%
            ter_score = 50
        else:
            ter_score = 30
        
        # AUM Score
        aum_score = liquidity_score  # Same logic
        
        # Tracking Error Score (simplified)
        tracking_error_score = 70  # Default good score
        
        # NAV Premium Score (simplified)
        nav_premium_score = 60  # Default neutral
        
        return FundamentalScore(
            liquidity_score=liquidity_score,
            ter_score=ter_score,
            aum_score=aum_score,
            tracking_error_score=tracking_error_score,
            nav_premium_score=nav_premium_score
        )
    
    def _calculate_risk_score(self, data: pd.DataFrame, indicators: Dict) -> RiskScore:
        """Calcule le score de risque"""
        
        # Volatility Score (basé sur ATR)
        atr = indicators['atr'].iloc[-1] if not pd.isna(indicators['atr'].iloc[-1]) else 0
        current_price = data['close_price'].iloc[-1]
        volatility_ratio = atr / current_price if current_price > 0 else 0
        
        if volatility_ratio < 0.02:  # Low vol
            volatility_score = 80
        elif volatility_ratio < 0.05:  # Medium vol
            volatility_score = 60
        else:  # High vol
            volatility_score = 30
        
        # Correlation Score (simplified)
        correlation_score = 60
        
        # Drawdown Score (simplified)
        returns = data['close_price'].pct_change().dropna()
        if len(returns) > 0:
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = abs(drawdown.min())
            
            if max_drawdown < 0.05:  # < 5%
                drawdown_score = 80
            elif max_drawdown < 0.10:  # < 10%
                drawdown_score = 60
            elif max_drawdown < 0.20:  # < 20%
                drawdown_score = 40
            else:
                drawdown_score = 20
        else:
            drawdown_score = 50
        
        # Beta Score (simplified)
        beta_score = 60  # Default neutral
        
        return RiskScore(
            volatility_score=volatility_score,
            correlation_score=correlation_score,
            drawdown_score=drawdown_score,
            beta_score=beta_score
        )
    
    def _determine_signal_algorithm(self, indicators: Dict, composite_score: float) -> Tuple[SignalType, AlgorithmType]:
        """Détermine le type de signal et l'algorithme"""
        
        if composite_score < self.min_confidence_threshold:
            return SignalType.WAIT, AlgorithmType.MOMENTUM
        
        # Breakout detection
        current_price = indicators.get('close_price', 0)
        bb_upper = indicators.get('bb_upper', pd.Series([0])).iloc[-1]
        bb_lower = indicators.get('bb_lower', pd.Series([0])).iloc[-1]
        
        if not pd.isna(bb_upper) and not pd.isna(bb_lower):
            if current_price > bb_upper:
                return SignalType.BUY, AlgorithmType.BREAKOUT
            elif current_price < bb_lower:
                return SignalType.SELL, AlgorithmType.BREAKOUT
        
        # Mean Reversion
        rsi = indicators.get('rsi', pd.Series([50])).iloc[-1]
        if not pd.isna(rsi):
            if rsi < 30 and composite_score > 70:
                return SignalType.BUY, AlgorithmType.MEAN_REVERSION
            elif rsi > 70 and composite_score < 40:
                return SignalType.SELL, AlgorithmType.MEAN_REVERSION
        
        # Momentum
        if composite_score > 75:
            return SignalType.BUY, AlgorithmType.MOMENTUM
        elif composite_score < 30:
            return SignalType.SELL, AlgorithmType.MOMENTUM
        elif composite_score > 60:
            return SignalType.HOLD, AlgorithmType.MOMENTUM
        
        return SignalType.WAIT, AlgorithmType.MOMENTUM
    
    def _calculate_advanced_targets(self, current_price: float, indicators: Dict, 
                                  signal_type: SignalType, algorithm_type: AlgorithmType) -> Tuple[float, float]:
        """Calcule les objectifs de prix avancés"""
        
        atr = indicators.get('atr', pd.Series([current_price * 0.02])).iloc[-1]
        if pd.isna(atr):
            atr = current_price * 0.02
        
        if signal_type == SignalType.BUY:
            if algorithm_type == AlgorithmType.BREAKOUT:
                price_target = current_price * 1.08  # 8% target
                stop_loss = current_price * 0.95     # 5% stop
            elif algorithm_type == AlgorithmType.MEAN_REVERSION:
                bb_middle = indicators.get('bb_middle', pd.Series([current_price])).iloc[-1]
                price_target = bb_middle if not pd.isna(bb_middle) else current_price * 1.05
                stop_loss = current_price - (2 * atr)
            else:  # MOMENTUM
                price_target = current_price * 1.06  # 6% target
                stop_loss = current_price - (1.5 * atr)
                
        elif signal_type == SignalType.SELL:
            if algorithm_type == AlgorithmType.BREAKOUT:
                price_target = current_price * 0.92  # 8% target down
                stop_loss = current_price * 1.05     # 5% stop up
            else:
                price_target = current_price * 0.95  # 5% target down
                stop_loss = current_price + (1.5 * atr)
        else:
            price_target = current_price * 1.02
            stop_loss = current_price * 0.98
        
        return round(price_target, 4), round(stop_loss, 4)
    
    def _calculate_expected_return(self, current_price: float, price_target: float, signal_type: SignalType) -> float:
        """Calcule le rendement attendu"""
        if signal_type == SignalType.BUY:
            return ((price_target - current_price) / current_price) * 100
        elif signal_type == SignalType.SELL:
            return ((current_price - price_target) / current_price) * 100
        else:
            return 0.0
    
    def _calculate_risk_reward_ratio(self, current_price: float, price_target: float, 
                                   stop_loss: float, signal_type: SignalType) -> float:
        """Calcule le ratio risque/rendement"""
        if signal_type == SignalType.BUY:
            potential_gain = price_target - current_price
            potential_loss = current_price - stop_loss
        elif signal_type == SignalType.SELL:
            potential_gain = current_price - price_target
            potential_loss = stop_loss - current_price
        else:
            return 1.0
        
        if potential_loss > 0:
            return round(potential_gain / potential_loss, 2)
        else:
            return 0.0
    
    def _estimate_holding_period(self, algorithm_type: AlgorithmType, indicators: Dict) -> int:
        """Estime la période de détention en jours"""
        if algorithm_type == AlgorithmType.BREAKOUT:
            return 5  # Court terme
        elif algorithm_type == AlgorithmType.MEAN_REVERSION:
            return 3  # Très court terme
        elif algorithm_type == AlgorithmType.MOMENTUM:
            return 10  # Moyen terme
        else:
            return 7   # Default
    
    def _generate_justification(self, signal_type: SignalType, algorithm_type: AlgorithmType,
                              technical_score: TechnicalScore, composite_score: float) -> str:
        """Génère la justification du signal"""
        
        algo_name = {
            AlgorithmType.BREAKOUT: "Cassure",
            AlgorithmType.MEAN_REVERSION: "Retour à la moyenne",
            AlgorithmType.MOMENTUM: "Momentum",
            AlgorithmType.STATISTICAL_ARBITRAGE: "Arbitrage statistique"
        }
        
        main_indicators = []
        if technical_score.rsi_score > 70:
            main_indicators.append("RSI favorable")
        if technical_score.macd_score > 60:
            main_indicators.append("MACD positif")
        if technical_score.volume_score > 60:
            main_indicators.append("Volume élevé")
        
        justification = f"Signal {signal_type.value} - Algorithme {algo_name.get(algorithm_type, 'Momentum')}. "
        justification += f"Score composite: {composite_score:.1f}/100. "
        
        if main_indicators:
            justification += f"Indicateurs clés: {', '.join(main_indicators)}."
        
        return justification