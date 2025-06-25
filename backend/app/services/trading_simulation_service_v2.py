"""
Service de simulation de trading automatique - Version stateless et persistante
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.services.multi_source_etf_data import MultiSourceETFDataService
from app.services.technical_indicators import TechnicalAnalysisService
from app.services.technical_analysis import SignalGenerator
from app.core.database import get_db
from app.models.trading_simulation import (
    TradingSimulation, SimulationTrade, SimulationPerformanceSnapshot, 
    SimulationStatus, SimulationStrategy
)
from app.schemas.trading_simulation import TradingSimulationCreate
# Import removed to avoid circular import - will import dynamically if needed

logger = logging.getLogger(__name__)


class TradingSimulationService:
    """
    Service stateless pour les simulations de trading automatique.
    Toutes les données sont persistées en base de données.
    """
    
    def __init__(self):
        self.etf_data_service = MultiSourceETFDataService()
        self.technical_service = TechnicalAnalysisService()
        self.signal_service = SignalGenerator()
        
        # ETFs européens disponibles avec données réelles validées
        self.available_etfs = [
            # LSE - London Stock Exchange (GBP/USD)
            "IWDA.L",   # iShares Core MSCI World UCITS ETF
            "CSPX.L",   # iShares Core S&P 500 UCITS ETF USD (Acc)
            "VUSA.L",   # Vanguard S&P 500 UCITS ETF 
            "IEMA.L",   # iShares Core MSCI Emerging Markets IMI
            "IEUR.L",   # iShares Core MSCI Europe UCITS ETF
            "INRG.L",   # iShares Global Clean Energy UCITS ETF
            
            # XETRA - Deutsche Börse (EUR)
            "EUNL.DE",  # iShares Core MSCI World UCITS ETF
            "XMME.DE",  # Xtrackers MSCI Emerging Markets UCITS ETF
            "EXS1.DE",  # iShares Core EURO STOXX 50 UCITS ETF
            
            # Euronext Amsterdam (EUR)
            "IWDA.AS",  # iShares Core MSCI World UCITS ETF
            "VWRL.AS",  # Vanguard FTSE All-World UCITS ETF
        ]

    async def create_simulation(
        self, 
        db: Session, 
        user_id: int, 
        config: TradingSimulationCreate
    ) -> TradingSimulation:
        """
        Crée une nouvelle simulation de trading et la sauvegarde en BDD.
        """
        try:
            # Sélectionner les ETFs selon la configuration
            if hasattr(config, 'etf_symbols') and config.etf_symbols:
                # Valider que les ETFs sélectionnés sont disponibles
                selected_etfs = []
                for symbol in config.etf_symbols:
                    if symbol in self.available_etfs:
                        selected_etfs.append(symbol)
                    else:
                        logger.warning(f"ETF {symbol} non disponible, ignoré")
                
                if not selected_etfs:
                    logger.warning("Aucun ETF valide sélectionné, utilisation de la sélection par défaut")
                    selected_etfs = self.available_etfs[:5]
            else:
                # Sélection par défaut : mix d'ETFs populaires avec données fiables
                selected_etfs = ["IWDA.L", "CSPX.L", "VUSA.L", "IEMA.L", "IEUR.L"]
            
            # Créer l'objet simulation avec les nouveaux champs
            simulation = TradingSimulation(
                user_id=user_id,
                name=config.name,
                initial_capital=config.initial_capital,
                duration_days=config.duration_days,
                strategy_type=config.strategy_type,
                risk_level=config.risk_level,
                rebalance_frequency_hours=config.rebalance_frequency_hours,
                auto_stop_loss=config.auto_stop_loss,
                auto_take_profit=config.auto_take_profit,
                etf_symbols=selected_etfs,
                status=SimulationStatus.PENDING,
                cash=config.initial_capital,
                current_value=config.initial_capital,
                active_positions={},
                daily_returns=[],
                completed_trades=[],
                created_at=datetime.utcnow()
            )
            
            # Sauvegarder en base
            db.add(simulation)
            db.commit()
            db.refresh(simulation)
            
            logger.info(f"Simulation créée: ID={simulation.id}, User={user_id}, ETFs={len(selected_etfs)}")
            return simulation
            
        except Exception as e:
            logger.error(f"Erreur création simulation: {str(e)}")
            db.rollback()
            raise

    async def start_simulation(self, simulation_id: str, db: Session) -> None:
        """
        Démarre une simulation en lançant la tâche Celery.
        """
        try:
            simulation = db.query(TradingSimulation).filter(
                TradingSimulation.id == simulation_id
            ).first()
            
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} non trouvée")
            
            if simulation.status != SimulationStatus.PENDING:
                raise ValueError(f"Simulation {simulation_id} ne peut pas être démarrée depuis l'état {simulation.status}")
            
            # Lancer la tâche Celery
            task = start_trading_simulation_task.delay(simulation_id)
            
            # Mettre à jour le statut
            simulation.status = SimulationStatus.RUNNING
            simulation.started_at = datetime.utcnow()
            simulation.celery_task_id = task.id
            
            db.commit()
            
            logger.info(f"Simulation {simulation_id} démarrée avec tâche Celery {task.id}")
            
        except Exception as e:
            logger.error(f"Erreur démarrage simulation {simulation_id}: {str(e)}")
            db.rollback()
            raise

    async def pause_simulation(self, simulation_id: str, db: Session) -> None:
        """
        Met en pause une simulation.
        """
        try:
            simulation = db.query(TradingSimulation).filter(
                TradingSimulation.id == simulation_id
            ).first()
            
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} non trouvée")
            
            if simulation.status != SimulationStatus.RUNNING:
                raise ValueError(f"Simulation {simulation_id} n'est pas en cours d'exécution")
            
            # Mettre à jour le statut
            simulation.status = SimulationStatus.PAUSED
            simulation.paused_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Simulation {simulation_id} mise en pause")
            
        except Exception as e:
            logger.error(f"Erreur pause simulation {simulation_id}: {str(e)}")
            db.rollback()
            raise

    async def stop_simulation(self, simulation_id: str, db: Session) -> None:
        """
        Arrête définitivement une simulation.
        """
        try:
            simulation = db.query(TradingSimulation).filter(
                TradingSimulation.id == simulation_id
            ).first()
            
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} non trouvée")
            
            # Calculer les statistiques finales
            await self._calculate_final_stats(simulation, db)
            
            # Mettre à jour le statut
            simulation.status = SimulationStatus.COMPLETED
            simulation.ended_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Simulation {simulation_id} arrêtée")
            
        except Exception as e:
            logger.error(f"Erreur arrêt simulation {simulation_id}: {str(e)}")
            db.rollback()
            raise

    async def execute_rebalance(self, simulation_id: str, db: Session) -> List[SimulationTrade]:
        """
        Exécute un rééquilibrage du portefeuille d'une simulation.
        Cette méthode est appelée par les tâches Celery.
        """
        try:
            simulation = db.query(TradingSimulation).filter(
                TradingSimulation.id == simulation_id
            ).first()
            
            if not simulation or simulation.status != SimulationStatus.RUNNING:
                logger.warning(f"Simulation {simulation_id} non éligible pour rééquilibrage")
                return []
            
            # Récupérer les données de marché actuelles
            market_data = await self._get_current_market_data(simulation.etf_list)
            
            if not market_data:
                logger.warning(f"Aucune donnée de marché disponible pour simulation {simulation_id}")
                return []
            
            # Générer les signaux de trading
            signals = await self._generate_trading_signals(simulation, market_data, db)
            
            # Exécuter les trades
            executed_trades = await self._execute_trades(simulation, signals, market_data, db)
            
            # Mettre à jour la simulation
            await self._update_simulation_after_rebalance(simulation, executed_trades, market_data, db)
            
            # Créer un snapshot de performance
            await self._create_performance_snapshot(simulation, db)
            
            logger.info(f"Rééquilibrage simulation {simulation_id}: {len(executed_trades)} trades exécutés")
            return executed_trades
            
        except Exception as e:
            logger.error(f"Erreur rééquilibrage simulation {simulation_id}: {str(e)}")
            raise

    async def get_available_etfs_with_data(self) -> List[Dict[str, str]]:
        """
        Retourne la liste des ETFs disponibles avec leurs informations et validation des données.
        """
        available_etfs = []
        
        for symbol in self.available_etfs:
            try:
                # Tester si on peut récupérer des données pour cet ETF
                etf_data = await self.etf_data_service.get_etf_data(symbol)
                
                if etf_data and etf_data.current_price > 0:
                    etf_info = self.etf_data_service.european_etfs.get(symbol, {})
                    available_etfs.append({
                        "symbol": symbol,
                        "isin": etf_info.get("isin", ""),
                        "name": etf_info.get("name", symbol),
                        "sector": etf_info.get("sector", "Unknown"),
                        "exchange": etf_info.get("exchange", ""),
                        "current_price": etf_data.current_price,
                        "currency": etf_data.currency
                    })
                    
            except Exception as e:
                logger.warning(f"ETF {symbol} indisponible: {str(e)}")
                continue
        
        logger.info(f"ETFs disponibles avec données: {len(available_etfs)}")
        return available_etfs

    async def _get_current_market_data(self, etf_symbols: List[str]) -> Dict[str, Any]:
        """
        Récupère les données de marché actuelles pour les ETFs.
        """
        market_data = {}
        
        for symbol in etf_symbols:
            try:
                # Récupérer les données via le service multi-source
                etf_data = await self.etf_data_service.get_etf_data(symbol)
                
                if etf_data:
                    market_data[symbol] = {
                        'current_price': etf_data.current_price,
                        'volume': etf_data.volume,
                        'change_percent': etf_data.change_percent,
                        'timestamp': datetime.utcnow(),
                        'isin': etf_data.isin,
                        'name': etf_data.name
                    }
                    
            except Exception as e:
                logger.error(f"Erreur récupération données {symbol}: {str(e)}")
                continue
        
        return market_data

    async def _generate_trading_signals(
        self, 
        simulation: TradingSimulation, 
        market_data: Dict[str, Any], 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Génère les signaux de trading selon la stratégie de la simulation.
        """
        signals = []
        
        for symbol in simulation.etf_list:
            if symbol not in market_data:
                continue
                
            try:
                # Générer un signal via le service de signaux
                signal_data = await self.signal_service.generate_signal_for_etf(
                    etf_symbol=symbol,
                    strategy_type=simulation.strategy.value
                )
                
                if signal_data:
                    signals.append({
                        'symbol': symbol,
                        'signal': signal_data.signal_type,
                        'confidence': signal_data.confidence_score,
                        'reason': signal_data.reasoning,
                        'current_price': market_data[symbol]['current_price']
                    })
                    
            except Exception as e:
                logger.error(f"Erreur génération signal pour {symbol}: {str(e)}")
                continue
        
        return signals

    async def _execute_trades(
        self,
        simulation: TradingSimulation,
        signals: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        db: Session
    ) -> List[SimulationTrade]:
        """
        Exécute les trades basés sur les signaux générés.
        """
        executed_trades = []
        current_positions = simulation.current_positions or {}
        
        for signal in signals:
            symbol = signal['symbol']
            signal_type = signal['signal']
            confidence = signal['confidence']
            current_price = signal['current_price']
            
            try:
                # Déterminer l'action à effectuer
                if signal_type == 'BUY' and confidence > 0.6:
                    # Calculer la taille de la position
                    position_size = simulation.current_capital * simulation.max_position_size
                    quantity = int(position_size / current_price)
                    
                    if quantity > 0:
                        trade = await self._create_buy_trade(
                            simulation, symbol, quantity, current_price, signal['reason'], db
                        )
                        if trade:
                            executed_trades.append(trade)
                            current_positions[symbol] = current_positions.get(symbol, 0) + quantity
                
                elif signal_type == 'SELL' and symbol in current_positions and current_positions[symbol] > 0:
                    # Vendre toute la position
                    quantity = current_positions[symbol]
                    trade = await self._create_sell_trade(
                        simulation, symbol, quantity, current_price, signal['reason'], db
                    )
                    if trade:
                        executed_trades.append(trade)
                        current_positions[symbol] = 0
                        
            except Exception as e:
                logger.error(f"Erreur exécution trade {symbol}: {str(e)}")
                continue
        
        # Mettre à jour les positions
        simulation.current_positions = current_positions
        
        return executed_trades

    async def _create_buy_trade(
        self,
        simulation: TradingSimulation,
        symbol: str,
        quantity: int,
        price: float,
        reason: str,
        db: Session
    ) -> Optional[SimulationTrade]:
        """
        Crée un trade d'achat et le sauvegarde en BDD.
        """
        try:
            total_cost = quantity * price
            fees = total_cost * 0.001  # 0.1% de frais
            
            # Vérifier que nous avons assez de capital
            if simulation.current_capital < (total_cost + fees):
                logger.warning(f"Capital insuffisant pour acheter {quantity} {symbol}")
                return None
            
            trade = SimulationTrade(
                simulation_id=simulation.id,
                etf_symbol=symbol,
                etf_isin=await self._get_isin_for_symbol(symbol),
                trade_type='BUY',
                quantity=quantity,
                price=price,
                total_amount=total_cost,
                fees=fees,
                reason=reason,
                executed_at=datetime.utcnow(),
                portfolio_value_before=simulation.current_capital
            )
            
            # Mettre à jour le capital
            simulation.current_capital -= (total_cost + fees)
            trade.portfolio_value_after = simulation.current_capital
            
            # Sauvegarder
            db.add(trade)
            simulation.total_trades += 1
            db.commit()
            
            logger.info(f"Trade BUY exécuté: {quantity} {symbol} à {price}€")
            return trade
            
        except Exception as e:
            logger.error(f"Erreur création trade BUY {symbol}: {str(e)}")
            db.rollback()
            return None

    async def _create_sell_trade(
        self,
        simulation: TradingSimulation,
        symbol: str,
        quantity: int,
        price: float,
        reason: str,
        db: Session
    ) -> Optional[SimulationTrade]:
        """
        Crée un trade de vente et le sauvegarde en BDD.
        """
        try:
            total_proceeds = quantity * price
            fees = total_proceeds * 0.001  # 0.1% de frais
            net_proceeds = total_proceeds - fees
            
            trade = SimulationTrade(
                simulation_id=simulation.id,
                etf_symbol=symbol,
                etf_isin=await self._get_isin_for_symbol(symbol),
                trade_type='SELL',
                quantity=quantity,
                price=price,
                total_amount=total_proceeds,
                fees=fees,
                reason=reason,
                executed_at=datetime.utcnow(),
                portfolio_value_before=simulation.current_capital
            )
            
            # Mettre à jour le capital
            simulation.current_capital += net_proceeds
            trade.portfolio_value_after = simulation.current_capital
            
            # Calculer le P&L du trade
            # TODO: Calculer le P&L réel basé sur le prix d'achat
            trade.profit_loss = 0  # Simplification pour l'instant
            
            # Sauvegarder
            db.add(trade)
            simulation.total_trades += 1
            db.commit()
            
            logger.info(f"Trade SELL exécuté: {quantity} {symbol} à {price}€")
            return trade
            
        except Exception as e:
            logger.error(f"Erreur création trade SELL {symbol}: {str(e)}")
            db.rollback()
            return None

    async def _get_isin_for_symbol(self, symbol: str) -> str:
        """
        Récupère l'ISIN pour un symbole donné.
        """
        try:
            etf_data = await self.etf_data_service.get_etf_data(symbol)
            return etf_data.isin if etf_data else ""
        except:
            return ""

    async def _update_simulation_after_rebalance(
        self,
        simulation: TradingSimulation,
        trades: List[SimulationTrade],
        market_data: Dict[str, Any],
        db: Session
    ) -> None:
        """
        Met à jour la simulation après un rééquilibrage.
        """
        try:
            # Calculer la valeur actuelle du portefeuille
            portfolio_value = simulation.current_capital
            
            for symbol, quantity in simulation.current_positions.items():
                if quantity > 0 and symbol in market_data:
                    portfolio_value += quantity * market_data[symbol]['current_price']
            
            # Calculer les statistiques
            total_return = portfolio_value - simulation.initial_capital
            total_return_percent = (total_return / simulation.initial_capital) * 100
            
            # Mettre à jour la simulation
            simulation.total_return = total_return
            simulation.total_return_percent = total_return_percent
            simulation.last_rebalance_at = datetime.utcnow()
            
            # Calculer le win rate
            if simulation.total_trades > 0:
                winning_trades = db.query(SimulationTrade).filter(
                    and_(
                        SimulationTrade.simulation_id == simulation.id,
                        SimulationTrade.profit_loss > 0
                    )
                ).count()
                
                simulation.winning_trades = winning_trades
                simulation.losing_trades = simulation.total_trades - winning_trades
                simulation.win_rate = (winning_trades / simulation.total_trades) * 100
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour simulation: {str(e)}")
            db.rollback()

    async def _create_performance_snapshot(self, simulation: TradingSimulation, db: Session) -> None:
        """
        Crée un snapshot de performance pour suivi historique.
        """
        try:
            snapshot = SimulationPerformanceSnapshot(
                simulation_id=simulation.id,
                timestamp=datetime.utcnow(),
                portfolio_value=simulation.current_capital + sum([
                    qty * 100 for qty in simulation.current_positions.values()  # Prix approximatif
                ]),
                total_return=simulation.total_return,
                total_return_percent=simulation.total_return_percent,
                positions_count=len([qty for qty in simulation.current_positions.values() if qty > 0])
            )
            
            db.add(snapshot)
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur création snapshot: {str(e)}")

    async def _calculate_final_stats(self, simulation: TradingSimulation, db: Session) -> None:
        """
        Calcule les statistiques finales d'une simulation.
        """
        try:
            # Calculer le Sharpe ratio, max drawdown, etc.
            # Implémentation simplifiée
            
            if simulation.total_return_percent > 0:
                simulation.sharpe_ratio = simulation.total_return_percent / 10  # Simplification
            
            # Calculer le max drawdown depuis les snapshots
            snapshots = db.query(SimulationPerformanceSnapshot).filter(
                SimulationPerformanceSnapshot.simulation_id == simulation.id
            ).order_by(SimulationPerformanceSnapshot.timestamp.asc()).all()
            
            if snapshots:
                max_value = simulation.initial_capital
                max_drawdown = 0
                
                for snapshot in snapshots:
                    if snapshot.portfolio_value > max_value:
                        max_value = snapshot.portfolio_value
                    drawdown = (max_value - snapshot.portfolio_value) / max_value * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                
                simulation.max_drawdown = max_drawdown
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Erreur calcul stats finales: {str(e)}")