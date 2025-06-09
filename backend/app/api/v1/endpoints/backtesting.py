"""
Endpoints pour le backtesting de stratégies
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.backtesting_engine import BacktestingEngine

router = APIRouter()

class BacktestRequest(BaseModel):
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    transaction_fee: float = 0.001
    strategy: str = "momentum"

class BacktestResponse(BaseModel):
    start_date: str
    end_date: str
    symbols: List[str]
    strategy: str
    initial_capital: float
    final_capital: float
    metrics: dict
    trades: List[dict]
    portfolio_evolution: List[dict]

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Lance un backtest avec les paramètres spécifiés
    """
    try:
        # Validation des dates
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="La date de début doit être antérieure à la date de fin")
        
        # Limitation à 2 ans maximum
        max_period = timedelta(days=730)
        if request.end_date - request.start_date > max_period:
            raise HTTPException(status_code=400, detail="Période maximum de 2 ans autorisée")
        
        # Validation des symboles
        if not request.symbols or len(request.symbols) > 10:
            raise HTTPException(status_code=400, detail="Entre 1 et 10 symboles autorisés")
        
        # Validation de la stratégie
        valid_strategies = ["momentum", "mean_reversion", "breakout"]
        if request.strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Stratégie doit être parmi: {valid_strategies}")
        
        # Lancer le backtest
        engine = BacktestingEngine()
        results = await engine.run_backtest(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            transaction_fee=request.transaction_fee,
            strategy=request.strategy
        )
        
        return BacktestResponse(**results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du backtest: {str(e)}")

@router.get("/strategies")
async def get_available_strategies():
    """
    Retourne la liste des stratégies disponibles
    """
    return {
        "strategies": [
            {
                "name": "momentum",
                "description": "Stratégie basée sur le momentum - suit les tendances",
                "parameters": {
                    "short_ma": 5,
                    "long_ma": 20
                }
            },
            {
                "name": "mean_reversion", 
                "description": "Stratégie de retour à la moyenne - achète bas, vend haut",
                "parameters": {
                    "bollinger_period": 20,
                    "bollinger_std": 2
                }
            },
            {
                "name": "breakout",
                "description": "Stratégie de cassure - suit les breakouts avec volume",
                "parameters": {
                    "lookback_period": 20,
                    "volume_threshold": 1.5
                }
            }
        ]
    }

@router.get("/presets")
async def get_backtest_presets():
    """
    Retourne des configurations prédéfinies pour les backtests
    """
    return {
        "presets": [
            {
                "name": "ETF Européens Diversifiés",
                "symbols": ["IWDA.AS", "VWCE.DE", "CSPX.L"],
                "strategy": "momentum",
                "description": "Portfolio diversifié d'ETF européens populaires"
            },
            {
                "name": "ETF Sectoriels Tech",
                "symbols": ["IUIT.L", "WTCH.DE"],
                "strategy": "momentum", 
                "description": "Focus sur le secteur technologique"
            },
            {
                "name": "ETF Obligations",
                "symbols": ["IEAG.AS", "AGGH.L"],
                "strategy": "mean_reversion",
                "description": "Portfolio obligataire pour stabilité"
            },
            {
                "name": "Test Rapide",
                "symbols": ["IWDA.AS"],
                "strategy": "momentum",
                "description": "Test simple sur un ETF monde"
            }
        ]
    }

@router.post("/quick-test")
async def quick_backtest(
    symbol: str = Query(..., description="Symbole ETF à tester"),
    strategy: str = Query("momentum", description="Stratégie à utiliser"),
    months: int = Query(6, ge=1, le=24, description="Nombre de mois à tester"),
    current_user: User = Depends(get_current_user)
):
    """
    Lance un backtest rapide sur un ETF
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        engine = BacktestingEngine()
        results = await engine.run_backtest(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            transaction_fee=0.001,
            strategy=strategy
        )
        
        # Simplifier pour réponse rapide
        return {
            "symbol": symbol,
            "strategy": strategy,
            "period_months": months,
            "total_return": results["metrics"]["total_return"],
            "annualized_return": results["metrics"]["annualized_return"],
            "max_drawdown": results["metrics"]["max_drawdown"],
            "sharpe_ratio": results["metrics"]["sharpe_ratio"],
            "total_trades": results["metrics"]["total_trades"],
            "win_rate": results["metrics"]["win_rate"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du test rapide: {str(e)}")

@router.get("/performance-comparison")
async def compare_strategies(
    symbols: str = Query(..., description="Symboles séparés par des virgules"),
    months: int = Query(6, ge=1, le=12, description="Période en mois"),
    current_user: User = Depends(get_current_user)
):
    """
    Compare les performances de différentes stratégies
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        if len(symbol_list) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 symboles autorisés")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        strategies = ["momentum", "mean_reversion", "breakout"]
        results = {}
        
        engine = BacktestingEngine()
        
        for strategy in strategies:
            try:
                backtest_result = await engine.run_backtest(
                    symbols=symbol_list,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=10000.0,
                    transaction_fee=0.001,
                    strategy=strategy
                )
                
                results[strategy] = {
                    "total_return": backtest_result["metrics"]["total_return"],
                    "annualized_return": backtest_result["metrics"]["annualized_return"],
                    "sharpe_ratio": backtest_result["metrics"]["sharpe_ratio"],
                    "max_drawdown": backtest_result["metrics"]["max_drawdown"],
                    "total_trades": backtest_result["metrics"]["total_trades"],
                    "win_rate": backtest_result["metrics"]["win_rate"]
                }
                
            except Exception as e:
                results[strategy] = {"error": str(e)}
        
        return {
            "symbols": symbol_list,
            "period_months": months,
            "comparison": results,
            "best_strategy": max(
                results.keys(), 
                key=lambda k: results[k].get("total_return", -999) if "error" not in results[k] else -999
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")