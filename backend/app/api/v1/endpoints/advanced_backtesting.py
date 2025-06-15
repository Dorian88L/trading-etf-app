"""
Endpoints pour le backtesting avancé et la simulation de trading automatique
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel, Field
import uuid
from decimal import Decimal
import pandas as pd
import asyncio

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.real_market_data import get_real_market_data_service
from app.services.advanced_backtesting_service import get_advanced_backtesting_service
from app.services.trading_simulation_service import get_trading_simulation_service

import logging
logger = logging.getLogger(__name__)

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

# Nouveaux endpoints pour Walk-Forward Analysis et tests avec données futures

class WalkForwardRequest(BaseModel):
    """Requête pour Walk-Forward Analysis"""
    etf_symbol: str
    strategy_type: str = "rsi_mean_reversion"
    optimization_window_days: int = 252  # 1 an
    test_window_days: int = 63  # 3 mois
    step_size_days: int = 21  # 3 semaines
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    param_ranges: Optional[Dict[str, List]] = None

class FutureSimulationRequest(BaseModel):
    """Requête pour simulation avec données futures"""
    etf_symbol: str
    strategy_type: str = "rsi_mean_reversion"
    simulation_weeks: int = 12  # Simulation sur 12 semaines
    optimal_params: Optional[Dict[str, Any]] = None
    use_optimized_params: bool = True

@router.post("/walk-forward-analysis")
async def run_walk_forward_analysis(
    request: WalkForwardRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Exécute une analyse Walk-Forward complète
    """
    try:
        from app.services.walk_forward_analysis import get_walk_forward_service
        
        logger.info(f"Démarrage Walk-Forward Analysis pour {request.etf_symbol}")
        
        # Initialiser les services
        wf_service = get_walk_forward_service()
        market_service = get_real_market_data_service()
        
        # Récupérer les données historiques
        end_date = datetime.now() if not request.end_date else datetime.fromisoformat(request.end_date)
        start_date = (end_date - timedelta(days=500)) if not request.start_date else datetime.fromisoformat(request.start_date)
        
        # Obtenir les données de marché réelles
        historical_data = await market_service.get_historical_data(
            request.etf_symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if historical_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée historique trouvée pour {request.etf_symbol}"
            )
        
        # Exécuter l'analyse Walk-Forward
        results = wf_service.run_walk_forward_analysis(
            historical_data=historical_data,
            strategy_type=request.strategy_type,
            optimization_window_days=request.optimization_window_days,
            test_window_days=request.test_window_days,
            step_size_days=request.step_size_days,
            param_ranges=request.param_ranges
        )
        
        # Ajouter métadonnées
        results['metadata'] = {
            'etf_symbol': request.etf_symbol,
            'strategy_type': request.strategy_type,
            'data_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'total_days': len(historical_data)
            },
            'analysis_config': {
                'optimization_window': request.optimization_window_days,
                'test_window': request.test_window_days,
                'step_size': request.step_size_days
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "message": f"Walk-Forward Analysis terminée pour {request.etf_symbol}",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse Walk-Forward: {str(e)}"
        )

