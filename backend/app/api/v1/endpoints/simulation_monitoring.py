"""
Endpoints pour le monitoring des simulations de trading
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.simulation_recovery_service import get_simulation_recovery_service
from app.core.database import get_db
from app.models.trading_simulation import TradingSimulation, SimulationStatus
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/simulation-status")
async def get_simulation_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le statut général des simulations
    """
    try:
        recovery_service = get_simulation_recovery_service()
        status = recovery_service.get_recovery_status()
        
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération statut: {str(e)}")

@router.get("/user-simulations-health")
async def get_user_simulations_health(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère l'état de santé des simulations de l'utilisateur
    """
    try:
        # Compter les simulations par statut pour cet utilisateur
        user_simulations = db.query(TradingSimulation)\
            .filter(TradingSimulation.user_id == current_user.id)\
            .all()
        
        status_counts = {}
        for status in SimulationStatus:
            status_counts[status.value] = 0
        
        active_simulations = []
        for sim in user_simulations:
            status_counts[sim.status.value] += 1
            
            if sim.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
                # Vérifier la santé de la simulation
                is_healthy = True
                health_issues = []
                
                if sim.status == SimulationStatus.RUNNING:
                    # Vérifier le heartbeat
                    if sim.last_heartbeat:
                        time_since_heartbeat = datetime.utcnow() - sim.last_heartbeat
                        if time_since_heartbeat > timedelta(minutes=10):
                            is_healthy = False
                            health_issues.append(f"Pas d'activité depuis {time_since_heartbeat}")
                    
                    # Vérifier les erreurs
                    if sim.error_count > 0:
                        health_issues.append(f"{sim.error_count} erreurs")
                
                active_simulations.append({
                    "id": str(sim.id),
                    "name": sim.name,
                    "status": sim.status.value,
                    "current_value": sim.current_value,
                    "total_return_pct": sim.total_return_pct,
                    "days_remaining": sim.days_remaining,
                    "is_healthy": is_healthy,
                    "health_issues": health_issues,
                    "last_heartbeat": sim.last_heartbeat.isoformat() if sim.last_heartbeat else None,
                    "celery_task_id": sim.celery_task_id
                })
        
        return {
            "success": True,
            "data": {
                "status_counts": status_counts,
                "active_simulations": active_simulations,
                "total_simulations": len(user_simulations),
                "healthy_simulations": sum(1 for sim in active_simulations if sim["is_healthy"])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération santé: {str(e)}")

@router.post("/cleanup-abandoned")
async def cleanup_abandoned_simulations(
    current_user: User = Depends(get_current_active_user)
):
    """
    Lance le nettoyage des simulations abandonnées (admin seulement)
    """
    try:
        recovery_service = get_simulation_recovery_service()
        result = recovery_service.cleanup_abandoned_simulations()
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

@router.post("/recover-simulations")
async def recover_simulations(
    current_user: User = Depends(get_current_active_user)
):
    """
    Force la récupération des simulations (admin seulement)
    """
    try:
        from app.services.simulation_recovery_service import startup_recovery
        result = startup_recovery()
        
        return {
            "success": True,
            "data": result,
            "message": "Récupération forcée des simulations terminée",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération: {str(e)}")

@router.get("/celery-tasks")
async def get_celery_tasks_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le statut des tâches Celery pour les simulations de l'utilisateur
    """
    try:
        # Récupérer les simulations avec tâches Celery actives
        running_simulations = db.query(TradingSimulation)\
            .filter(
                TradingSimulation.user_id == current_user.id,
                TradingSimulation.status == SimulationStatus.RUNNING,
                TradingSimulation.celery_task_id.isnot(None)
            )\
            .all()
        
        tasks_info = []
        for sim in running_simulations:
            task_info = {
                "simulation_id": str(sim.id),
                "simulation_name": sim.name,
                "celery_task_id": sim.celery_task_id,
                "status": sim.status.value,
                "last_heartbeat": sim.last_heartbeat.isoformat() if sim.last_heartbeat else None,
                "error_count": sim.error_count,
                "started_at": sim.started_at.isoformat() if sim.started_at else None
            }
            
            # Tentative d'inspection de la tâche Celery (si disponible)
            try:
                from app.celery_app import celery_app
                from celery import current_app
                
                # Récupérer l'état de la tâche
                task_result = celery_app.AsyncResult(sim.celery_task_id)
                task_info["celery_status"] = task_result.status
                task_info["celery_info"] = task_result.info if task_result.info else None
                
            except Exception as e:
                task_info["celery_status"] = "UNKNOWN"
                task_info["celery_error"] = str(e)
            
            tasks_info.append(task_info)
        
        return {
            "success": True,
            "data": {
                "running_tasks": len(tasks_info),
                "tasks": tasks_info
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération tâches: {str(e)}")

@router.get("/simulation/{simulation_id}/logs")
async def get_simulation_logs(
    simulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les logs d'une simulation spécifique
    """
    try:
        # Vérifier que la simulation appartient à l'utilisateur
        simulation = db.query(TradingSimulation)\
            .filter(
                TradingSimulation.id == simulation_id,
                TradingSimulation.user_id == current_user.id
            )\
            .first()
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation non trouvée")
        
        # Récupérer les informations de debug
        debug_info = {
            "simulation_id": str(simulation.id),
            "name": simulation.name,
            "status": simulation.status.value,
            "created_at": simulation.created_at.isoformat(),
            "started_at": simulation.started_at.isoformat() if simulation.started_at else None,
            "last_heartbeat": simulation.last_heartbeat.isoformat() if simulation.last_heartbeat else None,
            "error_count": simulation.error_count,
            "error_message": simulation.error_message,
            "celery_task_id": simulation.celery_task_id,
            "etf_symbols": simulation.etf_symbols,
            "current_value": simulation.current_value,
            "initial_capital": simulation.initial_capital,
            "total_return_pct": simulation.total_return_pct,
            "days_remaining": simulation.days_remaining,
            "active_positions": simulation.active_positions,
            "next_rebalance": simulation.next_rebalance.isoformat() if simulation.next_rebalance else None
        }
        
        # Récupérer les derniers trades
        from app.models.trading_simulation import SimulationTrade
        recent_trades = db.query(SimulationTrade)\
            .filter(SimulationTrade.simulation_id == simulation_id)\
            .order_by(SimulationTrade.timestamp.desc())\
            .limit(10)\
            .all()
        
        trades_info = []
        for trade in recent_trades:
            trades_info.append({
                "timestamp": trade.timestamp.isoformat(),
                "symbol": trade.symbol,
                "action": trade.action,
                "quantity": trade.quantity,
                "price": trade.price,
                "value": trade.value,
                "reason": trade.reason,
                "confidence": trade.confidence
            })
        
        debug_info["recent_trades"] = trades_info
        
        return {
            "success": True,
            "data": debug_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération logs: {str(e)}")