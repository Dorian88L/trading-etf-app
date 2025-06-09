"""
Service de simulation de trading automatique en temps réel
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import time
import logging
from dataclasses import dataclass
import json

from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.services.advanced_backtesting_service import AdvancedBacktestingService, Trade, Position

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    name: str
    initial_capital: float
    duration_days: int
    strategy_type: str
    risk_level: str
    allowed_etf_sectors: List[str]
    rebalance_frequency_hours: int
    auto_stop_loss: bool
    auto_take_profit: bool

class TradingSimulationService:
    def __init__(self, market_service: RealMarketDataService):
        self.market_service = market_service
        self.backtesting_service = AdvancedBacktestingService(market_service)
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
        self.simulation_tasks: Dict[str, asyncio.Task] = {}
        
    async def create_simulation(self, config: Any, user_id: str) -> Dict[str, Any]:
        """
        Crée une nouvelle simulation de trading
        """
        simulation_id = str(uuid.uuid4())
        
        # Sélectionner les ETFs automatiquement selon les secteurs
        etf_symbols = await self._select_etfs_for_simulation(config)
        
        simulation = {
            "id": simulation_id,
            "user_id": user_id,
            "config": config.dict(),
            "etf_symbols": etf_symbols,
            "current_value": config.initial_capital,
            "total_return_pct": 0.0,
            "daily_returns": [],
            "active_positions": {},
            "completed_trades": [],
            "cash": config.initial_capital,
            "portfolio_history": [],
            "risk_metrics": {},
            "next_rebalance": datetime.now() + timedelta(hours=config.rebalance_frequency_hours),
            "status": "running",
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "days_remaining": config.duration_days,
            "target_end_date": datetime.now() + timedelta(days=config.duration_days)
        }
        
        self.active_simulations[simulation_id] = simulation
        
        logger.info(f"Simulation créée: {simulation_id} pour utilisateur {user_id}")
        logger.info(f"ETFs sélectionnés: {etf_symbols}")
        
        return simulation

    async def _select_etfs_for_simulation(self, config: Any) -> List[str]:
        """
        Sélectionne automatiquement les ETFs pour la simulation
        """
        try:
            # Récupérer tous les ETFs disponibles
            all_etfs = await self.market_service.get_all_etfs()
            
            if not all_etfs:
                # ETFs par défaut si aucune donnée disponible
                return ["IE00B4L5Y983", "IE00BK5BQT80", "IE00B5BMR087"]  # IWDA, VWCE, CSPX
            
            # Filtrer par secteurs si spécifiés
            if config.allowed_etf_sectors:
                filtered_etfs = [
                    etf for etf in all_etfs 
                    if etf.get("sector", "").lower() in [s.lower() for s in config.allowed_etf_sectors]
                ]
            else:
                filtered_etfs = all_etfs
            
            # Sélection basée sur le niveau de risque
            if config.risk_level == "conservative":
                # Privilégier les ETFs larges et diversifiés
                preferred_sectors = ["global equity", "developed markets", "government bonds"]
                max_etfs = 3
            elif config.risk_level == "moderate":
                # Mix équilibré
                preferred_sectors = ["global equity", "technology", "european equity", "us equity"]
                max_etfs = 5
            else:  # aggressive
                # ETFs plus spécialisés et volatils
                preferred_sectors = ["technology", "emerging markets", "small cap", "sector specific"]
                max_etfs = 7
            
            # Sélectionner les ETFs
            selected_etfs = []
            
            # D'abord les secteurs préférés
            for sector in preferred_sectors:
                sector_etfs = [
                    etf for etf in filtered_etfs 
                    if sector.lower() in etf.get("sector", "").lower()
                    and etf.get("symbol") not in [e.get("symbol") for e in selected_etfs]
                ]
                if sector_etfs and len(selected_etfs) < max_etfs:
                    # Prendre le plus liquide (volume élevé)
                    best_etf = max(sector_etfs, key=lambda x: x.get("volume", 0))
                    selected_etfs.append(best_etf)
            
            # Compléter avec d'autres ETFs si nécessaire
            if len(selected_etfs) < 3:  # Minimum 3 ETFs
                remaining_etfs = [
                    etf for etf in filtered_etfs 
                    if etf.get("symbol") not in [e.get("symbol") for e in selected_etfs]
                ]
                # Prendre les plus liquides
                remaining_etfs.sort(key=lambda x: x.get("volume", 0), reverse=True)
                selected_etfs.extend(remaining_etfs[:3-len(selected_etfs)])
            
            symbols = [etf.get("symbol") for etf in selected_etfs if etf.get("symbol")]
            
            # Fallback si pas assez d'ETFs
            if len(symbols) < 2:
                symbols = ["IE00B4L5Y983", "IE00BK5BQT80", "IE00B5BMR087"]  # ETFs par défaut
            
            return symbols[:max_etfs]
            
        except Exception as e:
            logger.error(f"Erreur sélection ETFs: {e}")
            # ETFs par défaut
            return ["IE00B4L5Y983", "IE00BK5BQT80", "IE00B5BMR087"]

    async def run_simulation_loop(self, simulation_id: str):
        """
        Lance la boucle principale de simulation
        """
        logger.info(f"Démarrage de la boucle de simulation {simulation_id}")
        
        try:
            while simulation_id in self.active_simulations:
                simulation = self.active_simulations[simulation_id]
                
                if simulation["status"] != "running":
                    break
                
                # Vérifier si la simulation est terminée
                if simulation["days_remaining"] <= 0:
                    await self._complete_simulation(simulation_id)
                    break
                
                # Vérifier s'il est temps de rééquilibrer
                if datetime.now() >= simulation["next_rebalance"]:
                    await self._rebalance_portfolio(simulation_id)
                
                # Mettre à jour les valeurs du portfolio
                await self._update_portfolio_values(simulation_id)
                
                # Calculer les métriques de risque
                await self._update_risk_metrics(simulation_id)
                
                # Attendre avant la prochaine itération (1 minute)
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info(f"Simulation {simulation_id} annulée")
        except Exception as e:
            logger.error(f"Erreur dans la simulation {simulation_id}: {e}")
            if simulation_id in self.active_simulations:
                self.active_simulations[simulation_id]["status"] = "error"

    async def _rebalance_portfolio(self, simulation_id: str):
        """
        Rééquilibre le portfolio selon la stratégie
        """
        simulation = self.active_simulations[simulation_id]
        
        logger.info(f"Rééquilibrage du portfolio {simulation_id}")
        
        try:
            # Récupérer les données de marché actuelles
            market_data = await self._get_current_market_data(simulation["etf_symbols"])
            
            # Générer des signaux de trading
            signals = await self._generate_simulation_signals(simulation, market_data)
            
            # Exécuter les trades
            new_trades = await self._execute_simulation_trades(simulation_id, signals, market_data)
            
            # Mettre à jour la simulation
            simulation["completed_trades"].extend(new_trades)
            simulation["last_updated"] = datetime.now()
            simulation["next_rebalance"] = datetime.now() + timedelta(
                hours=simulation["config"]["rebalance_frequency_hours"]
            )
            simulation["days_remaining"] = max(0, (simulation["target_end_date"] - datetime.now()).days)
            
            logger.info(f"Rééquilibrage terminé: {len(new_trades)} trades exécutés")
            
        except Exception as e:
            logger.error(f"Erreur lors du rééquilibrage {simulation_id}: {e}")

    async def _get_current_market_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les données de marché actuelles
        """
        market_data = {}
        
        for symbol in symbols:
            try:
                # Récupérer les données récentes (dernière semaine)
                data = await self.market_service.get_historical_data(
                    symbol=symbol,
                    period="1w"
                )
                
                if data and len(data) > 0:
                    latest = data[-1]
                    market_data[symbol] = {
                        "current_price": latest.get("close_price", 0),
                        "volume": latest.get("volume", 0),
                        "timestamp": latest.get("timestamp"),
                        "historical_data": data[-20:] if len(data) >= 20 else data  # 20 derniers points
                    }
                    
            except Exception as e:
                logger.error(f"Erreur récupération données pour {symbol}: {e}")
                continue
        
        return market_data

    async def _generate_simulation_signals(self, simulation: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère des signaux pour la simulation
        """
        signals = []
        config = simulation["config"]
        
        for symbol in simulation["etf_symbols"]:
            if symbol not in market_data:
                continue
            
            try:
                historical_data = market_data[symbol]["historical_data"]
                if len(historical_data) < 10:
                    continue
                
                # Convertir en DataFrame
                df = pd.DataFrame(historical_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Utiliser la stratégie du backtesting
                signal = await self.backtesting_service._calculate_signal(
                    config["strategy_type"],
                    self._get_strategy_params(config),
                    df,
                    symbol
                )
                
                if signal:
                    # Ajuster la confiance selon le niveau de risque
                    confidence_adjustment = {
                        "conservative": -10,
                        "moderate": 0,
                        "aggressive": +5
                    }.get(config["risk_level"], 0)
                    
                    signal["confidence"] = max(0, min(100, signal["confidence"] + confidence_adjustment))
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Erreur génération signal pour {symbol}: {e}")
                continue
        
        return signals

    def _get_strategy_params(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les paramètres de stratégie adaptés au niveau de risque
        """
        risk_level = config.get("risk_level", "moderate")
        
        if risk_level == "conservative":
            return {
                "rsi": {"period": 21, "oversold": 25, "overbought": 75},
                "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "bollinger": {"period": 20, "deviation": 2.5}
            }
        elif risk_level == "aggressive":
            return {
                "rsi": {"period": 10, "oversold": 35, "overbought": 65},
                "macd": {"fast_period": 8, "slow_period": 21, "signal_period": 6},
                "bollinger": {"period": 15, "deviation": 1.5}
            }
        else:  # moderate
            return {
                "rsi": {"period": 14, "oversold": 30, "overbought": 70},
                "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "bollinger": {"period": 20, "deviation": 2.0}
            }

    async def _execute_simulation_trades(self, simulation_id: str, signals: List[Dict[str, Any]], market_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Exécute les trades pour la simulation
        """
        simulation = self.active_simulations[simulation_id]
        trades = []
        
        for signal in signals:
            symbol = signal["symbol"]
            action = signal["action"]
            confidence = signal["confidence"]
            
            # Filtrer par confiance minimum
            min_confidence = {"conservative": 75, "moderate": 65, "aggressive": 55}[simulation["config"]["risk_level"]]
            if confidence < min_confidence:
                continue
            
            try:
                if action == "BUY":
                    trade = await self._execute_simulation_buy(simulation_id, signal, market_data)
                elif action == "SELL":
                    trade = await self._execute_simulation_sell(simulation_id, signal, market_data)
                else:
                    continue
                
                if trade:
                    trades.append(trade)
                    
            except Exception as e:
                logger.error(f"Erreur exécution trade {action} {symbol}: {e}")
                continue
        
        return trades

    async def _execute_simulation_buy(self, simulation_id: str, signal: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Exécute un achat dans la simulation
        """
        simulation = self.active_simulations[simulation_id]
        symbol = signal["symbol"]
        price = signal["price"]
        
        # Vérifier la liquidité disponible
        if simulation["cash"] < 50:  # Minimum 50€
            return None
        
        # Calculer la taille de position
        max_position_pct = {"conservative": 15, "moderate": 20, "aggressive": 25}[simulation["config"]["risk_level"]]
        max_position_value = simulation["current_value"] * (max_position_pct / 100)
        
        # Vérifier la position existante
        current_position_value = 0
        if symbol in simulation["active_positions"]:
            current_position_value = simulation["active_positions"][symbol]["value"]
        
        if current_position_value >= max_position_value:
            return None  # Position déjà au max
        
        # Calculer le montant d'achat
        available_for_trade = min(
            simulation["cash"] * 0.8,  # Garder 20% de liquidité
            max_position_value - current_position_value
        )
        
        if available_for_trade < 25:  # Minimum viable
            return None
        
        # Ajuster selon la confiance
        confidence_factor = signal["confidence"] / 100
        trade_amount = available_for_trade * confidence_factor * 0.5  # Acheter graduellement
        
        commission = trade_amount * 0.001  # 0.1% de commission
        net_amount = trade_amount - commission
        quantity = net_amount / price
        
        # Mettre à jour la simulation
        simulation["cash"] -= trade_amount
        
        if symbol in simulation["active_positions"]:
            pos = simulation["active_positions"][symbol]
            total_quantity = pos["quantity"] + quantity
            total_cost = (pos["avg_price"] * pos["quantity"]) + (price * quantity)
            avg_price = total_cost / total_quantity
            
            simulation["active_positions"][symbol].update({
                "quantity": total_quantity,
                "avg_price": avg_price,
                "current_price": price,
                "value": total_quantity * price
            })
        else:
            simulation["active_positions"][symbol] = {
                "quantity": quantity,
                "avg_price": price,
                "current_price": price,
                "value": quantity * price,
                "unrealized_pnl": 0
            }
        
        trade = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": "BUY",
            "quantity": quantity,
            "price": price,
            "value": net_amount,
            "commission": commission,
            "reason": signal["reason"],
            "confidence": signal["confidence"]
        }
        
        logger.info(f"Simulation {simulation_id}: Achat {quantity:.4f} {symbol} à {price:.2f}€")
        return trade

    async def _execute_simulation_sell(self, simulation_id: str, signal: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Exécute une vente dans la simulation
        """
        simulation = self.active_simulations[simulation_id]
        symbol = signal["symbol"]
        price = signal["price"]
        
        if symbol not in simulation["active_positions"]:
            return None
        
        position = simulation["active_positions"][symbol]
        
        # Vendre selon la confiance du signal
        confidence_factor = signal["confidence"] / 100
        sell_percentage = confidence_factor * 0.6  # Vendre max 60% à la fois
        quantity_to_sell = position["quantity"] * sell_percentage
        
        if quantity_to_sell < 0.001:
            return None
        
        gross_proceeds = quantity_to_sell * price
        commission = gross_proceeds * 0.001  # 0.1%
        net_proceeds = gross_proceeds - commission
        
        # Mettre à jour la simulation
        simulation["cash"] += net_proceeds
        
        new_quantity = position["quantity"] - quantity_to_sell
        if new_quantity < 0.001:  # Position fermée
            del simulation["active_positions"][symbol]
        else:
            simulation["active_positions"][symbol].update({
                "quantity": new_quantity,
                "current_price": price,
                "value": new_quantity * price
            })
        
        trade = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": "SELL",
            "quantity": quantity_to_sell,
            "price": price,
            "value": net_proceeds,
            "commission": commission,
            "reason": signal["reason"],
            "confidence": signal["confidence"],
            "pnl": (price - position["avg_price"]) * quantity_to_sell
        }
        
        logger.info(f"Simulation {simulation_id}: Vente {quantity_to_sell:.4f} {symbol} à {price:.2f}€")
        return trade

    async def _update_portfolio_values(self, simulation_id: str):
        """
        Met à jour les valeurs du portfolio
        """
        simulation = self.active_simulations[simulation_id]
        
        try:
            total_positions_value = 0
            
            # Mettre à jour les prix des positions
            for symbol, position in simulation["active_positions"].items():
                try:
                    # Récupérer le prix actuel (simplifié)
                    current_data = await self.market_service.get_current_price(symbol)
                    if current_data:
                        current_price = current_data.get("current_price", position["current_price"])
                        position["current_price"] = current_price
                        position["value"] = position["quantity"] * current_price
                        position["unrealized_pnl"] = (current_price - position["avg_price"]) * position["quantity"]
                        total_positions_value += position["value"]
                except Exception as e:
                    logger.error(f"Erreur mise à jour prix {symbol}: {e}")
                    total_positions_value += position["value"]  # Garder l'ancienne valeur
            
            # Mettre à jour la valeur totale
            old_value = simulation["current_value"]
            simulation["current_value"] = simulation["cash"] + total_positions_value
            simulation["total_return_pct"] = (
                (simulation["current_value"] - simulation["config"]["initial_capital"]) / 
                simulation["config"]["initial_capital"] * 100
            )
            
            # Ajouter le point à l'historique
            daily_return = ((simulation["current_value"] - old_value) / old_value * 100) if old_value > 0 else 0
            
            simulation["daily_returns"].append({
                "timestamp": datetime.now().isoformat(),
                "value": simulation["current_value"],
                "daily_return_pct": daily_return,
                "cash": simulation["cash"],
                "positions_value": total_positions_value
            })
            
            # Garder seulement les 1000 derniers points
            if len(simulation["daily_returns"]) > 1000:
                simulation["daily_returns"] = simulation["daily_returns"][-1000:]
            
            simulation["last_updated"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour valeurs {simulation_id}: {e}")

    async def _update_risk_metrics(self, simulation_id: str):
        """
        Met à jour les métriques de risque
        """
        simulation = self.active_simulations[simulation_id]
        
        if len(simulation["daily_returns"]) < 2:
            return
        
        try:
            returns = [point["daily_return_pct"] for point in simulation["daily_returns"][-30:]]  # 30 derniers jours
            
            if len(returns) > 1:
                volatility = np.std(returns)
                mean_return = np.mean(returns)
                sharpe = mean_return / volatility if volatility > 0 else 0
                
                # VaR simplifié
                var_95 = np.percentile(returns, 5) if len(returns) >= 5 else 0
                
                simulation["risk_metrics"] = {
                    "volatility_30d": volatility,
                    "mean_return_30d": mean_return,
                    "sharpe_30d": sharpe,
                    "var_95": var_95,
                    "updated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur calcul métriques risque {simulation_id}: {e}")

    async def _complete_simulation(self, simulation_id: str):
        """
        Termine une simulation
        """
        simulation = self.active_simulations[simulation_id]
        simulation["status"] = "completed"
        simulation["last_updated"] = datetime.now()
        
        logger.info(f"Simulation {simulation_id} terminée")
        logger.info(f"Valeur finale: {simulation['current_value']:.2f}€")
        logger.info(f"Rendement total: {simulation['total_return_pct']:.2f}%")

    async def get_simulation(self, simulation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une simulation spécifique
        """
        if simulation_id in self.active_simulations:
            simulation = self.active_simulations[simulation_id]
            if simulation["user_id"] == user_id:
                return simulation
        return None

    async def get_user_simulations(self, user_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère toutes les simulations d'un utilisateur
        """
        user_simulations = [
            sim for sim in self.active_simulations.values()
            if sim["user_id"] == user_id
        ]
        
        if status_filter:
            user_simulations = [
                sim for sim in user_simulations
                if sim["status"] == status_filter
            ]
        
        return user_simulations

    async def pause_simulation(self, simulation_id: str, user_id: str):
        """
        Met en pause une simulation
        """
        if simulation_id in self.active_simulations:
            simulation = self.active_simulations[simulation_id]
            if simulation["user_id"] == user_id:
                simulation["status"] = "paused"
                simulation["last_updated"] = datetime.now()

    async def resume_simulation(self, simulation_id: str, user_id: str):
        """
        Reprend une simulation
        """
        if simulation_id in self.active_simulations:
            simulation = self.active_simulations[simulation_id]
            if simulation["user_id"] == user_id and simulation["status"] == "paused":
                simulation["status"] = "running"
                simulation["last_updated"] = datetime.now()

    async def stop_simulation(self, simulation_id: str, user_id: str):
        """
        Arrête et supprime une simulation
        """
        if simulation_id in self.active_simulations:
            simulation = self.active_simulations[simulation_id]
            if simulation["user_id"] == user_id:
                simulation["status"] = "stopped"
                del self.active_simulations[simulation_id]
                
                if simulation_id in self.simulation_tasks:
                    self.simulation_tasks[simulation_id].cancel()
                    del self.simulation_tasks[simulation_id]

    async def get_leaderboard(self, timeframe: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère le classement des simulations
        """
        # Filtrer par timeframe
        cutoff_date = datetime.now()
        if timeframe == "week":
            cutoff_date -= timedelta(weeks=1)
        elif timeframe == "month":
            cutoff_date -= timedelta(days=30)
        # Pour "all_time", pas de filtre
        
        eligible_sims = []
        for sim in self.active_simulations.values():
            if timeframe == "all_time" or sim["created_at"] >= cutoff_date:
                eligible_sims.append({
                    "user_id": sim["user_id"][:8] + "...",  # Anonymisé
                    "name": sim["config"]["name"],
                    "return_pct": sim["total_return_pct"],
                    "duration_days": (datetime.now() - sim["created_at"]).days,
                    "status": sim["status"],
                    "risk_level": sim["config"]["risk_level"]
                })
        
        # Trier par rendement
        eligible_sims.sort(key=lambda x: x["return_pct"], reverse=True)
        
        return eligible_sims[:limit]


# Singleton
_trading_simulation_service = None

def get_trading_simulation_service() -> TradingSimulationService:
    global _trading_simulation_service
    if _trading_simulation_service is None:
        market_service = get_real_market_data_service()
        _trading_simulation_service = TradingSimulationService(market_service)
    return _trading_simulation_service