@router.post("/future-simulation")
async def run_future_simulation(
    request: FutureSimulationRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Teste une stratégie avec des données futures simulées
    Vérifie que le backtesting fonctionne avec des données à venir
    """
    try:
        import pandas as pd
        import numpy as np
        from app.services.walk_forward_analysis import get_walk_forward_service
        
        logger.info(f"Démarrage simulation futures pour {request.etf_symbol}")
        
        # Initialiser les services
        wf_service = get_walk_forward_service()
        market_service = get_real_market_data_service()
        
        # Récupérer les données historiques pour optimisation
        optimization_end = datetime.now()
        optimization_start = optimization_end - timedelta(days=252)  # 1 an pour optimisation
        
        historical_data = await market_service.get_historical_data(
            request.etf_symbol,
            start_date=optimization_start,
            end_date=optimization_end
        )
        
        if historical_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée historique trouvée pour {request.etf_symbol}"
            )
        
        # Obtenir les paramètres optimaux si demandé
        optimal_params = request.optimal_params
        if request.use_optimized_params and not optimal_params:
            # Optimiser sur les données historiques
            param_ranges = wf_service._get_default_param_ranges(request.strategy_type)
            optimal_params = wf_service._optimize_parameters(
                historical_data, 
                request.strategy_type, 
                param_ranges
            )
        
        # Générer des données futures simulées
        future_data = await _generate_future_simulation_data(
            historical_data, 
            request.simulation_weeks
        )
        
        # Tester la stratégie sur les données futures
        future_performance = wf_service._backtest_with_params(
            future_data,
            request.strategy_type,
            optimal_params or wf_service._get_default_params(request.strategy_type)
        )
        
        # Tester également sur données historiques pour comparaison
        historical_performance = wf_service._backtest_with_params(
            historical_data,
            request.strategy_type,
            optimal_params or wf_service._get_default_params(request.strategy_type)
        )
        
        # Analyse de la robustesse
        robustness_metrics = _calculate_robustness_metrics(
            historical_performance, 
            future_performance
        )
        
        return {
            "success": True,
            "message": f"Simulation futures terminée pour {request.etf_symbol}",
            "data": {
                "etf_symbol": request.etf_symbol,
                "strategy_type": request.strategy_type,
                "simulation_period": {
                    "weeks": request.simulation_weeks,
                    "start_date": optimization_end.isoformat(),
                    "end_date": (optimization_end + timedelta(weeks=request.simulation_weeks)).isoformat()
                },
                "optimal_params": optimal_params,
                "historical_performance": historical_performance,
                "future_performance": future_performance,
                "robustness_analysis": robustness_metrics,
                "validation_results": {
                    "strategy_stable": robustness_metrics['performance_consistency'] > 0.7,
                    "params_effective": robustness_metrics['parameter_effectiveness'] > 0.6,
                    "future_ready": robustness_metrics['forward_looking_score'] > 0.65
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la simulation futures: {str(e)}"
        )

# Fonctions utilitaires pour la simulation de données futures

async def _generate_future_simulation_data(
    historical_data: pd.DataFrame, 
    simulation_weeks: int
) -> pd.DataFrame:
    """
    Génère des données futures simulées basées sur les caractéristiques historiques
    """
    try:
        import pandas as pd
        import numpy as np
        
        # Analyser les caractéristiques des données historiques
        last_price = historical_data['close_price'].iloc[-1]
        returns = historical_data['close_price'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Volatilité annualisée
        mean_return = returns.mean() * 252  # Rendement annuel moyen
        
        # Générer des données futures
        simulation_days = simulation_weeks * 7
        future_dates = pd.date_range(
            start=historical_data.index[-1] + timedelta(days=1),
            periods=simulation_days,
            freq='D'
        )
        
        # Simulation de Monte Carlo pour les prix futurs
        np.random.seed(42)  # Pour la reproductibilité
        future_returns = np.random.normal(
            mean_return / 252,  # Rendement journalier moyen
            volatility / np.sqrt(252),  # Volatilité journalière
            simulation_days
        )
        
        # Calculer les prix futurs
        future_prices = [last_price]
        for ret in future_returns:
            future_prices.append(future_prices[-1] * (1 + ret))
        
        future_prices = future_prices[1:]  # Retirer le prix initial
        
        # Générer les volumes basés sur les patterns historiques
        avg_volume = historical_data['volume'].mean()
        volume_volatility = historical_data['volume'].std() / avg_volume
        
        future_volumes = np.random.lognormal(
            np.log(avg_volume),
            volume_volatility,
            simulation_days
        ).astype(int)
        
        # Créer le DataFrame des données futures
        future_data = pd.DataFrame({
            'open_price': future_prices,  # Simplification: open = close précédent
            'high_price': np.array(future_prices) * np.random.uniform(1.0, 1.02, simulation_days),
            'low_price': np.array(future_prices) * np.random.uniform(0.98, 1.0, simulation_days),
            'close_price': future_prices,
            'volume': future_volumes
        }, index=future_dates)
        
        # Assurer la cohérence high >= close >= low
        future_data['high_price'] = np.maximum(future_data['high_price'], future_data['close_price'])
        future_data['low_price'] = np.minimum(future_data['low_price'], future_data['close_price'])
        
        return future_data
        
    except Exception as e:
        raise Exception(f"Erreur génération données futures: {e}")

def _calculate_robustness_metrics(
    historical_perf: Dict[str, float], 
    future_perf: Dict[str, float]
) -> Dict[str, float]:
    """
    Calcule les métriques de robustesse entre performance historique et future
    """
    try:
        import numpy as np
        
        # Consistance des performances
        hist_sharpe = historical_perf.get('sharpe_ratio', 0)
        future_sharpe = future_perf.get('sharpe_ratio', 0)
        
        sharpe_consistency = 1 - abs(hist_sharpe - future_sharpe) / max(abs(hist_sharpe), abs(future_sharpe), 1)
        
        # Consistance des rendements
        hist_return = historical_perf.get('total_return', 0)
        future_return = future_perf.get('total_return', 0)
        
        return_consistency = 1 - abs(hist_return - future_return) / max(abs(hist_return), abs(future_return), 0.1)
        
        # Score de consistance globale
        performance_consistency = (sharpe_consistency + return_consistency) / 2
        
        # Efficacité des paramètres
        hist_trades = historical_perf.get('num_trades', 0)
        future_trades = future_perf.get('num_trades', 0)
        
        trades_consistency = 1 - abs(hist_trades - future_trades) / max(hist_trades, future_trades, 1)
        
        # Score d'efficacité des paramètres
        parameter_effectiveness = (trades_consistency + performance_consistency) / 2
        
        # Score forward-looking
        future_score_raw = (
            max(0, future_sharpe) * 0.4 +
            max(0, future_return) * 0.3 +
            min(1, future_trades / 10) * 0.3
        )
        
        forward_looking_score = min(1.0, future_score_raw)
        
        return {
            'performance_consistency': max(0, min(1, performance_consistency)),
            'parameter_effectiveness': max(0, min(1, parameter_effectiveness)),
            'forward_looking_score': forward_looking_score,
            'sharpe_ratio_stability': max(0, min(1, sharpe_consistency)),
            'return_stability': max(0, min(1, return_consistency)),
            'trades_stability': max(0, min(1, trades_consistency))
        }
        
    except Exception as e:
        return {
            'performance_consistency': 0.5,
            'parameter_effectiveness': 0.5,
            'forward_looking_score': 0.5,
            'sharpe_ratio_stability': 0.5,
            'return_stability': 0.5,
            'trades_stability': 0.5
        }