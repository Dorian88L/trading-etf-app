"""
Algorithmes de trading avancés pour la génération de signaux
Implémente: Breakout, Mean Reversion, Momentum, Arbitrage Statistique
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"

class StrategyType(Enum):
    BREAKOUT = "BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    STATISTICAL_ARBITRAGE = "STATISTICAL_ARBITRAGE"

@dataclass
class TradingSignal:
    etf_isin: str
    signal_type: SignalType
    strategy: StrategyType
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    expected_return: float
    risk_score: float
    timeframe: str
    reasons: List[str]
    technical_score: float
    generated_at: datetime

class TradingAlgorithms:
    def __init__(self):
        self.min_confidence = 60.0
        self.max_risk_score = 70.0
        
        # Paramètres des stratégies
        self.breakout_params = {
            'lookback_period': 20,
            'volume_threshold': 1.5,
            'breakout_threshold': 0.02,  # 2%
            'confirmation_period': 3
        }
        
        self.mean_reversion_params = {
            'lookback_period': 20,
            'zscore_threshold': 2.0,
            'min_deviation': 0.05,  # 5%
            'reversion_period': 10
        }
        
        self.momentum_params = {
            'short_period': 12,
            'long_period': 26,
            'signal_period': 9,
            'momentum_threshold': 0.03,  # 3%
            'trend_confirmation': 5
        }
        
        self.arbitrage_params = {
            'correlation_threshold': 0.7,
            'spread_threshold': 2.0,
            'lookback_period': 60,
            'half_life': 10
        }

    async def generate_breakout_signals(self, market_data: pd.DataFrame, etf_isin: str) -> Optional[TradingSignal]:
        """
        Stratégie de breakout - détecte les cassures de niveaux clés
        """
        try:
            if len(market_data) < self.breakout_params['lookback_period']:
                return None
                
            # Calcul des niveaux de support et résistance
            high_prices = market_data['high'].rolling(self.breakout_params['lookback_period'])
            low_prices = market_data['low'].rolling(self.breakout_params['lookback_period'])
            
            resistance = high_prices.max()
            support = low_prices.min()
            
            current_price = market_data['close'].iloc[-1]
            current_volume = market_data['volume'].iloc[-1]
            avg_volume = market_data['volume'].rolling(20).mean().iloc[-1]
            
            # Détection du breakout
            breakout_up = current_price > resistance.iloc[-1] * (1 + self.breakout_params['breakout_threshold'])
            breakout_down = current_price < support.iloc[-1] * (1 - self.breakout_params['breakout_threshold'])
            volume_confirmation = current_volume > avg_volume * self.breakout_params['volume_threshold']
            
            if not (breakout_up or breakout_down) or not volume_confirmation:
                return None
            
            # Calcul des indicateurs techniques pour la confiance
            rsi = self._calculate_rsi(market_data['close'])
            macd_line, macd_signal = self._calculate_macd(market_data['close'])
            
            signal_type = SignalType.BUY if breakout_up else SignalType.SELL
            
            # Calcul des niveaux de prix
            if signal_type == SignalType.BUY:
                target_price = current_price * 1.08  # 8% de profit
                stop_loss = support.iloc[-1]
                confidence = 70 + min(30, (current_price / resistance.iloc[-1] - 1) * 500)
            else:
                target_price = current_price * 0.92  # 8% de profit en short
                stop_loss = resistance.iloc[-1]
                confidence = 70 + min(30, (1 - current_price / support.iloc[-1]) * 500)
            
            # Ajustement de la confiance avec les indicateurs
            if signal_type == SignalType.BUY:
                if rsi < 70:  # Pas suracheté
                    confidence += 5
                if macd_line > macd_signal:  # MACD positif
                    confidence += 10
            else:
                if rsi > 30:  # Pas survendu
                    confidence += 5
                if macd_line < macd_signal:  # MACD négatif
                    confidence += 10
            
            confidence = min(95, confidence)
            expected_return = abs(target_price - current_price) / current_price
            risk_score = min(80, abs(stop_loss - current_price) / current_price * 100)
            
            reasons = [
                f"Breakout {'haussier' if breakout_up else 'baissier'} confirmé",
                f"Volume +{((current_volume/avg_volume-1)*100):.0f}% vs moyenne",
                f"Prix {'> résistance' if breakout_up else '< support'} {resistance.iloc[-1] if breakout_up else support.iloc[-1]:.2f}"
            ]
            
            return TradingSignal(
                etf_isin=etf_isin,
                signal_type=signal_type,
                strategy=StrategyType.BREAKOUT,
                confidence=confidence,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                expected_return=expected_return,
                risk_score=risk_score,
                timeframe="1D",
                reasons=reasons,
                technical_score=self._calculate_technical_score(market_data),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération signal breakout pour {etf_isin}: {e}")
            return None

    async def generate_mean_reversion_signals(self, market_data: pd.DataFrame, etf_isin: str) -> Optional[TradingSignal]:
        """
        Stratégie de retour à la moyenne
        """
        try:
            if len(market_data) < self.mean_reversion_params['lookback_period']:
                return None
                
            # Calcul de la moyenne mobile et écart-type
            period = self.mean_reversion_params['lookback_period']
            sma = market_data['close'].rolling(period).mean()
            std = market_data['close'].rolling(period).std()
            
            current_price = market_data['close'].iloc[-1]
            current_sma = sma.iloc[-1]
            current_std = std.iloc[-1]
            
            # Calcul du Z-Score
            z_score = (current_price - current_sma) / current_std
            
            # Vérification des conditions de mean reversion
            threshold = self.mean_reversion_params['zscore_threshold']
            min_dev = self.mean_reversion_params['min_deviation']
            
            deviation = abs(current_price - current_sma) / current_sma
            
            if abs(z_score) < threshold or deviation < min_dev:
                return None
            
            # Signal de retour à la moyenne
            signal_type = SignalType.SELL if z_score > threshold else SignalType.BUY
            
            # Calcul des niveaux
            target_price = current_sma  # Retour à la moyenne
            
            if signal_type == SignalType.BUY:
                stop_loss = current_price * 0.95  # 5% de protection
                confidence = 60 + min(30, abs(z_score) * 10)
            else:
                stop_loss = current_price * 1.05  # 5% de protection
                confidence = 60 + min(30, abs(z_score) * 10)
            
            # Confirmation avec RSI
            rsi = self._calculate_rsi(market_data['close'])
            if signal_type == SignalType.BUY and rsi < 30:
                confidence += 10
            elif signal_type == SignalType.SELL and rsi > 70:
                confidence += 10
            
            # Confirmation avec volume
            volume_sma = market_data['volume'].rolling(20).mean().iloc[-1]
            current_volume = market_data['volume'].iloc[-1]
            if current_volume > volume_sma:
                confidence += 5
            
            confidence = min(95, confidence)
            expected_return = abs(target_price - current_price) / current_price
            risk_score = abs(stop_loss - current_price) / current_price * 100
            
            reasons = [
                f"Z-Score extrême: {z_score:.2f}",
                f"Déviation de {deviation*100:.1f}% vs moyenne",
                f"RSI {'survente' if signal_type == SignalType.BUY else 'surachat'}: {rsi:.0f}"
            ]
            
            return TradingSignal(
                etf_isin=etf_isin,
                signal_type=signal_type,
                strategy=StrategyType.MEAN_REVERSION,
                confidence=confidence,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                expected_return=expected_return,
                risk_score=risk_score,
                timeframe="1D",
                reasons=reasons,
                technical_score=self._calculate_technical_score(market_data),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération signal mean reversion pour {etf_isin}: {e}")
            return None

    async def generate_momentum_signals(self, market_data: pd.DataFrame, etf_isin: str) -> Optional[TradingSignal]:
        """
        Stratégie de momentum - suit les tendances fortes
        """
        try:
            min_length = max(self.momentum_params['long_period'], 50)
            if len(market_data) < min_length:
                return None
                
            # Calcul des moyennes mobiles
            short_ma = market_data['close'].rolling(self.momentum_params['short_period']).mean()
            long_ma = market_data['close'].rolling(self.momentum_params['long_period']).mean()
            
            # MACD
            macd_line, macd_signal = self._calculate_macd(market_data['close'])
            
            current_price = market_data['close'].iloc[-1]
            
            # Détection du momentum
            ma_momentum = short_ma.iloc[-1] > long_ma.iloc[-1]
            macd_momentum = macd_line > macd_signal
            
            # Calcul de la force du momentum
            price_momentum = (current_price / market_data['close'].rolling(20).mean().iloc[-1] - 1)
            
            if abs(price_momentum) < self.momentum_params['momentum_threshold']:
                return None
            
            # Confirmation de tendance
            trend_days = 0
            for i in range(1, self.momentum_params['trend_confirmation'] + 1):
                if (market_data['close'].iloc[-i] > market_data['close'].iloc[-i-1]) == (price_momentum > 0):
                    trend_days += 1
            
            if trend_days < 3:  # Besoin d'au moins 3 jours de confirmation
                return None
            
            signal_type = SignalType.BUY if price_momentum > 0 else SignalType.SELL
            
            # Calcul des niveaux
            if signal_type == SignalType.BUY:
                target_price = current_price * (1 + abs(price_momentum) * 2)  # Projection momentum
                stop_loss = long_ma.iloc[-1]
                confidence = 65
            else:
                target_price = current_price * (1 - abs(price_momentum) * 2)
                stop_loss = long_ma.iloc[-1]
                confidence = 65
            
            # Ajustements de confiance
            if ma_momentum == (signal_type == SignalType.BUY):
                confidence += 10
            if macd_momentum == (signal_type == SignalType.BUY):
                confidence += 10
            confidence += min(15, trend_days * 3)
            
            # Volume confirmation
            volume_trend = market_data['volume'].rolling(5).mean().iloc[-1] > market_data['volume'].rolling(20).mean().iloc[-1]
            if volume_trend:
                confidence += 5
            
            confidence = min(95, confidence)
            expected_return = abs(target_price - current_price) / current_price
            risk_score = abs(stop_loss - current_price) / current_price * 100
            
            reasons = [
                f"Momentum {'haussier' if signal_type == SignalType.BUY else 'baissier'} de {price_momentum*100:.1f}%",
                f"Tendance confirmée sur {trend_days} jours",
                f"MACD {'positif' if macd_momentum else 'négatif'}"
            ]
            
            return TradingSignal(
                etf_isin=etf_isin,
                signal_type=signal_type,
                strategy=StrategyType.MOMENTUM,
                confidence=confidence,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                expected_return=expected_return,
                risk_score=risk_score,
                timeframe="1D",
                reasons=reasons,
                technical_score=self._calculate_technical_score(market_data),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération signal momentum pour {etf_isin}: {e}")
            return None

    async def generate_statistical_arbitrage_signals(self, 
                                                   etf_data: Dict[str, pd.DataFrame],
                                                   target_etf: str) -> Optional[TradingSignal]:
        """
        Arbitrage statistique - pairs trading entre ETF corrélés
        """
        try:
            if target_etf not in etf_data or len(etf_data) < 2:
                return None
                
            target_prices = etf_data[target_etf]['close']
            
            # Recherche du meilleur pair
            best_correlation = 0
            best_pair = None
            
            for etf_isin, data in etf_data.items():
                if etf_isin == target_etf:
                    continue
                    
                # Alignement des données
                common_dates = target_prices.index.intersection(data['close'].index)
                if len(common_dates) < self.arbitrage_params['lookback_period']:
                    continue
                
                corr = target_prices.loc[common_dates].corr(data['close'].loc[common_dates])
                
                if corr > best_correlation and corr > self.arbitrage_params['correlation_threshold']:
                    best_correlation = corr
                    best_pair = (etf_isin, data['close'].loc[common_dates])
            
            if best_pair is None:
                return None
            
            pair_etf, pair_prices = best_pair
            common_dates = target_prices.index.intersection(pair_prices.index)
            
            # Calcul du spread normalisé
            target_norm = target_prices.loc[common_dates] / target_prices.loc[common_dates].iloc[0]
            pair_norm = pair_prices.loc[common_dates] / pair_prices.loc[common_dates].iloc[0]
            spread = target_norm - pair_norm
            
            # Z-score du spread
            spread_mean = spread.rolling(self.arbitrage_params['lookback_period']).mean()
            spread_std = spread.rolling(self.arbitrage_params['lookback_period']).std()
            z_score = (spread.iloc[-1] - spread_mean.iloc[-1]) / spread_std.iloc[-1]
            
            if abs(z_score) < self.arbitrage_params['spread_threshold']:
                return None
            
            current_price = target_prices.iloc[-1]
            signal_type = SignalType.SELL if z_score > 0 else SignalType.BUY
            
            # Calcul de la convergence attendue
            mean_reversion_target = spread_mean.iloc[-1]
            expected_spread_change = mean_reversion_target - spread.iloc[-1]
            
            # Prix cible basé sur la convergence du spread
            target_price = current_price + (expected_spread_change * current_price)
            
            # Stop loss basé sur l'extension du spread
            if signal_type == SignalType.BUY:
                stop_loss = current_price * 0.97
            else:
                stop_loss = current_price * 1.03
            
            # Confiance basée sur la corrélation et le z-score
            confidence = 50 + min(20, best_correlation * 20) + min(25, abs(z_score) * 5)
            
            expected_return = abs(target_price - current_price) / current_price
            risk_score = abs(stop_loss - current_price) / current_price * 100
            
            reasons = [
                f"Arbitrage vs {pair_etf} (corr: {best_correlation:.2f})",
                f"Z-score spread: {z_score:.2f}",
                f"Convergence attendue: {expected_spread_change*100:.1f}%"
            ]
            
            return TradingSignal(
                etf_isin=target_etf,
                signal_type=signal_type,
                strategy=StrategyType.STATISTICAL_ARBITRAGE,
                confidence=confidence,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                expected_return=expected_return,
                risk_score=risk_score,
                timeframe="1D",
                reasons=reasons,
                technical_score=self._calculate_technical_score(etf_data[target_etf]),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération signal arbitrage pour {target_etf}: {e}")
            return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcul du RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """Calcul du MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            macd_signal = macd_line.ewm(span=signal).mean()
            return macd_line.iloc[-1], macd_signal.iloc[-1]
        except:
            return 0, 0

    def _calculate_technical_score(self, market_data: pd.DataFrame) -> float:
        """Calcul d'un score technique global"""
        try:
            score = 50
            
            # RSI
            rsi = self._calculate_rsi(market_data['close'])
            if 30 <= rsi <= 70:
                score += 10
            elif 20 <= rsi < 30 or 70 < rsi <= 80:
                score += 5
            
            # MACD
            macd_line, macd_signal = self._calculate_macd(market_data['close'])
            if macd_line > macd_signal:
                score += 10
            
            # Trend (SMA)
            sma_20 = market_data['close'].rolling(20).mean().iloc[-1]
            sma_50 = market_data['close'].rolling(50).mean().iloc[-1] if len(market_data) >= 50 else sma_20
            current_price = market_data['close'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                score += 15
            elif current_price > sma_20:
                score += 10
            
            # Volume
            current_volume = market_data['volume'].iloc[-1]
            avg_volume = market_data['volume'].rolling(20).mean().iloc[-1]
            if current_volume > avg_volume:
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Erreur calcul score technique: {e}")
            return 50

    async def generate_all_signals(self, market_data: pd.DataFrame, etf_isin: str, 
                                 related_etfs: Optional[Dict[str, pd.DataFrame]] = None) -> List[TradingSignal]:
        """
        Génère tous les types de signaux pour un ETF
        """
        signals = []
        
        try:
            # Breakout
            breakout_signal = await self.generate_breakout_signals(market_data, etf_isin)
            if breakout_signal and breakout_signal.confidence >= self.min_confidence:
                signals.append(breakout_signal)
            
            # Mean Reversion
            mr_signal = await self.generate_mean_reversion_signals(market_data, etf_isin)
            if mr_signal and mr_signal.confidence >= self.min_confidence:
                signals.append(mr_signal)
            
            # Momentum
            momentum_signal = await self.generate_momentum_signals(market_data, etf_isin)
            if momentum_signal and momentum_signal.confidence >= self.min_confidence:
                signals.append(momentum_signal)
            
            # Statistical Arbitrage (si données des ETF corrélés disponibles)
            if related_etfs:
                related_etfs[etf_isin] = market_data
                arb_signal = await self.generate_statistical_arbitrage_signals(related_etfs, etf_isin)
                if arb_signal and arb_signal.confidence >= self.min_confidence:
                    signals.append(arb_signal)
            
            # Tri par confiance décroissante
            signals.sort(key=lambda x: x.confidence, reverse=True)
            
            return signals
            
        except Exception as e:
            logger.error(f"Erreur génération signaux pour {etf_isin}: {e}")
            return []

    def filter_signals_by_risk(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filtre les signaux selon les critères de risque
        """
        return [
            signal for signal in signals 
            if signal.risk_score <= self.max_risk_score and signal.confidence >= self.min_confidence
        ]

    def get_portfolio_signals(self, signals: List[TradingSignal], max_correlation: float = 0.7) -> List[TradingSignal]:
        """
        Sélectionne les signaux pour un portefeuille diversifié
        """
        if not signals:
            return []
        
        # Groupe par stratégie pour diversification
        strategy_groups = {}
        for signal in signals:
            if signal.strategy not in strategy_groups:
                strategy_groups[signal.strategy] = []
            strategy_groups[signal.strategy].append(signal)
        
        # Sélection du meilleur signal par stratégie
        portfolio_signals = []
        for strategy, strategy_signals in strategy_groups.items():
            # Tri par confiance et sélection du meilleur
            strategy_signals.sort(key=lambda x: x.confidence, reverse=True)
            if strategy_signals:
                portfolio_signals.append(strategy_signals[0])
        
        return portfolio_signals[:5]  # Maximum 5 signaux simultanés