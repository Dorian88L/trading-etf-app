"""
Tâches Celery pour les simulations de trading automatique
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from celery import current_task
import logging

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.trading_simulation import TradingSimulation, SimulationTrade, SimulationPerformanceSnapshot, SimulationStatus
from app.services.real_market_data import get_real_market_data_service
from app.services.advanced_backtesting_service import AdvancedBacktestingService

logger = logging.getLogger(__name__)

def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()

@celery_app.task(bind=True, name="start_trading_simulation")
def start_trading_simulation_task(self, simulation_id: str):
    """
    Tâche Celery pour démarrer une simulation de trading
    """
    task_id = self.request.id
    logger.info(f"🚀 Démarrage de la simulation {simulation_id} avec tâche Celery {task_id}")
    
    db = get_db_session()
    try:
        # Mettre à jour la simulation avec l'ID de tâche Celery
        simulation = db.query(TradingSimulation).filter(TradingSimulation.id == simulation_id).first()
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} non trouvée")
        
        simulation.celery_task_id = task_id
        simulation.status = SimulationStatus.RUNNING
        simulation.started_at = datetime.utcnow()
        simulation.last_heartbeat = datetime.utcnow()
        db.commit()
        
        # Lancer la boucle de simulation
        return run_simulation_loop(simulation_id)
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage simulation {simulation_id}: {e}")
        if 'simulation' in locals():
            simulation.status = SimulationStatus.ERROR
            simulation.error_message = str(e)
            simulation.error_count += 1
            db.commit()
        raise
    finally:
        db.close()

def run_simulation_loop(simulation_id: str):
    """
    Boucle principale de simulation de trading
    """
    db = get_db_session()
    market_service = get_real_market_data_service()
    backtesting_service = AdvancedBacktestingService(market_service)
    
    try:
        simulation = db.query(TradingSimulation).filter(TradingSimulation.id == simulation_id).first()
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} non trouvée")
        
        logger.info(f"🔄 Boucle de simulation démarrée pour {simulation_id}")
        iterations = 0
        max_iterations = simulation.duration_days * 24 * 60  # Maximum d'itérations (1 par minute)
        
        while (simulation.status == SimulationStatus.RUNNING and 
               simulation.days_remaining > 0 and 
               iterations < max_iterations):
            
            try:
                # Mettre à jour le heartbeat
                simulation.last_heartbeat = datetime.utcnow()
                simulation.days_remaining = max(0, (simulation.target_end_date - datetime.utcnow()).days)
                
                # Vérifier si c'est le moment de rééquilibrer
                if datetime.utcnow() >= simulation.next_rebalance:
                    logger.info(f"⚖️ Rééquilibrage de la simulation {simulation_id}")
                    
                    # Récupérer les données de marché actuelles
                    market_data = get_current_market_data_sync(market_service, simulation.etf_symbols)
                    
                    # Générer des signaux de trading
                    signals = generate_simulation_signals_sync(simulation, market_data, backtesting_service)
                    
                    # Exécuter les trades
                    new_trades = execute_simulation_trades_sync(db, simulation, signals, market_data)
                    
                    # Mettre à jour la prochaine date de rééquilibrage
                    simulation.next_rebalance = datetime.utcnow() + timedelta(hours=simulation.rebalance_frequency_hours)
                    
                    logger.info(f"✅ Rééquilibrage terminé: {len(new_trades)} trades exécutés")
                
                # Mettre à jour les valeurs du portfolio
                update_portfolio_values_sync(db, simulation, market_service)
                
                # Calculer et sauvegarder les métriques de performance
                if iterations % 60 == 0:  # Toutes les heures
                    save_performance_snapshot(db, simulation)
                
                # Sauvegarder l'état de la simulation
                db.commit()
                
                iterations += 1
                
                # Attendre 1 minute avant la prochaine itération
                import time
                time.sleep(60)
                
                # Recharger la simulation pour vérifier les changements de statut
                db.refresh(simulation)
                
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de simulation {simulation_id}: {e}")
                simulation.error_count += 1
                simulation.error_message = str(e)
                
                # Si trop d'erreurs, arrêter la simulation
                if simulation.error_count >= 5:
                    simulation.status = SimulationStatus.ERROR
                    break
                
                db.commit()
                import time
                time.sleep(60)  # Attendre avant de réessayer
        
        # Terminer la simulation
        if simulation.days_remaining <= 0:
            simulation.status = SimulationStatus.COMPLETED
            simulation.completed_at = datetime.utcnow()
            calculate_final_metrics(db, simulation)
        
        db.commit()
        logger.info(f"🏁 Simulation {simulation_id} terminée avec le statut: {simulation.status}")
        
        return {
            "simulation_id": simulation_id,
            "status": simulation.status.value,
            "final_value": simulation.current_value,
            "total_return_pct": simulation.total_return_pct,
            "iterations": iterations
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale dans la simulation {simulation_id}: {e}")
        simulation.status = SimulationStatus.ERROR
        simulation.error_message = str(e)
        db.commit()
        raise
    finally:
        db.close()

def get_current_market_data_sync(market_service, symbols):
    """Version synchrone de récupération des données de marché"""
    import asyncio
    
    async def _get_data():
        market_data = {}
        for symbol in symbols:
            try:
                data = await market_service.get_historical_data(symbol=symbol, period="1w")
                if data and len(data) > 0:
                    latest = data[-1]
                    market_data[symbol] = {
                        "current_price": latest.get("close_price", 0),
                        "volume": latest.get("volume", 0),
                        "timestamp": latest.get("timestamp"),
                        "historical_data": data[-20:] if len(data) >= 20 else data
                    }
            except Exception as e:
                logger.error(f"Erreur récupération données {symbol}: {e}")
                continue
        return market_data
    
    # Exécuter la fonction async dans le contexte Celery
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_get_data())

def generate_simulation_signals_sync(simulation, market_data, backtesting_service):
    """Version synchrone de génération de signaux"""
    import asyncio
    import pandas as pd
    
    async def _generate_signals():
        signals = []
        config = simulation.__dict__
        
        for symbol in simulation.etf_symbols:
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
                strategy_params = get_strategy_params(config)
                signal = await backtesting_service._calculate_signal(
                    simulation.strategy_type,
                    strategy_params,
                    df,
                    symbol
                )
                
                if signal:
                    # Ajuster la confiance selon le niveau de risque
                    confidence_adjustment = {
                        "conservative": -10,
                        "moderate": 0,
                        "aggressive": +5
                    }.get(simulation.risk_level, 0)
                    
                    signal["confidence"] = max(0, min(100, signal["confidence"] + confidence_adjustment))
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Erreur génération signal {symbol}: {e}")
                continue
        
        return signals
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_generate_signals())

def get_strategy_params(config):
    """Récupère les paramètres de stratégie"""
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

def execute_simulation_trades_sync(db: Session, simulation: TradingSimulation, signals, market_data):
    """Exécute les trades pour la simulation"""
    trades = []
    
    for signal in signals:
        symbol = signal["symbol"]
        action = signal["action"]
        confidence = signal["confidence"]
        
        # Filtrer par confiance minimum
        min_confidence = {"conservative": 75, "moderate": 65, "aggressive": 55}[simulation.risk_level]
        if confidence < min_confidence:
            continue
        
        try:
            if action == "BUY":
                trade = execute_simulation_buy_sync(db, simulation, signal, market_data)
            elif action == "SELL":
                trade = execute_simulation_sell_sync(db, simulation, signal, market_data)
            else:
                continue
            
            if trade:
                trades.append(trade)
                
        except Exception as e:
            logger.error(f"Erreur exécution trade {action} {symbol}: {e}")
            continue
    
    return trades

def execute_simulation_buy_sync(db: Session, simulation: TradingSimulation, signal, market_data):
    """Exécute un achat dans la simulation"""
    symbol = signal["symbol"]
    price = signal["price"]
    
    # Vérifier la liquidité disponible
    if simulation.cash < 50:  # Minimum 50€
        return None
    
    # Calculer la taille de position
    max_position_pct = {"conservative": 15, "moderate": 20, "aggressive": 25}[simulation.risk_level]
    max_position_value = simulation.current_value * (max_position_pct / 100)
    
    # Vérifier la position existante
    active_positions = simulation.active_positions or {}
    current_position_value = active_positions.get(symbol, {}).get("value", 0)
    
    if current_position_value >= max_position_value:
        return None  # Position déjà au max
    
    # Calculer le montant d'achat
    available_for_trade = min(
        simulation.cash * 0.8,  # Garder 20% de liquidité
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
    simulation.cash -= trade_amount
    
    if symbol in active_positions:
        pos = active_positions[symbol]
        total_quantity = pos["quantity"] + quantity
        total_cost = (pos["avg_price"] * pos["quantity"]) + (price * quantity)
        avg_price = total_cost / total_quantity
        
        active_positions[symbol].update({
            "quantity": total_quantity,
            "avg_price": avg_price,
            "current_price": price,
            "value": total_quantity * price
        })
    else:
        active_positions[symbol] = {
            "quantity": quantity,
            "avg_price": price,
            "current_price": price,
            "value": quantity * price,
            "unrealized_pnl": 0
        }
    
    simulation.active_positions = active_positions
    
    # Créer l'enregistrement du trade
    trade = SimulationTrade(
        simulation_id=simulation.id,
        timestamp=datetime.utcnow(),
        symbol=symbol,
        action="BUY",
        quantity=quantity,
        price=price,
        value=net_amount,
        commission=commission,
        reason=signal["reason"],
        confidence=signal["confidence"]
    )
    
    db.add(trade)
    logger.info(f"🟢 Simulation {simulation.id}: Achat {quantity:.4f} {symbol} à {price:.2f}€")
    return trade

def execute_simulation_sell_sync(db: Session, simulation: TradingSimulation, signal, market_data):
    """Exécute une vente dans la simulation"""
    symbol = signal["symbol"]
    price = signal["price"]
    
    active_positions = simulation.active_positions or {}
    if symbol not in active_positions:
        return None
    
    position = active_positions[symbol]
    
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
    simulation.cash += net_proceeds
    
    new_quantity = position["quantity"] - quantity_to_sell
    pnl = (price - position["avg_price"]) * quantity_to_sell
    
    if new_quantity < 0.001:  # Position fermée
        del active_positions[symbol]
    else:
        active_positions[symbol].update({
            "quantity": new_quantity,
            "current_price": price,
            "value": new_quantity * price
        })
    
    simulation.active_positions = active_positions
    
    # Créer l'enregistrement du trade
    trade = SimulationTrade(
        simulation_id=simulation.id,
        timestamp=datetime.utcnow(),
        symbol=symbol,
        action="SELL",
        quantity=quantity_to_sell,
        price=price,
        value=net_proceeds,
        commission=commission,
        reason=signal["reason"],
        confidence=signal["confidence"],
        pnl=pnl
    )
    
    db.add(trade)
    logger.info(f"🔴 Simulation {simulation.id}: Vente {quantity_to_sell:.4f} {symbol} à {price:.2f}€")
    return trade

def update_portfolio_values_sync(db: Session, simulation: TradingSimulation, market_service):
    """Met à jour les valeurs du portfolio"""
    try:
        total_positions_value = 0
        active_positions = simulation.active_positions or {}
        
        # Mettre à jour les prix des positions
        for symbol, position in active_positions.items():
            try:
                # Récupérer le prix actuel de manière simplifiée
                market_data = get_current_market_data_sync(market_service, [symbol])
                if symbol in market_data:
                    current_price = market_data[symbol]["current_price"]
                    position["current_price"] = current_price
                    position["value"] = position["quantity"] * current_price
                    position["unrealized_pnl"] = (current_price - position["avg_price"]) * position["quantity"]
                
                total_positions_value += position["value"]
            except Exception as e:
                logger.error(f"Erreur mise à jour prix {symbol}: {e}")
                total_positions_value += position["value"]  # Garder l'ancienne valeur
        
        # Mettre à jour la valeur totale
        simulation.current_value = simulation.cash + total_positions_value
        simulation.total_return_pct = (
            (simulation.current_value - simulation.initial_capital) / 
            simulation.initial_capital * 100
        )
        simulation.active_positions = active_positions
        
    except Exception as e:
        logger.error(f"Erreur mise à jour valeurs simulation {simulation.id}: {e}")

def save_performance_snapshot(db: Session, simulation: TradingSimulation):
    """Sauvegarde un snapshot de performance"""
    try:
        snapshot = SimulationPerformanceSnapshot(
            simulation_id=simulation.id,
            timestamp=datetime.utcnow(),
            total_value=simulation.current_value,
            cash=simulation.cash,
            positions_value=simulation.current_value - simulation.cash,
            total_return_pct=simulation.total_return_pct,
            positions_count=len(simulation.active_positions or {})
        )
        
        db.add(snapshot)
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde snapshot {simulation.id}: {e}")

def calculate_final_metrics(db: Session, simulation: TradingSimulation):
    """Calcule les métriques finales de la simulation"""
    try:
        # Récupérer tous les trades
        trades = db.query(SimulationTrade)\
            .filter(SimulationTrade.simulation_id == simulation.id)\
            .order_by(SimulationTrade.timestamp)\
            .all()
        
        # Calculer les métriques
        total_trades = len(trades)
        profitable_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
        total_commission = sum(t.commission for t in trades)
        
        final_metrics = {
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate_pct": (profitable_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_commission": total_commission,
            "net_profit": simulation.current_value - simulation.initial_capital,
            "duration_days": (simulation.completed_at - simulation.started_at).days
        }
        
        simulation.final_metrics = final_metrics
        
    except Exception as e:
        logger.error(f"Erreur calcul métriques finales {simulation.id}: {e}")

@celery_app.task(name="pause_trading_simulation")
def pause_trading_simulation_task(simulation_id: str):
    """Tâche pour mettre en pause une simulation"""
    db = get_db_session()
    try:
        simulation = db.query(TradingSimulation).filter(TradingSimulation.id == simulation_id).first()
        if simulation:
            simulation.status = SimulationStatus.PAUSED
            db.commit()
            logger.info(f"⏸️ Simulation {simulation_id} mise en pause")
        return {"simulation_id": simulation_id, "status": "paused"}
    finally:
        db.close()

@celery_app.task(name="stop_trading_simulation")
def stop_trading_simulation_task(simulation_id: str):
    """Tâche pour arrêter une simulation"""
    db = get_db_session()
    try:
        simulation = db.query(TradingSimulation).filter(TradingSimulation.id == simulation_id).first()
        if simulation:
            simulation.status = SimulationStatus.STOPPED
            simulation.completed_at = datetime.utcnow()
            calculate_final_metrics(db, simulation)
            db.commit()
            logger.info(f"🛑 Simulation {simulation_id} arrêtée")
        return {"simulation_id": simulation_id, "status": "stopped"}
    finally:
        db.close()

@celery_app.task(name="cleanup_old_simulations")
def cleanup_old_simulations_task():
    """Tâche de nettoyage des anciennes simulations"""
    db = get_db_session()
    try:
        # Nettoyer les simulations abandonnées (pas de heartbeat depuis plus de 2 heures)
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        abandoned_simulations = db.query(TradingSimulation)\
            .filter(
                TradingSimulation.status == SimulationStatus.RUNNING,
                TradingSimulation.last_heartbeat < cutoff_time
            ).all()
        
        for sim in abandoned_simulations:
            sim.status = SimulationStatus.ERROR
            sim.error_message = "Simulation abandonnée (pas de heartbeat)"
            
        db.commit()
        logger.info(f"🧹 Nettoyé {len(abandoned_simulations)} simulations abandonnées")
        
        return {"cleaned_simulations": len(abandoned_simulations)}
        
    except Exception as e:
        logger.error(f"Erreur nettoyage simulations: {e}")
        return {"error": str(e)}
    finally:
        db.close()