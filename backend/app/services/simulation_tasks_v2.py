"""
Tâches Celery pour les simulations de trading automatique - Version corrigée
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from celery import current_task
import logging
import time

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.trading_simulation import TradingSimulation, SimulationStatus
from app.services.trading_simulation_service_v2 import TradingSimulationService

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(bind=True, name="start_trading_simulation", autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def start_trading_simulation_task(self, simulation_id: int):
    """
    Tâche Celery pour démarrer et gérer une simulation de trading.
    Cette tâche boucle jusqu'à ce que la simulation soit terminée.
    """
    task_id = self.request.id
    logger.info(f"🚀 Démarrage de la simulation {simulation_id} avec tâche Celery {task_id}")
    
    db = get_db_session()
    simulation_service = TradingSimulationService()
    
    try:
        # Vérifier que la simulation existe et est démarrable
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id
        ).first()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} non trouvée")
        
        if simulation.status != SimulationStatus.PENDING:
            raise ValueError(f"Simulation {simulation_id} ne peut pas être démarrée depuis l'état {simulation.status}")
        
        # Mettre à jour le statut initial
        simulation.status = SimulationStatus.RUNNING
        simulation.started_at = datetime.utcnow()
        simulation.celery_task_id = task_id
        simulation.last_heartbeat = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Simulation {simulation_id} initialisée, début de la boucle de trading")
        
        # Boucle principale de trading
        iteration_count = 0
        max_iterations = 24 * 60 * 7  # Maximum 7 jours d'exécution (1 iteration = 1 minute)
        
        while iteration_count < max_iterations:
            try:
                # Recharger la simulation pour vérifier son état
                db.refresh(simulation)
                
                # Vérifier si la simulation doit continuer
                if simulation.status != SimulationStatus.RUNNING:
                    logger.info(f"Simulation {simulation_id} arrêtée (statut: {simulation.status})")
                    break
                
                # Mettre à jour le heartbeat
                simulation.last_heartbeat = datetime.utcnow()
                
                # Vérifier s'il faut effectuer un rééquilibrage
                should_rebalance = (
                    simulation.last_rebalance_at is None or 
                    datetime.utcnow() >= (simulation.last_rebalance_at + timedelta(hours=simulation.rebalance_frequency_hours))
                )
                
                if should_rebalance:
                    logger.info(f"⚖️ Rééquilibrage de la simulation {simulation_id}")
                    
                    # Exécuter le rééquilibrage via le service
                    trades = await simulation_service.execute_rebalance(simulation_id, db)
                    
                    logger.info(f"✅ Rééquilibrage terminé: {len(trades)} trades exécutés")
                    
                    # Recharger la simulation après le rééquilibrage
                    db.refresh(simulation)
                
                # Sauvegarder l'état
                db.commit()
                
                # Attendre avant la prochaine itération (1 minute)
                time.sleep(60)
                iteration_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de simulation {simulation_id}: {str(e)}")
                
                # Incrémenter le compteur d'erreurs
                simulation.error_count = (simulation.error_count or 0) + 1
                simulation.error_message = str(e)
                
                # Si trop d'erreurs consécutives, arrêter la simulation
                if simulation.error_count >= 5:
                    logger.error(f"Trop d'erreurs pour la simulation {simulation_id}, arrêt")
                    simulation.status = SimulationStatus.FAILED
                    simulation.ended_at = datetime.utcnow()
                    db.commit()
                    break
                
                db.commit()
                
                # Attendre plus longtemps en cas d'erreur
                time.sleep(300)  # 5 minutes
        
        # Vérifier le statut final
        if simulation.status == SimulationStatus.RUNNING:
            # Si la simulation est toujours en cours, elle a atteint sa limite d'itérations
            logger.info(f"Simulation {simulation_id} terminée (limite d'itérations atteinte)")
            await simulation_service.stop_simulation(simulation_id, db)
        
        logger.info(f"🏁 Tâche Celery terminée pour la simulation {simulation_id}")
        return {"simulation_id": simulation_id, "status": simulation.status.value, "total_trades": simulation.total_trades}
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale dans la tâche simulation {simulation_id}: {str(e)}")
        
        # Marquer la simulation comme échouée
        if 'simulation' in locals() and simulation:
            simulation.status = SimulationStatus.FAILED
            simulation.ended_at = datetime.utcnow()
            simulation.error_message = str(e)
            db.commit()
        
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, name="pause_trading_simulation")
def pause_trading_simulation_task(self, simulation_id: int):
    """
    Tâche Celery pour mettre en pause une simulation.
    """
    logger.info(f"⏸️ Mise en pause de la simulation {simulation_id}")
    
    db = get_db_session()
    
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id
        ).first()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} non trouvée")
        
        if simulation.status != SimulationStatus.RUNNING:
            logger.warning(f"Simulation {simulation_id} n'est pas en cours d'exécution (statut: {simulation.status})")
            return {"simulation_id": simulation_id, "status": "already_paused"}
        
        # Mettre en pause
        simulation.status = SimulationStatus.PAUSED
        simulation.paused_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Simulation {simulation_id} mise en pause")
        return {"simulation_id": simulation_id, "status": "paused"}
        
    except Exception as e:
        logger.error(f"❌ Erreur pause simulation {simulation_id}: {str(e)}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, name="stop_trading_simulation")
def stop_trading_simulation_task(self, simulation_id: int):
    """
    Tâche Celery pour arrêter définitivement une simulation.
    """
    logger.info(f"🛑 Arrêt de la simulation {simulation_id}")
    
    db = get_db_session()
    simulation_service = TradingSimulationService()
    
    try:
        # Arrêter la simulation via le service
        await simulation_service.stop_simulation(simulation_id, db)
        
        logger.info(f"✅ Simulation {simulation_id} arrêtée")
        return {"simulation_id": simulation_id, "status": "stopped"}
        
    except Exception as e:
        logger.error(f"❌ Erreur arrêt simulation {simulation_id}: {str(e)}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, name="cleanup_stale_simulations")
def cleanup_stale_simulations_task(self):
    """
    Tâche de nettoyage pour identifier et nettoyer les simulations abandonnées.
    """
    logger.info("🧹 Nettoyage des simulations abandonnées")
    
    db = get_db_session()
    
    try:
        # Trouver les simulations qui n'ont pas de heartbeat depuis plus de 10 minutes
        stale_time = datetime.utcnow() - timedelta(minutes=10)
        
        stale_simulations = db.query(TradingSimulation).filter(
            TradingSimulation.status == SimulationStatus.RUNNING,
            TradingSimulation.last_heartbeat < stale_time
        ).all()
        
        cleaned_count = 0
        
        for simulation in stale_simulations:
            logger.warning(f"Simulation abandonnée détectée: {simulation.id}")
            
            # Marquer comme échouée
            simulation.status = SimulationStatus.FAILED
            simulation.ended_at = datetime.utcnow()
            simulation.error_message = "Simulation abandonnée (pas de heartbeat)"
            
            cleaned_count += 1
        
        if cleaned_count > 0:
            db.commit()
            logger.info(f"✅ {cleaned_count} simulations abandonnées nettoyées")
        else:
            logger.info("✅ Aucune simulation abandonnée trouvée")
        
        return {"cleaned_simulations": cleaned_count}
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage simulations: {str(e)}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, name="health_check_simulations")
def health_check_simulations_task(self):
    """
    Tâche de vérification de santé pour monitorer les simulations actives.
    """
    logger.info("🔍 Vérification de santé des simulations")
    
    db = get_db_session()
    
    try:
        # Compter les simulations par statut
        running_count = db.query(TradingSimulation).filter(
            TradingSimulation.status == SimulationStatus.RUNNING
        ).count()
        
        paused_count = db.query(TradingSimulation).filter(
            TradingSimulation.status == SimulationStatus.PAUSED
        ).count()
        
        completed_count = db.query(TradingSimulation).filter(
            TradingSimulation.status == SimulationStatus.COMPLETED
        ).count()
        
        failed_count = db.query(TradingSimulation).filter(
            TradingSimulation.status == SimulationStatus.FAILED
        ).count()
        
        logger.info(f"📊 Statut simulations - Running: {running_count}, Paused: {paused_count}, Completed: {completed_count}, Failed: {failed_count}")
        
        return {
            "running": running_count,
            "paused": paused_count,
            "completed": completed_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur health check: {str(e)}")
        raise
        
    finally:
        db.close()


# Configuration des tâches périodiques
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Configuration des tâches périodiques.
    """
    # Nettoyage des simulations abandonnées toutes les 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        cleanup_stale_simulations_task.s(),
        name='cleanup_stale_simulations'
    )
    
    # Health check toutes les 2 minutes
    sender.add_periodic_task(
        120.0,  # 2 minutes
        health_check_simulations_task.s(),
        name='health_check_simulations'
    )