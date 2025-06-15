"""
Service de Walk-Forward Analysis pour backtesting en conditions réelles
Optimise les paramètres sur une période puis teste sur la période suivante
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import itertools

# Import conditionally to avoid dependency issues during testing
try:
    from app.services.technical_indicators import TechnicalAnalysisService
except ImportError:
    TechnicalAnalysisService = None

try:
    from app.services.signal_generator import TradingSignalGenerator, SignalType
except ImportError:
    TradingSignalGenerator = None
    SignalType = None

logger = logging.getLogger(__name__)

@dataclass
class WalkForwardPeriod:
    """Période d'analyse walk-forward"""
    optimization_start: datetime
    optimization_end: datetime
    test_start: datetime
    test_end: datetime
    optimal_params: Dict[str, Any]
    test_performance: Dict[str, float]

@dataclass
class StrategyParameters:
    """Paramètres de stratégie à optimiser"""
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    sma_short: int = 20
    sma_long: int = 50
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04

class WalkForwardAnalysisService:
    """Service de Walk-Forward Analysis pour validation robuste des stratégies"""
    
    def __init__(self):
        # Initialize services conditionally
        self.technical_service = TechnicalAnalysisService() if TechnicalAnalysisService else None
        self.signal_generator = TradingSignalGenerator() if TradingSignalGenerator else None
        
    def run_walk_forward_analysis(
        self,
        historical_data: pd.DataFrame,
        strategy_type: str = "rsi_mean_reversion",
        optimization_window_days: int = 252,  # 1 an
        test_window_days: int = 63,  # 3 mois
        step_size_days: int = 21,  # 3 semaines
        param_ranges: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Exécute une analyse Walk-Forward complète
        
        Args:
            historical_data: Données historiques OHLCV
            strategy_type: Type de stratégie à tester
            optimization_window_days: Taille fenêtre d'optimisation
            test_window_days: Taille fenêtre de test
            step_size_days: Pas d'avancement
            param_ranges: Plages de paramètres à tester
            
        Returns:
            Résultats complets de l'analyse
        """
        try:
            logger.info(f"Démarrage Walk-Forward Analysis pour {strategy_type}")
            
            # Valider les données
            if len(historical_data) < optimization_window_days + test_window_days:
                raise ValueError("Données insuffisantes pour l'analyse")
            
            # Définir les plages de paramètres par défaut
            if param_ranges is None:
                param_ranges = self._get_default_param_ranges(strategy_type)
            
            # Générer les périodes Walk-Forward
            periods = self._generate_walk_forward_periods(
                historical_data, 
                optimization_window_days, 
                test_window_days, 
                step_size_days
            )
            
            logger.info(f"Génération de {len(periods)} périodes Walk-Forward")
            
            # Exécuter l'analyse pour chaque période
            results = []
            for i, period in enumerate(periods):
                logger.info(f"Analyse période {i+1}/{len(periods)}")
                
                period_result = self._analyze_single_period(
                    historical_data,
                    period,
                    strategy_type,
                    param_ranges
                )
                
                if period_result:
                    results.append(period_result)
            
            # Agréger les résultats
            aggregated_results = self._aggregate_walk_forward_results(results)
            
            logger.info("Walk-Forward Analysis terminée avec succès")
            return aggregated_results
            
        except Exception as e:
            logger.error(f"Erreur Walk-Forward Analysis: {e}")
            raise
    
    def _generate_walk_forward_periods(
        self,
        data: pd.DataFrame,
        opt_window: int,
        test_window: int,
        step_size: int
    ) -> List[Dict]:
        """Génère les périodes d'optimisation et de test"""
        periods = []
        
        start_idx = 0
        while start_idx + opt_window + test_window <= len(data):
            opt_start_idx = start_idx
            opt_end_idx = start_idx + opt_window
            test_start_idx = opt_end_idx
            test_end_idx = opt_end_idx + test_window
            
            periods.append({
                'opt_start_idx': opt_start_idx,
                'opt_end_idx': opt_end_idx,
                'test_start_idx': test_start_idx,
                'test_end_idx': test_end_idx,
                'opt_start_date': data.index[opt_start_idx],
                'opt_end_date': data.index[opt_end_idx-1],
                'test_start_date': data.index[test_start_idx],
                'test_end_date': data.index[test_end_idx-1]
            })
            
            start_idx += step_size
        
        return periods
    
    def _analyze_single_period(
        self,
        data: pd.DataFrame,
        period: Dict,
        strategy_type: str,
        param_ranges: Dict
    ) -> Optional[WalkForwardPeriod]:
        """Analyse une seule période Walk-Forward"""
        try:
            # Données d'optimisation
            opt_data = data.iloc[period['opt_start_idx']:period['opt_end_idx']]
            
            # Optimiser les paramètres
            optimal_params = self._optimize_parameters(
                opt_data, strategy_type, param_ranges
            )
            
            # Données de test
            test_data = data.iloc[period['test_start_idx']:period['test_end_idx']]
            
            # Tester avec les paramètres optimaux
            test_performance = self._backtest_with_params(
                test_data, strategy_type, optimal_params
            )
            
            return WalkForwardPeriod(
                optimization_start=period['opt_start_date'],
                optimization_end=period['opt_end_date'],
                test_start=period['test_start_date'],
                test_end=period['test_end_date'],
                optimal_params=optimal_params,
                test_performance=test_performance
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse période: {e}")
            return None
    
    def _optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        param_ranges: Dict
    ) -> Dict[str, Any]:
        """Optimise les paramètres de stratégie par grid search"""
        try:
            best_params = None
            best_score = -np.inf
            
            # Générer toutes les combinaisons de paramètres
            param_combinations = self._generate_param_combinations(param_ranges)
            
            # Limiter le nombre de combinaisons pour les performances
            if len(param_combinations) > 1000:
                param_combinations = param_combinations[:1000]
                logger.warning("Limitation à 1000 combinaisons pour les performances")
            
            # Tester chaque combinaison
            for params in param_combinations:
                try:
                    performance = self._backtest_with_params(data, strategy_type, params)
                    
                    # Score composite (Sharpe ratio pondéré par le nombre de trades)
                    sharpe = performance.get('sharpe_ratio', 0)
                    num_trades = performance.get('num_trades', 0)
                    min_trades = 5  # Minimum de trades requis
                    
                    if num_trades >= min_trades:
                        score = sharpe * min(1.0, num_trades / 20)  # Favoriser 20+ trades
                    else:
                        score = sharpe * 0.1  # Pénaliser peu de trades
                    
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
                        
                except Exception as e:
                    logger.debug(f"Erreur test paramètres {params}: {e}")
                    continue
            
            return best_params or self._get_default_params(strategy_type)
            
        except Exception as e:
            logger.error(f"Erreur optimisation paramètres: {e}")
            return self._get_default_params(strategy_type)
    
    def _generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Génère toutes les combinaisons de paramètres"""
        keys = list(param_ranges.keys())
        values = [param_ranges[key] for key in keys]
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        return combinations
    
    def _backtest_with_params(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, float]:
        """Exécute un backtest avec des paramètres spécifiques"""
        try:
            # Calculer les indicateurs avec les paramètres
            indicators = self._calculate_indicators_with_params(data, params)
            
            # Générer les signaux selon la stratégie
            signals = self._generate_signals_with_strategy(
                data, indicators, strategy_type, params
            )
            
            # Calculer les performances
            performance = self._calculate_performance_metrics(data, signals, params)
            
            return performance
            
        except Exception as e:
            logger.error(f"Erreur backtest: {e}")
            return {'sharpe_ratio': -10, 'total_return': -1, 'num_trades': 0}
    
    def _calculate_indicators_with_params(
        self, 
        data: pd.DataFrame, 
        params: Dict
    ) -> Dict[str, np.ndarray]:
        """Calcule les indicateurs techniques avec paramètres personnalisés"""
        indicators = {}
        
        # RSI
        if 'rsi_period' in params:
            indicators['rsi'] = self._calculate_rsi(
                data['close_price'], params['rsi_period']
            )
        
        # SMA
        if 'sma_short' in params and 'sma_long' in params:
            indicators['sma_short'] = self._calculate_sma(
                data['close_price'], params['sma_short']
            )
            indicators['sma_long'] = self._calculate_sma(
                data['close_price'], params['sma_long']
            )
        
        # MACD
        if all(k in params for k in ['macd_fast', 'macd_slow', 'macd_signal']):
            macd_data = self._calculate_macd(
                data['close_price'],
                params['macd_fast'],
                params['macd_slow'],
                params['macd_signal']
            )
            indicators.update(macd_data)
        
        # Bollinger Bands
        if 'bollinger_period' in params and 'bollinger_std' in params:
            bb_data = self._calculate_bollinger_bands(
                data['close_price'],
                params['bollinger_period'],
                params['bollinger_std']
            )
            indicators.update(bb_data)
        
        return indicators
    
    def _generate_signals_with_strategy(
        self,
        data: pd.DataFrame,
        indicators: Dict,
        strategy_type: str,
        params: Dict
    ) -> List[int]:
        """Génère les signaux selon la stratégie choisie"""
        signals = [0] * len(data)  # 0=hold, 1=buy, -1=sell
        
        if strategy_type == "rsi_mean_reversion":
            rsi = indicators.get('rsi', [])
            oversold = params.get('rsi_oversold', 30)
            overbought = params.get('rsi_overbought', 70)
            
            for i in range(len(rsi)):
                if len(rsi) > i and rsi[i] < oversold:
                    signals[i] = 1  # Buy signal
                elif len(rsi) > i and rsi[i] > overbought:
                    signals[i] = -1  # Sell signal
        
        elif strategy_type == "sma_crossover":
            sma_short = indicators.get('sma_short', [])
            sma_long = indicators.get('sma_long', [])
            
            for i in range(1, min(len(sma_short), len(sma_long), len(signals))):
                if (len(sma_short) > i and len(sma_long) > i and 
                    sma_short[i] > sma_long[i] and 
                    sma_short[i-1] <= sma_long[i-1]):
                    signals[i] = 1  # Golden cross
                elif (len(sma_short) > i and len(sma_long) > i and 
                      sma_short[i] < sma_long[i] and 
                      sma_short[i-1] >= sma_long[i-1]):
                    signals[i] = -1  # Death cross
        
        elif strategy_type == "bollinger_mean_reversion":
            bb_upper = indicators.get('bb_upper', [])
            bb_lower = indicators.get('bb_lower', [])
            prices = data['close_price'].values
            
            for i in range(min(len(prices), len(signals))):
                if len(bb_lower) > i and len(prices) > i and prices[i] < bb_lower[i]:
                    signals[i] = 1  # Price below lower band
                elif len(bb_upper) > i and len(prices) > i and prices[i] > bb_upper[i]:
                    signals[i] = -1  # Price above upper band
        
        return signals
    
    def _calculate_performance_metrics(
        self,
        data: pd.DataFrame,
        signals: List[int],
        params: Dict
    ) -> Dict[str, float]:
        """Calcule les métriques de performance"""
        try:
            prices = data['close_price'].values
            returns = []
            trades = []
            position = 0
            entry_price = 0
            
            stop_loss_pct = params.get('stop_loss_pct', 0.02)
            take_profit_pct = params.get('take_profit_pct', 0.04)
            
            for i in range(len(signals)):
                current_price = prices[i]
                
                # Vérifier stop loss et take profit
                if position != 0 and entry_price > 0:
                    price_change = (current_price - entry_price) / entry_price
                    
                    if position == 1:  # Long position
                        if price_change <= -stop_loss_pct:  # Stop loss
                            returns.append(-stop_loss_pct)
                            trades.append(-stop_loss_pct)
                            position = 0
                            continue
                        elif price_change >= take_profit_pct:  # Take profit
                            returns.append(take_profit_pct)
                            trades.append(take_profit_pct)
                            position = 0
                            continue
                    elif position == -1:  # Short position
                        if price_change >= stop_loss_pct:  # Stop loss
                            returns.append(-stop_loss_pct)
                            trades.append(-stop_loss_pct)
                            position = 0
                            continue
                        elif price_change <= -take_profit_pct:  # Take profit
                            returns.append(take_profit_pct)
                            trades.append(take_profit_pct)
                            position = 0
                            continue
                
                # Traiter les nouveaux signaux
                if signals[i] == 1 and position != 1:  # Buy signal
                    if position == -1:  # Close short
                        ret = (entry_price - current_price) / entry_price
                        returns.append(ret)
                        trades.append(ret)
                    position = 1
                    entry_price = current_price
                    
                elif signals[i] == -1 and position != -1:  # Sell signal
                    if position == 1:  # Close long
                        ret = (current_price - entry_price) / entry_price
                        returns.append(ret)
                        trades.append(ret)
                    position = -1
                    entry_price = current_price
            
            # Clôturer la position finale
            if position != 0 and entry_price > 0:
                final_price = prices[-1]
                if position == 1:
                    ret = (final_price - entry_price) / entry_price
                else:
                    ret = (entry_price - final_price) / entry_price
                returns.append(ret)
                trades.append(ret)
            
            # Calculer les métriques
            if not returns:
                return {'sharpe_ratio': -10, 'total_return': 0, 'num_trades': 0}
            
            total_return = np.prod([1 + r for r in returns]) - 1
            avg_return = np.mean(returns)
            volatility = np.std(returns) if len(returns) > 1 else 0
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            max_drawdown = self._calculate_max_drawdown(returns)
            win_rate = len([r for r in trades if r > 0]) / len(trades) if trades else 0
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'num_trades': len(trades),
                'win_rate': win_rate,
                'avg_return_per_trade': avg_return
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul performance: {e}")
            return {'sharpe_ratio': -10, 'total_return': -1, 'num_trades': 0}
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calcule le drawdown maximum"""
        cumulative = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return abs(np.min(drawdown))
    
    def _aggregate_walk_forward_results(
        self, 
        results: List[WalkForwardPeriod]
    ) -> Dict[str, Any]:
        """Agrège les résultats de toutes les périodes"""
        if not results:
            return {'error': 'Aucun résultat à agréger'}
        
        # Extraire les métriques de performance
        all_returns = []
        all_sharpe = []
        all_drawdowns = []
        all_num_trades = []
        all_win_rates = []
        
        for result in results:
            perf = result.test_performance
            all_returns.append(perf.get('total_return', 0))
            all_sharpe.append(perf.get('sharpe_ratio', 0))
            all_drawdowns.append(perf.get('max_drawdown', 0))
            all_num_trades.append(perf.get('num_trades', 0))
            all_win_rates.append(perf.get('win_rate', 0))
        
        # Calculer les statistiques agrégées
        cumulative_return = np.prod([1 + r for r in all_returns]) - 1
        avg_sharpe = np.mean(all_sharpe)
        max_drawdown = max(all_drawdowns) if all_drawdowns else 0
        total_trades = sum(all_num_trades)
        avg_win_rate = np.mean(all_win_rates)
        
        # Stabilité des paramètres (diversité)
        param_stability = self._calculate_parameter_stability(results)
        
        return {
            'summary': {
                'num_periods': len(results),
                'cumulative_return': cumulative_return,
                'average_sharpe_ratio': avg_sharpe,
                'maximum_drawdown': max_drawdown,
                'total_trades': total_trades,
                'average_win_rate': avg_win_rate,
                'parameter_stability': param_stability
            },
            'period_results': [
                {
                    'test_period': f"{r.test_start.date()} to {r.test_end.date()}",
                    'optimal_params': r.optimal_params,
                    'performance': r.test_performance
                }
                for r in results
            ],
            'robustness_score': self._calculate_robustness_score(results)
        }
    
    def _calculate_parameter_stability(self, results: List[WalkForwardPeriod]) -> float:
        """Calcule la stabilité des paramètres optimaux"""
        if len(results) < 2:
            return 1.0
        
        # Analyser la variance des paramètres numériques
        param_values = {}
        for result in results:
            for param, value in result.optimal_params.items():
                if isinstance(value, (int, float)):
                    if param not in param_values:
                        param_values[param] = []
                    param_values[param].append(value)
        
        # Calculer le coefficient de variation moyen
        cv_scores = []
        for param, values in param_values.items():
            if len(values) > 1 and np.mean(values) != 0:
                cv = np.std(values) / np.mean(values)
                cv_scores.append(1 / (1 + cv))  # Inversé: plus stable = score plus élevé
        
        return np.mean(cv_scores) if cv_scores else 0.5
    
    def _calculate_robustness_score(self, results: List[WalkForwardPeriod]) -> float:
        """Calcule un score de robustesse global"""
        if not results:
            return 0.0
        
        # Facteurs de robustesse
        positive_periods = len([r for r in results if r.test_performance.get('total_return', 0) > 0])
        consistency_score = positive_periods / len(results)
        
        sharpe_ratios = [r.test_performance.get('sharpe_ratio', 0) for r in results]
        sharpe_stability = 1 - (np.std(sharpe_ratios) / (abs(np.mean(sharpe_ratios)) + 0.1))
        
        param_stability = self._calculate_parameter_stability(results)
        
        # Score composite
        robustness = (consistency_score * 0.4 + 
                     max(0, sharpe_stability) * 0.3 + 
                     param_stability * 0.3)
        
        return min(1.0, max(0.0, robustness))
    
    # Méthodes utilitaires pour les calculs techniques
    def _calculate_rsi(self, prices: pd.Series, period: int) -> List[float]:
        """Calcule le RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).tolist()
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> List[float]:
        """Calcule la moyenne mobile simple"""
        return prices.rolling(window=period).mean().fillna(prices).tolist()
    
    def _calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, List[float]]:
        """Calcule le MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        
        return {
            'macd': macd.fillna(0).tolist(),
            'macd_signal': macd_signal.fillna(0).tolist(),
            'macd_histogram': macd_histogram.fillna(0).tolist()
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float) -> Dict[str, List[float]]:
        """Calcule les bandes de Bollinger"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        return {
            'bb_upper': (sma + std_dev * std).fillna(prices * 1.02).tolist(),
            'bb_middle': sma.fillna(prices).tolist(),
            'bb_lower': (sma - std_dev * std).fillna(prices * 0.98).tolist()
        }
    
    def _get_default_param_ranges(self, strategy_type: str) -> Dict[str, List]:
        """Retourne les plages de paramètres par défaut selon la stratégie"""
        base_ranges = {
            'rsi_period': [10, 14, 18, 22],
            'rsi_oversold': [20, 25, 30, 35],
            'rsi_overbought': [65, 70, 75, 80],
            'stop_loss_pct': [0.01, 0.02, 0.03, 0.04],
            'take_profit_pct': [0.02, 0.03, 0.04, 0.06]
        }
        
        if strategy_type == "sma_crossover":
            base_ranges.update({
                'sma_short': [10, 15, 20, 25],
                'sma_long': [40, 50, 60, 70]
            })
        elif strategy_type == "bollinger_mean_reversion":
            base_ranges.update({
                'bollinger_period': [15, 20, 25, 30],
                'bollinger_std': [1.5, 2.0, 2.5, 3.0]
            })
        elif strategy_type == "macd_momentum":
            base_ranges.update({
                'macd_fast': [8, 12, 16],
                'macd_slow': [21, 26, 31],
                'macd_signal': [6, 9, 12]
            })
        
        return base_ranges
    
    def _get_default_params(self, strategy_type: str) -> Dict[str, Any]:
        """Retourne les paramètres par défaut"""
        defaults = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        }
        
        if strategy_type == "sma_crossover":
            defaults.update({
                'sma_short': 20,
                'sma_long': 50
            })
        elif strategy_type == "bollinger_mean_reversion":
            defaults.update({
                'bollinger_period': 20,
                'bollinger_std': 2.0
            })
        elif strategy_type == "macd_momentum":
            defaults.update({
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            })
        
        return defaults

def get_walk_forward_service() -> WalkForwardAnalysisService:
    """Factory function pour le service Walk-Forward Analysis"""
    return WalkForwardAnalysisService()