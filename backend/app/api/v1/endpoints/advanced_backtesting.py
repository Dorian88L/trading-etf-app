"""
Endpoints pour le backtesting avancé et la simulation de trading automatique
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel, Field
import uuid
from decimal import Decimal
import asyncio

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.real_market_data import get_real_market_data_service
from app.services.advanced_backtesting_service import get_advanced_backtesting_service
from app.services.trading_simulation_service import get_trading_simulation_service

router = APIRouter()

# Modèles de données
class BacktestConfig(BaseModel):
    name: str = Field(..., description="Nom du backtest")
    start_date: date = Field(..., description="Date de début")
    end_date: date = Field(..., description="Date de fin")
    initial_capital: float = Field(default=10000, ge=100, description="Capital initial en euros")
    strategy_type: str = Field(..., description="Type de stratégie (rsi, macd, bollinger, advanced)")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de la stratégie")
    etf_symbols: List[str] = Field(..., description="Symboles des ETFs à trader")
    rebalance_frequency: str = Field(default="daily", description="Fréquence de rééquilibrage")
    transaction_cost_pct: float = Field(default=0.1, description="Coût de transaction en %")
    stop_loss_pct: Optional[float] = Field(default=None, description="Stop loss en %")
    take_profit_pct: Optional[float] = Field(default=None, description="Take profit en %")
    max_position_size_pct: float = Field(default=10, description="Taille max d'une position en %")

class TradingSimulationConfig(BaseModel):
    name: str = Field(..., description="Nom de la simulation")
    initial_capital: float = Field(default=100, ge=50, le=10000, description="Capital initial en euros")
    duration_days: int = Field(default=30, ge=7, le=365, description="Durée de simulation en jours")
    strategy_type: str = Field(default="advanced", description="Type de stratégie de trading")
    risk_level: str = Field(default="moderate", description="Niveau de risque (conservative, moderate, aggressive)")
    allowed_etf_sectors: List[str] = Field(default_factory=list, description="Secteurs d'ETF autorisés")
    rebalance_frequency_hours: int = Field(default=24, description="Fréquence de rééquilibrage en heures")
    auto_stop_loss: bool = Field(default=True, description="Stop loss automatique")
    auto_take_profit: bool = Field(default=True, description="Take profit automatique")

class BacktestResult(BaseModel):
    id: str
    config: BacktestConfig
    total_return_pct: float
    annualized_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    number_of_trades: int
    final_value: float
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]
    benchmark_comparison: Dict[str, Any]
    created_at: datetime
    execution_time_seconds: float

class TradingSimulationResult(BaseModel):
    id: str
    config: TradingSimulationConfig
    current_value: float
    total_return_pct: float
    daily_returns: List[Dict[str, Any]]
    active_positions: List[Dict[str, Any]]
    completed_trades: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]
    next_rebalance: datetime
    status: str  # "running", "completed", "paused", "error"
    created_at: datetime
    last_updated: datetime

@router.post("/backtest/run", response_model=BacktestResult)
async def run_advanced_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Lance un backtest avancé avec des données réelles
    """
    backtesting_service = get_advanced_backtesting_service()
    
    try:
        # Valider la configuration
        if config.end_date <= config.start_date:
            raise HTTPException(status_code=400, detail="La date de fin doit être postérieure à la date de début")
        
        if len(config.etf_symbols) == 0:
            raise HTTPException(status_code=400, detail="Au moins un ETF doit être sélectionné")
        
        # Lancer le backtest
        result = await backtesting_service.run_backtest(
            config=config,
            user_id=current_user.id
        )
        
        # Sauvegarder le résultat en base de données
        background_tasks.add_task(
            backtesting_service.save_backtest_result,
            result,
            current_user.id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du backtest: {str(e)}")

@router.get("/backtest/history", response_model=List[BacktestResult])
async def get_backtest_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Récupère l'historique des backtests de l'utilisateur
    """
    backtesting_service = get_advanced_backtesting_service()
    
    try:
        results = await backtesting_service.get_user_backtests(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@router.delete("/backtest/{backtest_id}")
async def delete_backtest(
    backtest_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Supprime un backtest
    """
    backtesting_service = get_advanced_backtesting_service()
    
    try:
        await backtesting_service.delete_backtest(
            backtest_id=backtest_id,
            user_id=current_user.id
        )
        return {"message": "Backtest supprimé avec succès"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@router.post("/simulation/start", response_model=TradingSimulationResult)
async def start_trading_simulation(
    config: TradingSimulationConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Démarre une simulation de trading automatique
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        # Créer une nouvelle simulation
        simulation = await simulation_service.create_simulation(
            config=config,
            user_id=current_user.id
        )
        
        # Lancer la simulation en arrière-plan
        background_tasks.add_task(
            simulation_service.run_simulation_loop,
            simulation.id
        )
        
        return simulation
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la simulation: {str(e)}")

@router.get("/simulation/active", response_model=List[TradingSimulationResult])
async def get_active_simulations(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Récupère les simulations actives de l'utilisateur
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        simulations = await simulation_service.get_user_simulations(
            user_id=current_user.id,
            status_filter="running"
        )
        return simulations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@router.get("/simulation/{simulation_id}", response_model=TradingSimulationResult)
async def get_simulation_details(
    simulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Récupère les détails d'une simulation
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        simulation = await simulation_service.get_simulation(
            simulation_id=simulation_id,
            user_id=current_user.id
        )
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation non trouvée")
        
        return simulation
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@router.post("/simulation/{simulation_id}/pause")
async def pause_simulation(
    simulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Met en pause une simulation
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        await simulation_service.pause_simulation(
            simulation_id=simulation_id,
            user_id=current_user.id
        )
        return {"message": "Simulation mise en pause"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise en pause: {str(e)}")

@router.post("/simulation/{simulation_id}/resume")
async def resume_simulation(
    simulation_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Reprend une simulation en pause
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        await simulation_service.resume_simulation(
            simulation_id=simulation_id,
            user_id=current_user.id
        )
        
        # Relancer la boucle de simulation
        background_tasks.add_task(
            simulation_service.run_simulation_loop,
            simulation_id
        )
        
        return {"message": "Simulation reprise"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la reprise: {str(e)}")

@router.delete("/simulation/{simulation_id}")
async def stop_simulation(
    simulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Arrête et supprime une simulation
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        await simulation_service.stop_simulation(
            simulation_id=simulation_id,
            user_id=current_user.id
        )
        return {"message": "Simulation arrêtée et supprimée"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'arrêt: {str(e)}")

@router.get("/strategies/available")
async def get_available_strategies():
    """
    Récupère la liste des stratégies disponibles
    """
    return {
        "strategies": [
            {
                "id": "rsi",
                "name": "RSI (Relative Strength Index)",
                "description": "Stratégie basée sur les niveaux de surachat et survente",
                "params": {
                    "period": {"type": "int", "default": 14, "min": 5, "max": 50},
                    "oversold": {"type": "int", "default": 30, "min": 10, "max": 40},
                    "overbought": {"type": "int", "default": 70, "min": 60, "max": 90}
                }
            },
            {
                "id": "macd",
                "name": "MACD (Moving Average Convergence Divergence)",
                "description": "Stratégie basée sur les croisements de moyennes mobiles",
                "params": {
                    "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20},
                    "slow_period": {"type": "int", "default": 26, "min": 15, "max": 40},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
                }
            },
            {
                "id": "bollinger",
                "name": "Bandes de Bollinger",
                "description": "Stratégie basée sur la volatilité et les bandes",
                "params": {
                    "period": {"type": "int", "default": 20, "min": 10, "max": 50},
                    "deviation": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
                }
            },
            {
                "id": "advanced",
                "name": "Stratégie Avancée Multi-Indicateurs",
                "description": "Combine plusieurs indicateurs avec machine learning",
                "params": {
                    "risk_level": {"type": "string", "default": "moderate", "options": ["conservative", "moderate", "aggressive"]},
                    "use_ml": {"type": "bool", "default": True},
                    "sentiment_weight": {"type": "float", "default": 0.3, "min": 0.0, "max": 1.0}
                }
            }
        ]
    }

@router.get("/etf/sectors")
async def get_etf_sectors():
    """
    Récupère la liste des secteurs d'ETF disponibles
    """
    market_service = get_real_market_data_service()
    
    try:
        sectors = await market_service.get_available_sectors()
        return {"sectors": sectors}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@router.get("/simulation/leaderboard")
async def get_simulation_leaderboard(
    timeframe: str = "week",  # week, month, all_time
    limit: int = 10
):
    """
    Récupère le classement des meilleures simulations
    """
    simulation_service = get_trading_simulation_service()
    
    try:
        leaderboard = await simulation_service.get_leaderboard(
            timeframe=timeframe,
            limit=limit
        )
        return {"leaderboard": leaderboard}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")