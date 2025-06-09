"""
Service avancé de backtesting avec données réelles
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import time
import logging
from dataclasses import dataclass

from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.services.technical_analysis import TechnicalAnalysisService

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    date: datetime
    symbol: str
    action: str  # "BUY" or "SELL"
    quantity: float
    price: float
    value: float
    commission: float
    signal_reason: str
    confidence: float

@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    value: float
    unrealized_pnl: float
    realized_pnl: float

class AdvancedBacktestingService:
    def __init__(self, market_service: RealMarketDataService):
        self.market_service = market_service
        self.technical_analysis = TechnicalAnalysisService()
        
    async def run_backtest(self, config: Any, user_id: str) -> Dict[str, Any]:
        """
        Lance un backtest complet avec données réelles
        """
        start_time = time.time()
        backtest_id = str(uuid.uuid4())
        
        logger.info(f"Démarrage du backtest {backtest_id} pour l'utilisateur {user_id}")
        
        try:
            # 1. Récupérer les données de marché réelles
            market_data = await self._fetch_market_data(config)
            
            # 2. Valider les données
            if not market_data or len(market_data) == 0:
                raise ValueError("Aucune donnée de marché disponible pour la période sélectionnée")
            
            # 3. Initialiser le portfolio
            portfolio = self._initialize_portfolio(config.initial_capital)
            
            # 4. Exécuter la simulation
            trades, equity_curve = await self._run_simulation(config, market_data, portfolio)
            
            # 5. Calculer les métriques
            metrics = self._calculate_metrics(trades, equity_curve, config.initial_capital)
            
            # 6. Générer le rapport de comparaison avec benchmark
            benchmark_comparison = await self._calculate_benchmark_comparison(
                config, equity_curve, market_data
            )
            
            execution_time = time.time() - start_time
            
            result = {
                "id": backtest_id,
                "config": config.dict(),
                "total_return_pct": metrics["total_return_pct"],
                "annualized_return_pct": metrics["annualized_return_pct"],
                "volatility_pct": metrics["volatility_pct"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "win_rate_pct": metrics["win_rate_pct"],
                "number_of_trades": len(trades),
                "final_value": equity_curve[-1]["value"] if equity_curve else config.initial_capital,
                "trades": [self._trade_to_dict(trade) for trade in trades],
                "equity_curve": equity_curve,
                "risk_metrics": metrics["risk_metrics"],
                "benchmark_comparison": benchmark_comparison,
                "created_at": datetime.now(),
                "execution_time_seconds": execution_time
            }
            
            logger.info(f"Backtest {backtest_id} terminé en {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Erreur dans le backtest {backtest_id}: {str(e)}")
            raise

    async def _fetch_market_data(self, config: Any) -> Dict[str, pd.DataFrame]:
        """
        Récupère les données de marché réelles pour tous les ETFs
        """
        market_data = {}
        
        for symbol in config.etf_symbols:
            try:
                # Calculer la période appropriée
                period = self._calculate_period(config.start_date, config.end_date)
                
                # Récupérer les données via le service
                data = await self.market_service.get_historical_data(
                    symbol=symbol,
                    period=period,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
                
                if data and len(data) > 0:
                    # Convertir en DataFrame pandas
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    
                    # Filtrer par dates
                    start_dt = pd.to_datetime(config.start_date)
                    end_dt = pd.to_datetime(config.end_date)
                    df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                    
                    if len(df) > 0:
                        market_data[symbol] = df
                        logger.info(f"Données récupérées pour {symbol}: {len(df)} points")
                    else:
                        logger.warning(f"Aucune donnée dans la période pour {symbol}")
                else:
                    logger.warning(f"Impossible de récupérer les données pour {symbol}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données pour {symbol}: {e}")
                continue
        
        return market_data

    def _calculate_period(self, start_date: date, end_date: date) -> str:
        """
        Calcule la période appropriée pour l'API
        """
        diff = (end_date - start_date).days
        
        if diff <= 7:
            return "1w"
        elif diff <= 30:
            return "1mo"
        elif diff <= 90:
            return "3mo"
        elif diff <= 180:
            return "6mo"
        elif diff <= 365:
            return "1y"
        else:
            return "2y"

    def _initialize_portfolio(self, initial_capital: float) -> Dict[str, Any]:
        """
        Initialise le portfolio
        """
        return {
            "cash": initial_capital,
            "positions": {},
            "total_value": initial_capital,
            "initial_capital": initial_capital
        }

    async def _run_simulation(self, config: Any, market_data: Dict[str, pd.DataFrame], portfolio: Dict[str, Any]) -> Tuple[List[Trade], List[Dict[str, Any]]]:
        """
        Exécute la simulation de trading
        """
        trades = []
        equity_curve = []
        
        # Obtenir toutes les dates de trading uniques
        all_dates = set()
        for df in market_data.values():
            all_dates.update(df.index.date)
        trading_dates = sorted(all_dates)
        
        logger.info(f"Simulation sur {len(trading_dates)} jours de trading")
        
        for i, current_date in enumerate(trading_dates):
            current_datetime = datetime.combine(current_date, datetime.min.time())
            
            # Mettre à jour les prix actuels des positions
            self._update_portfolio_values(portfolio, market_data, current_date)
            
            # Générer des signaux de trading
            signals = await self._generate_trading_signals(
                config, market_data, current_date
            )
            
            # Exécuter les trades basés sur les signaux
            day_trades = self._execute_trades(
                config, portfolio, signals, market_data, current_date
            )
            trades.extend(day_trades)
            
            # Enregistrer la valeur du portfolio
            equity_point = {
                "date": current_date.isoformat(),
                "value": portfolio["total_value"],
                "cash": portfolio["cash"],
                "positions_value": sum(pos["value"] for pos in portfolio["positions"].values()),
                "daily_return": 0.0 if i == 0 else (
                    (portfolio["total_value"] - equity_curve[-1]["value"]) / equity_curve[-1]["value"] * 100
                ) if equity_curve else 0.0
            }
            equity_curve.append(equity_point)
            
            # Log du progrès
            if i % 50 == 0:
                logger.info(f"Simulation: {i}/{len(trading_dates)} jours - Valeur: {portfolio['total_value']:.2f}€")
        
        return trades, equity_curve

    def _update_portfolio_values(self, portfolio: Dict[str, Any], market_data: Dict[str, pd.DataFrame], current_date: date):
        """
        Met à jour les valeurs du portfolio avec les prix actuels
        """
        total_positions_value = 0
        
        for symbol, position in portfolio["positions"].items():
            if symbol in market_data:
                df = market_data[symbol]
                # Trouver le prix le plus récent disponible
                available_dates = df.index.date <= current_date
                if available_dates.any():
                    latest_data = df[available_dates].iloc[-1]
                    current_price = latest_data['close_price']
                    position["current_price"] = current_price
                    position["value"] = position["quantity"] * current_price
                    position["unrealized_pnl"] = (current_price - position["avg_price"]) * position["quantity"]
                    total_positions_value += position["value"]
        
        portfolio["total_value"] = portfolio["cash"] + total_positions_value

    async def _generate_trading_signals(self, config: Any, market_data: Dict[str, pd.DataFrame], current_date: date) -> List[Dict[str, Any]]:
        """
        Génère des signaux de trading basés sur la stratégie configurée
        """
        signals = []
        
        for symbol in config.etf_symbols:
            if symbol not in market_data:
                continue
                
            df = market_data[symbol]
            # Filtrer jusqu'à la date actuelle
            historical_data = df[df.index.date <= current_date]
            
            if len(historical_data) < 20:  # Minimum de données nécessaires
                continue
            
            try:
                signal = await self._calculate_signal(config.strategy_type, config.strategy_params, historical_data, symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Erreur calcul signal pour {symbol}: {e}")
                continue
        
        return signals

    async def _calculate_signal(self, strategy_type: str, params: Dict[str, Any], data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Calcule un signal de trading basé sur la stratégie
        """
        if len(data) < 20:
            return None
        
        try:
            if strategy_type == "rsi":
                return self._rsi_strategy(data, params.get("rsi", {}), symbol)
            elif strategy_type == "macd":
                return self._macd_strategy(data, params.get("macd", {}), symbol)
            elif strategy_type == "bollinger":
                return self._bollinger_strategy(data, params.get("bollinger", {}), symbol)
            elif strategy_type == "advanced":
                return await self._advanced_strategy(data, params, symbol)
            else:
                return None
        except Exception as e:
            logger.error(f"Erreur dans la stratégie {strategy_type} pour {symbol}: {e}")
            return None

    def _rsi_strategy(self, data: pd.DataFrame, params: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Stratégie basée sur RSI
        """
        period = params.get("period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)
        
        # Calculer RSI
        rsi_values = self.technical_analysis.calculate_rsi(data['close_price'].values, period)
        
        if len(rsi_values) == 0:
            return None
        
        current_rsi = rsi_values[-1]
        
        if current_rsi < oversold:
            return {
                "symbol": symbol,
                "action": "BUY",
                "confidence": min(95, (oversold - current_rsi) / oversold * 100 + 60),
                "reason": f"RSI en survente ({current_rsi:.1f})",
                "price": data['close_price'].iloc[-1]
            }
        elif current_rsi > overbought:
            return {
                "symbol": symbol,
                "action": "SELL",
                "confidence": min(95, (current_rsi - overbought) / (100 - overbought) * 100 + 60),
                "reason": f"RSI en surachat ({current_rsi:.1f})",
                "price": data['close_price'].iloc[-1]
            }
        
        return None

    def _macd_strategy(self, data: pd.DataFrame, params: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Stratégie basée sur MACD
        """
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)
        
        # Calculer MACD
        macd_result = self.technical_analysis.calculate_macd(
            data['close_price'].values, fast_period, slow_period, signal_period
        )
        
        if len(macd_result["macd"]) < 2:
            return None
        
        # Vérifier les croisements
        current_macd = macd_result["macd"][-1]
        current_signal = macd_result["signal"][-1]
        prev_macd = macd_result["macd"][-2]
        prev_signal = macd_result["signal"][-2]
        
        # Croisement haussier
        if prev_macd <= prev_signal and current_macd > current_signal:
            return {
                "symbol": symbol,
                "action": "BUY",
                "confidence": min(90, abs(current_macd - current_signal) * 1000 + 65),
                "reason": f"Croisement haussier MACD",
                "price": data['close_price'].iloc[-1]
            }
        # Croisement baissier
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return {
                "symbol": symbol,
                "action": "SELL",
                "confidence": min(90, abs(current_macd - current_signal) * 1000 + 65),
                "reason": f"Croisement baissier MACD",
                "price": data['close_price'].iloc[-1]
            }
        
        return None

    def _bollinger_strategy(self, data: pd.DataFrame, params: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Stratégie basée sur les Bandes de Bollinger
        """
        period = params.get("period", 20)
        deviation = params.get("deviation", 2.0)
        
        # Calculer les bandes de Bollinger
        bollinger = self.technical_analysis.calculate_bollinger_bands(
            data['close_price'].values, period, deviation
        )
        
        if len(bollinger["upper"]) == 0:
            return None
        
        current_price = data['close_price'].iloc[-1]
        upper_band = bollinger["upper"][-1]
        lower_band = bollinger["lower"][-1]
        middle_band = bollinger["middle"][-1]
        
        # Position relative dans les bandes
        band_width = upper_band - lower_band
        if band_width == 0:
            return None
        
        position_in_bands = (current_price - lower_band) / band_width
        
        # Signal d'achat près de la bande inférieure
        if position_in_bands < 0.2:
            return {
                "symbol": symbol,
                "action": "BUY",
                "confidence": min(90, (0.2 - position_in_bands) * 400 + 60),
                "reason": f"Prix près de la bande inférieure",
                "price": current_price
            }
        # Signal de vente près de la bande supérieure
        elif position_in_bands > 0.8:
            return {
                "symbol": symbol,
                "action": "SELL",
                "confidence": min(90, (position_in_bands - 0.8) * 400 + 60),
                "reason": f"Prix près de la bande supérieure",
                "price": current_price
            }
        
        return None

    async def _advanced_strategy(self, data: pd.DataFrame, params: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Stratégie avancée combinant plusieurs indicateurs
        """
        risk_level = params.get("risk_level", "moderate")
        
        # Combiner RSI, MACD et Bollinger
        rsi_signal = self._rsi_strategy(data, {"period": 14, "oversold": 30, "overbought": 70}, symbol)
        macd_signal = self._macd_strategy(data, {"fast_period": 12, "slow_period": 26, "signal_period": 9}, symbol)
        bollinger_signal = self._bollinger_strategy(data, {"period": 20, "deviation": 2.0}, symbol)
        
        signals = [s for s in [rsi_signal, macd_signal, bollinger_signal] if s is not None]
        
        if len(signals) < 2:
            return None
        
        # Vérifier la cohérence des signaux
        buy_signals = [s for s in signals if s["action"] == "BUY"]
        sell_signals = [s for s in signals if s["action"] == "SELL"]
        
        confidence_threshold = {"conservative": 80, "moderate": 70, "aggressive": 60}[risk_level]
        
        if len(buy_signals) >= 2:
            avg_confidence = sum(s["confidence"] for s in buy_signals) / len(buy_signals)
            if avg_confidence >= confidence_threshold:
                return {
                    "symbol": symbol,
                    "action": "BUY",
                    "confidence": min(95, avg_confidence),
                    "reason": f"Consensus haussier ({len(buy_signals)} indicateurs)",
                    "price": data['close_price'].iloc[-1]
                }
        
        elif len(sell_signals) >= 2:
            avg_confidence = sum(s["confidence"] for s in sell_signals) / len(sell_signals)
            if avg_confidence >= confidence_threshold:
                return {
                    "symbol": symbol,
                    "action": "SELL",
                    "confidence": min(95, avg_confidence),
                    "reason": f"Consensus baissier ({len(sell_signals)} indicateurs)",
                    "price": data['close_price'].iloc[-1]
                }
        
        return None

    def _execute_trades(self, config: Any, portfolio: Dict[str, Any], signals: List[Dict[str, Any]], market_data: Dict[str, pd.DataFrame], current_date: date) -> List[Trade]:
        """
        Exécute les trades basés sur les signaux
        """
        trades = []
        
        for signal in signals:
            symbol = signal["symbol"]
            action = signal["action"]
            price = signal["price"]
            confidence = signal["confidence"]
            
            # Vérifier les conditions d'exécution
            if confidence < 60:  # Seuil de confiance minimum
                continue
            
            try:
                if action == "BUY":
                    trade = self._execute_buy(config, portfolio, symbol, price, signal, current_date)
                elif action == "SELL":
                    trade = self._execute_sell(config, portfolio, symbol, price, signal, current_date)
                else:
                    continue
                
                if trade:
                    trades.append(trade)
                    logger.debug(f"Trade exécuté: {action} {symbol} à {price:.2f}€")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du trade {action} {symbol}: {e}")
                continue
        
        return trades

    def _execute_buy(self, config: Any, portfolio: Dict[str, Any], symbol: str, price: float, signal: Dict[str, Any], current_date: date) -> Optional[Trade]:
        """
        Exécute un ordre d'achat
        """
        # Calculer la taille de position maximale
        max_position_value = portfolio["total_value"] * (config.max_position_size_pct / 100)
        
        # Vérifier si on a déjà une position
        if symbol in portfolio["positions"]:
            current_position_value = portfolio["positions"][symbol]["value"]
            if current_position_value >= max_position_value:
                return None  # Position déjà au maximum
        
        # Calculer la quantité à acheter
        commission_rate = config.transaction_cost_pct / 100
        available_cash = portfolio["cash"] * 0.95  # Garder 5% de liquidité
        
        if available_cash < 50:  # Minimum 50€ par trade
            return None
        
        trade_value = min(available_cash, max_position_value / 2)  # Acheter par tranches
        commission = trade_value * commission_rate
        net_trade_value = trade_value - commission
        quantity = net_trade_value / price
        
        if quantity <= 0:
            return None
        
        # Mettre à jour le portfolio
        portfolio["cash"] -= trade_value
        
        if symbol in portfolio["positions"]:
            # Moyenne pondérée du prix d'achat
            current_pos = portfolio["positions"][symbol]
            total_quantity = current_pos["quantity"] + quantity
            total_cost = (current_pos["avg_price"] * current_pos["quantity"]) + (price * quantity)
            avg_price = total_cost / total_quantity
            
            portfolio["positions"][symbol].update({
                "quantity": total_quantity,
                "avg_price": avg_price,
                "current_price": price,
                "value": total_quantity * price
            })
        else:
            portfolio["positions"][symbol] = {
                "quantity": quantity,
                "avg_price": price,
                "current_price": price,
                "value": quantity * price,
                "unrealized_pnl": 0,
                "realized_pnl": 0
            }
        
        return Trade(
            date=datetime.combine(current_date, datetime.min.time()),
            symbol=symbol,
            action="BUY",
            quantity=quantity,
            price=price,
            value=net_trade_value,
            commission=commission,
            signal_reason=signal["reason"],
            confidence=signal["confidence"]
        )

    def _execute_sell(self, config: Any, portfolio: Dict[str, Any], symbol: str, price: float, signal: Dict[str, Any], current_date: date) -> Optional[Trade]:
        """
        Exécute un ordre de vente
        """
        if symbol not in portfolio["positions"]:
            return None  # Pas de position à vendre
        
        position = portfolio["positions"][symbol]
        quantity_to_sell = position["quantity"] * 0.5  # Vendre 50% de la position
        
        if quantity_to_sell <= 0:
            return None
        
        commission_rate = config.transaction_cost_pct / 100
        gross_proceeds = quantity_to_sell * price
        commission = gross_proceeds * commission_rate
        net_proceeds = gross_proceeds - commission
        
        # Mettre à jour le portfolio
        portfolio["cash"] += net_proceeds
        
        # Calculer le PnL réalisé
        realized_pnl = (price - position["avg_price"]) * quantity_to_sell
        
        # Mettre à jour la position
        new_quantity = position["quantity"] - quantity_to_sell
        if new_quantity <= 0.001:  # Position fermée
            del portfolio["positions"][symbol]
        else:
            portfolio["positions"][symbol].update({
                "quantity": new_quantity,
                "current_price": price,
                "value": new_quantity * price,
                "realized_pnl": position["realized_pnl"] + realized_pnl
            })
        
        return Trade(
            date=datetime.combine(current_date, datetime.min.time()),
            symbol=symbol,
            action="SELL",
            quantity=quantity_to_sell,
            price=price,
            value=net_proceeds,
            commission=commission,
            signal_reason=signal["reason"],
            confidence=signal["confidence"]
        )

    def _calculate_metrics(self, trades: List[Trade], equity_curve: List[Dict[str, Any]], initial_capital: float) -> Dict[str, Any]:
        """
        Calcule les métriques de performance
        """
        if not equity_curve:
            return self._empty_metrics()
        
        final_value = equity_curve[-1]["value"]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Calculer les retours journaliers
        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev_value = equity_curve[i-1]["value"]
            curr_value = equity_curve[i]["value"]
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
        
        if not daily_returns:
            return self._empty_metrics()
        
        # Métriques de base
        volatility = np.std(daily_returns) * np.sqrt(252)  # Annualisée
        mean_return = np.mean(daily_returns) * 252  # Annualisé
        
        # Sharpe ratio (en assumant 0% de taux sans risque)
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Win rate
        winning_trades = [t for t in trades if self._is_winning_trade(t, trades)]
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        # Métriques de risque avancées
        risk_metrics = self._calculate_risk_metrics(daily_returns, equity_curve)
        
        return {
            "total_return_pct": total_return * 100,
            "annualized_return_pct": mean_return * 100,
            "volatility_pct": volatility * 100,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown * 100,
            "win_rate_pct": win_rate,
            "risk_metrics": risk_metrics
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """
        Retourne des métriques vides
        """
        return {
            "total_return_pct": 0,
            "annualized_return_pct": 0,
            "volatility_pct": 0,
            "sharpe_ratio": 0,
            "max_drawdown_pct": 0,
            "win_rate_pct": 0,
            "risk_metrics": {}
        }

    def _calculate_max_drawdown(self, equity_curve: List[Dict[str, Any]]) -> float:
        """
        Calcule le maximum drawdown
        """
        values = [point["value"] for point in equity_curve]
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)
        
        return max_dd

    def _is_winning_trade(self, trade: Trade, all_trades: List[Trade]) -> bool:
        """
        Détermine si un trade est gagnant (simplification)
        """
        if trade.action == "SELL":
            # Trouver le dernier achat correspondant
            for prev_trade in reversed(all_trades):
                if prev_trade.symbol == trade.symbol and prev_trade.action == "BUY" and prev_trade.date < trade.date:
                    return trade.price > prev_trade.price
        return False

    def _calculate_risk_metrics(self, daily_returns: List[float], equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule des métriques de risque avancées
        """
        if not daily_returns:
            return {}
        
        returns_array = np.array(daily_returns)
        
        # Value at Risk (VaR) à 95%
        var_95 = np.percentile(returns_array, 5)
        
        # Conditional Value at Risk (CVaR)
        cvar_95 = np.mean(returns_array[returns_array <= var_95])
        
        # Calmar ratio
        max_dd = self._calculate_max_drawdown(equity_curve)
        mean_annual_return = np.mean(returns_array) * 252
        calmar_ratio = mean_annual_return / max_dd if max_dd > 0 else 0
        
        # Sortino ratio
        downside_returns = returns_array[returns_array < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = mean_annual_return / downside_deviation if downside_deviation > 0 else 0
        
        return {
            "var_95_pct": var_95 * 100,
            "cvar_95_pct": cvar_95 * 100,
            "calmar_ratio": calmar_ratio,
            "sortino_ratio": sortino_ratio,
            "downside_deviation_pct": downside_deviation * 100
        }

    async def _calculate_benchmark_comparison(self, config: Any, equity_curve: List[Dict[str, Any]], market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Compare avec un benchmark (buy and hold)
        """
        if not equity_curve or not config.etf_symbols:
            return {}
        
        try:
            # Utiliser le premier ETF comme benchmark
            benchmark_symbol = config.etf_symbols[0]
            if benchmark_symbol not in market_data:
                return {}
            
            benchmark_data = market_data[benchmark_symbol]
            start_price = benchmark_data['close_price'].iloc[0]
            end_price = benchmark_data['close_price'].iloc[-1]
            
            benchmark_return = (end_price - start_price) / start_price * 100
            strategy_return = (equity_curve[-1]["value"] - config.initial_capital) / config.initial_capital * 100
            
            alpha = strategy_return - benchmark_return
            
            return {
                "benchmark_symbol": benchmark_symbol,
                "benchmark_return_pct": benchmark_return,
                "strategy_return_pct": strategy_return,
                "alpha_pct": alpha,
                "outperformed": alpha > 0
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul benchmark: {e}")
            return {}

    def _trade_to_dict(self, trade: Trade) -> Dict[str, Any]:
        """
        Convertit un trade en dictionnaire
        """
        return {
            "date": trade.date.isoformat(),
            "symbol": trade.symbol,
            "action": trade.action,
            "quantity": trade.quantity,
            "price": trade.price,
            "value": trade.value,
            "commission": trade.commission,
            "signal_reason": trade.signal_reason,
            "confidence": trade.confidence
        }

    async def save_backtest_result(self, result: Dict[str, Any], user_id: str):
        """
        Sauvegarde le résultat en base de données (à implémenter)
        """
        # TODO: Implémenter la sauvegarde en DB
        logger.info(f"Sauvegarde du backtest {result['id']} pour l'utilisateur {user_id}")

    async def get_user_backtests(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Récupère les backtests de l'utilisateur (à implémenter)
        """
        # TODO: Implémenter la récupération depuis la DB
        return []

    async def delete_backtest(self, backtest_id: str, user_id: str):
        """
        Supprime un backtest (à implémenter)
        """
        # TODO: Implémenter la suppression
        logger.info(f"Suppression du backtest {backtest_id} pour l'utilisateur {user_id}")


# Singleton
_advanced_backtesting_service = None

def get_advanced_backtesting_service() -> AdvancedBacktestingService:
    global _advanced_backtesting_service
    if _advanced_backtesting_service is None:
        market_service = get_real_market_data_service()
        _advanced_backtesting_service = AdvancedBacktestingService(market_service)
    return _advanced_backtesting_service