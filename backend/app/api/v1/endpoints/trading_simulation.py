from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.trading_simulation import TradingSimulation, SimulationStatus, SimulationTrade
from app.services.trading_simulation_service_v2 import TradingSimulationService
from app.schemas.trading_simulation import (
    TradingSimulationCreate,
    TradingSimulationResponse,
    TradingSimulationUpdate,
    SimulationTradeResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Instance du service de simulation
simulation_service = TradingSimulationService()


@router.get("/available-etfs")
async def get_available_etfs():
    """
    Obtenir la liste des ETFs disponibles pour les simulations avec données réelles.
    """
    try:
        etfs = await simulation_service.get_available_etfs_with_data()
        return {
            "success": True,
            "count": len(etfs),
            "etfs": etfs
        }
    except Exception as e:
        logger.error(f"Erreur récupération ETFs disponibles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des ETFs disponibles"
        )


@router.post("/test", response_model=TradingSimulationResponse)
async def test_create_simulation(
    simulation_data: TradingSimulationCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint de test pour créer une simulation sans authentification.
    """
    try:
        # Utiliser un user_id de test (remplacer par un UUID existant en base)
        test_user_id = "1d104a96-3d45-4861-b48f-6d3a529b2683"  # UUID de test
        
        logger.info(f"TEST: Création d'une simulation pour l'utilisateur {test_user_id}")
        
        # Créer la simulation via le service
        simulation = await simulation_service.create_simulation(
            db=db,
            user_id=test_user_id,
            config=simulation_data
        )
        
        logger.info(f"TEST: Simulation créée avec l'ID: {simulation.id}")
        return simulation
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la simulation: {str(e)}"
        )


@router.get("/leaderboard")
async def get_simulation_leaderboard(
    timeframe: str = "week",
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Obtenir le classement des meilleures simulations.
    """
    try:
        # Pour l'instant, retourner un classement simple basé sur les simulations récentes
        query = db.query(TradingSimulation).filter(
            TradingSimulation.status.in_([SimulationStatus.RUNNING, SimulationStatus.COMPLETED])
        ).order_by(TradingSimulation.total_return_pct.desc()).limit(limit)
        
        simulations = query.all()
        
        leaderboard = []
        for i, sim in enumerate(simulations, 1):
            leaderboard.append({
                "rank": i,
                "simulation_id": str(sim.id),
                "name": sim.name,
                "user_id": str(sim.user_id),
                "total_return_pct": sim.total_return_pct or 0.0,
                "duration_days": sim.duration_days,
                "status": sim.status.value,
                "started_at": sim.started_at.isoformat() if sim.started_at else None
            })
        
        return {
            "success": True,
            "timeframe": timeframe,
            "leaderboard": leaderboard,
            "count": len(leaderboard)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du classement: {str(e)}"
        )


@router.post("/", response_model=TradingSimulationResponse)
async def create_simulation(
    simulation_data: TradingSimulationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle simulation de trading automatique.
    """
    try:
        logger.info(f"Création d'une simulation pour l'utilisateur {current_user.id}")
        
        # Créer la simulation via le service
        simulation = await simulation_service.create_simulation(
            db=db,
            user_id=current_user.id,
            config=simulation_data
        )
        
        logger.info(f"Simulation créée avec l'ID: {simulation.id}")
        return simulation
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la simulation: {str(e)}"
        )


@router.get("/", response_model=List[TradingSimulationResponse])
async def get_user_simulations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[SimulationStatus] = None
):
    """
    Récupérer toutes les simulations de l'utilisateur connecté.
    """
    try:
        query = db.query(TradingSimulation).filter(
            TradingSimulation.user_id == current_user.id
        )
        
        if status_filter:
            query = query.filter(TradingSimulation.status == status_filter)
            
        simulations = query.order_by(TradingSimulation.created_at.desc()).all()
        
        logger.info(f"Récupération de {len(simulations)} simulations pour l'utilisateur {current_user.id}")
        return simulations
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des simulations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des simulations: {str(e)}"
        )


@router.get("/{simulation_id}", response_model=TradingSimulationResponse)
async def get_simulation(
    simulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer une simulation spécifique.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        return simulation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la simulation {simulation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la simulation: {str(e)}"
        )


@router.post("/{simulation_id}/start")
async def start_simulation(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Démarrer une simulation de trading.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        if simulation.status != SimulationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La simulation ne peut pas être démarrée depuis l'état: {simulation.status}"
            )
        
        # Démarrer la simulation via le service
        await simulation_service.start_simulation(simulation_id, db)
        
        logger.info(f"Simulation {simulation_id} démarrée par l'utilisateur {current_user.id}")
        return {"message": "Simulation démarrée avec succès", "simulation_id": simulation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la simulation {simulation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du démarrage de la simulation: {str(e)}"
        )


@router.post("/{simulation_id}/pause")
async def pause_simulation(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre en pause une simulation de trading.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        if simulation.status != SimulationStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La simulation ne peut pas être mise en pause depuis l'état: {simulation.status}"
            )
        
        # Mettre en pause via le service
        await simulation_service.pause_simulation(simulation_id, db)
        
        logger.info(f"Simulation {simulation_id} mise en pause par l'utilisateur {current_user.id}")
        return {"message": "Simulation mise en pause avec succès", "simulation_id": simulation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise en pause de la simulation {simulation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise en pause de la simulation: {str(e)}"
        )


@router.post("/{simulation_id}/stop")
async def stop_simulation(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Arrêter définitivement une simulation de trading.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        if simulation.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La simulation est déjà terminée: {simulation.status}"
            )
        
        # Arrêter la simulation via le service
        await simulation_service.stop_simulation(simulation_id, db)
        
        logger.info(f"Simulation {simulation_id} arrêtée par l'utilisateur {current_user.id}")
        return {"message": "Simulation arrêtée avec succès", "simulation_id": simulation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de la simulation {simulation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'arrêt de la simulation: {str(e)}"
        )


@router.get("/{simulation_id}/trades", response_model=List[SimulationTradeResponse])
async def get_simulation_trades(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """
    Récupérer l'historique des trades d'une simulation.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
        
        trades = db.query(SimulationTrade).filter(
            SimulationTrade.simulation_id == simulation_id
        ).order_by(
            SimulationTrade.executed_at.desc()
        ).offset(offset).limit(limit).all()
        
        logger.info(f"Récupération de {len(trades)} trades pour la simulation {simulation_id}")
        return trades
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des trades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des trades: {str(e)}"
        )


@router.put("/{simulation_id}", response_model=TradingSimulationResponse)  
async def update_simulation(
    simulation_id: int,
    simulation_update: TradingSimulationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les paramètres d'une simulation.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        # Seules les simulations en pause ou créées peuvent être modifiées
        if simulation.status not in [SimulationStatus.PENDING, SimulationStatus.PAUSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La simulation ne peut pas être modifiée dans l'état: {simulation.status}"
            )
        
        # Mettre à jour les champs modifiables
        update_data = simulation_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(simulation, field, value)
        
        db.commit()
        db.refresh(simulation)
        
        logger.info(f"Simulation {simulation_id} mise à jour par l'utilisateur {current_user.id}")
        return simulation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la simulation {simulation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de la simulation: {str(e)}"  
        )


@router.delete("/{simulation_id}")
async def delete_simulation(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une simulation et tous ses trades associés.
    """
    try:
        simulation = db.query(TradingSimulation).filter(
            TradingSimulation.id == simulation_id,
            TradingSimulation.user_id == current_user.id
        ).first()
        
        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation non trouvée"
            )
            
        # Arrêter la simulation si elle est en cours
        if simulation.status == SimulationStatus.RUNNING:
            await simulation_service.stop_simulation(simulation_id, db)
        
        # Supprimer tous les trades associés
        db.query(SimulationTrade).filter(
            SimulationTrade.simulation_id == simulation_id
        ).delete()
        
        # Supprimer la simulation
        db.delete(simulation)
        db.commit()
        
        logger.info(f"Simulation {simulation_id} supprimée par l'utilisateur {current_user.id}")
        return {"message": "Simulation supprimée avec succès", "simulation_id": simulation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la simulation {simulation_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la simulation: {str(e)}"
        )