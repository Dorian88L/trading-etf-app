"""
Service de récupération automatique des simulations de trading
Redémarre les simulations actives au démarrage du serveur
"""

import logging
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.trading_simulation import TradingSimulation, SimulationStatus
from app.services.simulation_tasks import start_trading_simulation_task, cleanup_old_simulations_task

logger = logging.getLogger(__name__)

class SimulationRecoveryService:
    """Service pour récupérer et redémarrer les simulations actives"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def recover_active_simulations(self):
        """
        Récupère et redémarre toutes les simulations qui étaient actives
        """
        logger.info("🔄 Démarrage de la récupération des simulations actives...")
        
        try:
            # Trouver toutes les simulations qui étaient en cours
            active_simulations = self.db.query(TradingSimulation)\
                .filter(TradingSimulation.status.in_([SimulationStatus.RUNNING, SimulationStatus.PENDING]))\
                .all()
            
            recovered_count = 0
            expired_count = 0
            error_count = 0
            
            for simulation in active_simulations:
                try:
                    # Vérifier si la simulation a expiré
                    if self._is_simulation_expired(simulation):
                        logger.info(f"⏰ Simulation {simulation.id} expirée - marquage comme terminée")
                        simulation.status = SimulationStatus.COMPLETED
                        simulation.completed_at = datetime.utcnow()
                        expired_count += 1
                        continue
                    
                    # Vérifier si la simulation est récupérable
                    if self._is_simulation_recoverable(simulation):
                        logger.info(f"🚀 Redémarrage de la simulation {simulation.id}")
                        
                        # Relancer la tâche Celery
                        task = start_trading_simulation_task.delay(str(simulation.id))
                        
                        # Mettre à jour l'ID de tâche
                        simulation.celery_task_id = task.id
                        simulation.status = SimulationStatus.RUNNING
                        simulation.last_heartbeat = datetime.utcnow()
                        
                        recovered_count += 1
                        
                        logger.info(f"✅ Simulation {simulation.id} redémarrée avec tâche {task.id}")
                    else:
                        # Marquer comme erreur si non récupérable
                        logger.warning(f"⚠️ Simulation {simulation.id} non récupérable - marquage en erreur")
                        simulation.status = SimulationStatus.ERROR
                        simulation.error_message = "Simulation non récupérable au redémarrage"
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Erreur récupération simulation {simulation.id}: {e}")
                    simulation.status = SimulationStatus.ERROR
                    simulation.error_message = f"Erreur de récupération: {str(e)}"
                    error_count += 1
            
            # Sauvegarder les changements
            self.db.commit()
            
            logger.info(f"📊 Récupération terminée:")
            logger.info(f"   - Simulations redémarrées: {recovered_count}")
            logger.info(f"   - Simulations expirées: {expired_count}")
            logger.info(f"   - Simulations en erreur: {error_count}")
            
            # Lancer le nettoyage des anciennes simulations
            cleanup_old_simulations_task.delay()
            
            return {
                "recovered": recovered_count,
                "expired": expired_count,
                "errors": error_count,
                "total_processed": len(active_simulations)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale lors de la récupération: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()
    
    def _is_simulation_expired(self, simulation: TradingSimulation) -> bool:
        """
        Vérifie si une simulation a expiré
        """
        if simulation.target_end_date and datetime.utcnow() > simulation.target_end_date:
            return True
        
        if simulation.days_remaining is not None and simulation.days_remaining <= 0:
            return True
        
        return False
    
    def _is_simulation_recoverable(self, simulation: TradingSimulation) -> bool:
        """
        Vérifie si une simulation peut être récupérée
        """
        # Vérifier si la simulation n'a pas été abandonnée depuis trop longtemps
        if simulation.last_heartbeat:
            time_since_heartbeat = datetime.utcnow() - simulation.last_heartbeat
            if time_since_heartbeat > timedelta(hours=6):  # Plus de 6h sans heartbeat
                logger.warning(f"Simulation {simulation.id}: dernière activité il y a {time_since_heartbeat}")
                return False
        
        # Vérifier si la simulation a des erreurs répétées
        if simulation.error_count >= 5:
            logger.warning(f"Simulation {simulation.id}: trop d'erreurs ({simulation.error_count})")
            return False
        
        # Vérifier la cohérence des données
        if not simulation.etf_symbols or len(simulation.etf_symbols) == 0:
            logger.warning(f"Simulation {simulation.id}: pas d'ETF configurés")
            return False
        
        if simulation.initial_capital <= 0:
            logger.warning(f"Simulation {simulation.id}: capital initial invalide")
            return False
        
        return True
    
    def get_recovery_status(self) -> dict:
        """
        Récupère le statut de récupération des simulations
        """
        try:
            db = SessionLocal()
            
            # Compter les simulations par statut
            running_count = db.query(TradingSimulation)\
                .filter(TradingSimulation.status == SimulationStatus.RUNNING)\
                .count()
            
            paused_count = db.query(TradingSimulation)\
                .filter(TradingSimulation.status == SimulationStatus.PAUSED)\
                .count()
            
            completed_count = db.query(TradingSimulation)\
                .filter(TradingSimulation.status == SimulationStatus.COMPLETED)\
                .count()
            
            error_count = db.query(TradingSimulation)\
                .filter(TradingSimulation.status == SimulationStatus.ERROR)\
                .count()
            
            # Vérifier les simulations sans heartbeat récent
            stale_cutoff = datetime.utcnow() - timedelta(hours=2)
            stale_count = db.query(TradingSimulation)\
                .filter(
                    TradingSimulation.status == SimulationStatus.RUNNING,
                    TradingSimulation.last_heartbeat < stale_cutoff
                )\
                .count()
            
            db.close()
            
            return {
                "running": running_count,
                "paused": paused_count,
                "completed": completed_count,
                "error": error_count,
                "stale": stale_count,
                "total": running_count + paused_count + completed_count + error_count,
                "healthy_ratio": (running_count / (running_count + error_count + stale_count)) if (running_count + error_count + stale_count) > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération statut: {e}")
            return {"error": str(e)}
    
    def cleanup_abandoned_simulations(self):
        """
        Nettoie les simulations abandonnées
        """
        try:
            db = SessionLocal()
            
            # Simulatiions abandonnées = pas de heartbeat depuis plus de 4 heures
            cutoff_time = datetime.utcnow() - timedelta(hours=4)
            
            abandoned_simulations = db.query(TradingSimulation)\
                .filter(
                    TradingSimulation.status == SimulationStatus.RUNNING,
                    TradingSimulation.last_heartbeat < cutoff_time
                )\
                .all()
            
            cleaned_count = 0
            for simulation in abandoned_simulations:
                simulation.status = SimulationStatus.ERROR
                simulation.error_message = "Simulation abandonnée (pas d'activité récente)"
                simulation.completed_at = datetime.utcnow()
                cleaned_count += 1
            
            db.commit()
            db.close()
            
            logger.info(f"🧹 Nettoyé {cleaned_count} simulations abandonnées")
            return {"cleaned": cleaned_count}
            
        except Exception as e:
            logger.error(f"Erreur nettoyage simulations abandonnées: {e}")
            return {"error": str(e)}

# Service singleton
_recovery_service = None

def get_simulation_recovery_service() -> SimulationRecoveryService:
    """Récupère l'instance du service de récupération"""
    global _recovery_service
    if _recovery_service is None:
        _recovery_service = SimulationRecoveryService()
    return _recovery_service

def startup_recovery():
    """
    Fonction à appeler au démarrage de l'application pour récupérer les simulations
    """
    logger.info("🔄 Démarrage du processus de récupération des simulations...")
    
    try:
        recovery_service = get_simulation_recovery_service()
        result = recovery_service.recover_active_simulations()
        
        logger.info("✅ Récupération des simulations terminée avec succès")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des simulations: {e}")
        return {"error": str(e)}

def schedule_periodic_cleanup():
    """
    Programme le nettoyage périodique des simulations abandonnées
    """
    from app.celery_app import celery_app
    
    # Programmer le nettoyage toutes les heures
    celery_app.conf.beat_schedule.update({
        "cleanup-abandoned-simulations": {
            "task": "app.services.simulation_tasks.cleanup_old_simulations",
            "schedule": 3600.0,  # Toutes les heures
        }
    })
    
    logger.info("📅 Nettoyage périodique programmé toutes les heures")