"""
Moteur de backtesting avancé pour tester les stratégies de trading
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from app.services.signal_generator import TradingSignalGenerator
from app.services.real_market_data import RealMarketDataService
from app.models.signal import SignalType

logger = logging.getLogger(__name__)

class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class BacktestTrade:
    """Représente une transaction dans le backtest"""
    date: datetime
    symbol: str
    order_type: OrderType
    quantity: float
    price: float
    fees: float = 0.0
    signal_confidence: float = 0.0

@dataclass
class BacktestMetrics:
    """Métriques de performance du backtest"""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float

class BacktestingEngine:
    """Moteur de backtesting pour stratégies ETF"""
    
    def __init__(self):
        self.signal_generator = TradingSignalGenerator()
        self.market_service = RealMarketDataService()
        
    async def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        transaction_fee: float = 0.001,  # 0.1%
        strategy: str = "momentum"
    ) -> Dict:
        """
        Exécute un backtest complet
        
        Args:
            symbols: Liste des symboles ETF à tester
            start_date: Date de début du backtest
            end_date: Date de fin du backtest
            initial_capital: Capital initial
            transaction_fee: Frais de transaction (pourcentage)
            strategy: Stratégie à tester ('momentum', 'mean_reversion', 'breakout')
        """
        logger.info(f"Démarrage backtest: {symbols} du {start_date} au {end_date}")
        
        try:
            # 1. Récupérer les données historiques
            historical_data = await self._get_historical_data(symbols, start_date, end_date)
            
            # 2. Générer les signaux
            signals = await self._generate_signals(historical_data, strategy)
            
            # 3. Simuler les trades
            trades, portfolio_value = await self._simulate_trades(
                signals, historical_data, initial_capital, transaction_fee
            )
            
            # 4. Calculer les métriques
            metrics = self._calculate_metrics(portfolio_value, trades, initial_capital)
            
            # 5. Préparer les résultats
            results = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "symbols": symbols,
                "strategy": strategy,
                "initial_capital": initial_capital,
                "final_capital": portfolio_value[-1] if portfolio_value else initial_capital,
                "metrics": {
                    "total_return": metrics.total_return,
                    "annualized_return": metrics.annualized_return,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "max_drawdown": metrics.max_drawdown,
                    "win_rate": metrics.win_rate,
                    "total_trades": metrics.total_trades,
                    "profitable_trades": metrics.profitable_trades,
                    "avg_trade_return": metrics.avg_trade_return,
                    "volatility": metrics.volatility,
                    "calmar_ratio": metrics.calmar_ratio
                },
                "trades": [
                    {
                        "date": trade.date.isoformat(),
                        "symbol": trade.symbol,
                        "type": trade.order_type.value,
                        "quantity": trade.quantity,
                        "price": trade.price,
                        "fees": trade.fees,
                        "confidence": trade.signal_confidence
                    }
                    for trade in trades
                ],
                "portfolio_evolution": [
                    {"date": (start_date + timedelta(days=i)).isoformat(), "value": value}
                    for i, value in enumerate(portfolio_value)
                ]
            }
            
            logger.info(f"Backtest terminé. Rendement total: {metrics.total_return:.2%}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest: {e}")
            raise
    
    async def _get_historical_data(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Récupère les données historiques pour les symboles"""
        historical_data = {}
        
        for symbol in symbols:
            try:
                # Récupérer via Yahoo Finance
                data = await self.market_service.get_historical_data(
                    symbol, start_date, end_date
                )
                
                if data is not None and not data.empty:
                    historical_data[symbol] = data
                else:
                    logger.warning(f"Pas de données pour {symbol}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de {symbol}: {e}")
                
        return historical_data
    
    async def _generate_signals(
        self, 
        historical_data: Dict[str, pd.DataFrame], 
        strategy: str
    ) -> Dict[str, List[Dict]]:
        """Génère les signaux de trading pour chaque symbole"""
        signals = {}
        
        for symbol, data in historical_data.items():
            try:
                symbol_signals = []
                
                # Générer des signaux pour chaque jour
                for i in range(20, len(data)):  # Besoin de 20 jours pour les indicateurs
                    price_slice = data.iloc[:i+1]
                    
                    # Générer signal basé sur la stratégie
                    if strategy == "momentum":
                        signal = self._momentum_signal(price_slice)
                    elif strategy == "mean_reversion":
                        signal = self._mean_reversion_signal(price_slice)
                    elif strategy == "breakout":
                        signal = self._breakout_signal(price_slice)
                    else:
                        signal = self._momentum_signal(price_slice)  # Par défaut
                    
                    if signal:
                        signal["date"] = data.index[i]
                        signal["symbol"] = symbol
                        symbol_signals.append(signal)
                
                signals[symbol] = symbol_signals
                
            except Exception as e:
                logger.error(f"Erreur génération signaux pour {symbol}: {e}")
                signals[symbol] = []
        
        return signals
    
    def _momentum_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Signal basé sur le momentum"""
        if len(data) < 20:
            return None
            
        # Calculer moyennes mobiles
        sma_short = data['close'].rolling(5).mean().iloc[-1]
        sma_long = data['close'].rolling(20).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Signal d'achat si MA courte > MA longue et prix au-dessus
        if sma_short > sma_long and current_price > sma_short:
            return {
                "type": SignalType.BUY,
                "confidence": min(0.8, (sma_short - sma_long) / sma_long * 10),
                "price": current_price
            }
        
        # Signal de vente si MA courte < MA longue
        elif sma_short < sma_long and current_price < sma_short:
            return {
                "type": SignalType.SELL,
                "confidence": min(0.8, (sma_long - sma_short) / sma_long * 10),
                "price": current_price
            }
            
        return None
    
    def _mean_reversion_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Signal basé sur le retour à la moyenne"""
        if len(data) < 20:
            return None
            
        # Bollinger Bands
        sma = data['close'].rolling(20).mean().iloc[-1]
        std = data['close'].rolling(20).std().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        # Signal d'achat si prix proche de la bande inférieure
        if current_price <= lower_band:
            return {
                "type": SignalType.BUY,
                "confidence": min(0.9, (lower_band - current_price) / lower_band),
                "price": current_price
            }
        
        # Signal de vente si prix proche de la bande supérieure
        elif current_price >= upper_band:
            return {
                "type": SignalType.SELL,
                "confidence": min(0.9, (current_price - upper_band) / upper_band),
                "price": current_price
            }
            
        return None
    
    def _breakout_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Signal basé sur les cassures"""
        if len(data) < 20:
            return None
            
        # Résistance et support sur 20 jours
        high_20 = data['high'].rolling(20).max().iloc[-2]  # Excluant aujourd'hui
        low_20 = data['low'].rolling(20).min().iloc[-2]
        current_price = data['close'].iloc[-1]
        volume_avg = data['volume'].rolling(20).mean().iloc[-1]
        current_volume = data['volume'].iloc[-1]
        
        # Cassure avec volume
        if current_price > high_20 and current_volume > volume_avg * 1.5:
            return {
                "type": SignalType.BUY,
                "confidence": min(0.9, (current_price - high_20) / high_20 * 5),
                "price": current_price
            }
        
        elif current_price < low_20 and current_volume > volume_avg * 1.5:
            return {
                "type": SignalType.SELL,
                "confidence": min(0.9, (low_20 - current_price) / low_20 * 5),
                "price": current_price
            }
            
        return None
    
    async def _simulate_trades(
        self,
        signals: Dict[str, List[Dict]],
        historical_data: Dict[str, pd.DataFrame],
        initial_capital: float,
        transaction_fee: float
    ) -> Tuple[List[BacktestTrade], List[float]]:
        """Simule l'exécution des trades"""
        trades = []
        cash = initial_capital
        positions = {}  # {symbol: quantity}
        portfolio_values = [initial_capital]
        
        # Créer un calendrier unifié de tous les signaux
        all_signals = []
        for symbol, symbol_signals in signals.items():
            for signal in symbol_signals:
                all_signals.append((signal["date"], symbol, signal))
        
        # Trier par date
        all_signals.sort(key=lambda x: x[0])
        
        for signal_date, symbol, signal in all_signals:
            try:
                signal_type = signal["type"]
                price = signal["price"]
                confidence = signal["confidence"]
                
                # Calcul de la taille de position basée sur la confiance
                position_size = min(0.2, confidence) * 0.5  # Max 10% du portfolio
                
                if signal_type == SignalType.BUY and cash > 0:
                    # Acheter
                    trade_value = cash * position_size
                    fees = trade_value * transaction_fee
                    quantity = (trade_value - fees) / price
                    
                    if quantity > 0:
                        cash -= trade_value
                        positions[symbol] = positions.get(symbol, 0) + quantity
                        
                        trade = BacktestTrade(
                            date=signal_date,
                            symbol=symbol,
                            order_type=OrderType.BUY,
                            quantity=quantity,
                            price=price,
                            fees=fees,
                            signal_confidence=confidence
                        )
                        trades.append(trade)
                
                elif signal_type == SignalType.SELL and symbol in positions and positions[symbol] > 0:
                    # Vendre
                    quantity_to_sell = positions[symbol] * position_size
                    trade_value = quantity_to_sell * price
                    fees = trade_value * transaction_fee
                    
                    cash += trade_value - fees
                    positions[symbol] -= quantity_to_sell
                    
                    trade = BacktestTrade(
                        date=signal_date,
                        symbol=symbol,
                        order_type=OrderType.SELL,
                        quantity=quantity_to_sell,
                        price=price,
                        fees=fees,
                        signal_confidence=confidence
                    )
                    trades.append(trade)
                
                # Calculer la valeur du portfolio
                portfolio_value = cash
                for pos_symbol, quantity in positions.items():
                    if pos_symbol in historical_data:
                        # Obtenir le prix du jour
                        data = historical_data[pos_symbol]
                        price_data = data[data.index <= signal_date]
                        if not price_data.empty:
                            current_price = price_data['close'].iloc[-1]
                            portfolio_value += quantity * current_price
                
                portfolio_values.append(portfolio_value)
                
            except Exception as e:
                logger.error(f"Erreur simulation trade {symbol}: {e}")
        
        return trades, portfolio_values
    
    def _calculate_metrics(
        self,
        portfolio_values: List[float],
        trades: List[BacktestTrade],
        initial_capital: float
    ) -> BacktestMetrics:
        """Calcule les métriques de performance"""
        if not portfolio_values or len(portfolio_values) < 2:
            return BacktestMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        final_value = portfolio_values[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Retour annualisé
        days = len(portfolio_values)
        annualized_return = (final_value / initial_capital) ** (365 / days) - 1
        
        # Volatilité
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualisée
        
        # Sharpe ratio (assume risk-free rate = 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Max drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Statistiques des trades
        total_trades = len(trades)
        if total_trades > 0:
            # Calculer les trades appariés (achat/vente)
            trade_returns = []
            buy_trades = {}
            
            for trade in trades:
                if trade.order_type == OrderType.BUY:
                    if trade.symbol not in buy_trades:
                        buy_trades[trade.symbol] = []
                    buy_trades[trade.symbol].append(trade)
                
                elif trade.order_type == OrderType.SELL and trade.symbol in buy_trades:
                    if buy_trades[trade.symbol]:
                        buy_trade = buy_trades[trade.symbol].pop(0)
                        trade_return = (trade.price - buy_trade.price) / buy_trade.price
                        trade_returns.append(trade_return)
            
            profitable_trades = sum(1 for r in trade_returns if r > 0)
            win_rate = profitable_trades / len(trade_returns) if trade_returns else 0
            avg_trade_return = np.mean(trade_returns) if trade_returns else 0
        else:
            profitable_trades = 0
            win_rate = 0
            avg_trade_return = 0
        
        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            avg_trade_return=avg_trade_return,
            volatility=volatility,
            calmar_ratio=calmar_ratio
        )