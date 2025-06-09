"""
Endpoints pour les algorithmes de trading avancés
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.trading_algorithms import TradingAlgorithms, StrategyType, SignalType
from app.schemas.signal import TradingSignalResponse

router = APIRouter()

@router.get("/signals/advanced/{etf_isin}", response_model=List[TradingSignalResponse])
async def get_advanced_signals(
    etf_isin: str,
    strategies: Optional[str] = Query(None, description="Stratégies séparées par des virgules"),
    min_confidence: float = Query(60, ge=0, le=100),
    max_risk: float = Query(70, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère des signaux de trading avancés pour un ETF spécifique
    """
    try:
        algorithms = TradingAlgorithms()
        algorithms.min_confidence = min_confidence
        algorithms.max_risk_score = max_risk
        
        # Génération de données mockées pour démo
        market_data = _generate_mock_market_data(etf_isin)
        
        # Filtrage des stratégies
        selected_strategies = []
        if strategies:
            strategy_names = [s.strip().upper() for s in strategies.split(',')]
            for strategy_name in strategy_names:
                try:
                    selected_strategies.append(StrategyType[strategy_name])
                except KeyError:
                    pass
        
        # Génération des signaux
        all_signals = await algorithms.generate_all_signals(market_data, etf_isin)
        
        # Filtrage par stratégies si spécifié
        if selected_strategies:
            all_signals = [s for s in all_signals if s.strategy in selected_strategies]
        
        # Conversion en réponse
        response_signals = []
        for signal in all_signals:
            response_signals.append(TradingSignalResponse(
                id=f"adv_{signal.etf_isin}_{signal.strategy.value}_{int(signal.generated_at.timestamp())}",
                etf_isin=signal.etf_isin,
                signal_type=signal.signal_type.value,
                strategy=signal.strategy.value,
                confidence=signal.confidence,
                entry_price=signal.entry_price,
                target_price=signal.target_price,
                stop_loss=signal.stop_loss,
                expected_return=signal.expected_return,
                risk_score=signal.risk_score,
                timeframe=signal.timeframe,
                reasons=signal.reasons,
                technical_score=signal.technical_score,
                generated_at=signal.generated_at,
                is_active=True,
                expires_at=signal.generated_at + timedelta(days=7)
            ))
        
        return response_signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/portfolio", response_model=List[TradingSignalResponse])
async def get_portfolio_signals(
    etf_isins: str = Query(..., description="ISINs séparés par des virgules"),
    max_signals: int = Query(5, ge=1, le=10),
    min_confidence: float = Query(70, ge=0, le=100),
    diversify: bool = Query(True, description="Diversifier par stratégie"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère des signaux optimisés pour un portefeuille d'ETF
    """
    try:
        algorithms = TradingAlgorithms()
        algorithms.min_confidence = min_confidence
        
        isin_list = [isin.strip() for isin in etf_isins.split(',')]
        if len(isin_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 ETF autorisés")
        
        all_portfolio_signals = []
        etf_data = {}
        
        # Génération des données et signaux pour chaque ETF
        for etf_isin in isin_list:
            market_data = _generate_mock_market_data(etf_isin)
            etf_data[etf_isin] = market_data
            
            signals = await algorithms.generate_all_signals(
                market_data, 
                etf_isin, 
                related_etfs=etf_data if len(etf_data) > 1 else None
            )
            all_portfolio_signals.extend(signals)
        
        # Optimisation du portefeuille
        if diversify:
            optimized_signals = algorithms.get_portfolio_signals(all_portfolio_signals)
        else:
            # Tri par confiance et sélection des meilleurs
            all_portfolio_signals.sort(key=lambda x: x.confidence, reverse=True)
            optimized_signals = all_portfolio_signals[:max_signals]
        
        # Filtrage par risque
        final_signals = algorithms.filter_signals_by_risk(optimized_signals)[:max_signals]
        
        # Conversion en réponse
        response_signals = []
        for signal in final_signals:
            response_signals.append(TradingSignalResponse(
                id=f"port_{signal.etf_isin}_{signal.strategy.value}_{int(signal.generated_at.timestamp())}",
                etf_isin=signal.etf_isin,
                signal_type=signal.signal_type.value,
                strategy=signal.strategy.value,
                confidence=signal.confidence,
                entry_price=signal.entry_price,
                target_price=signal.target_price,
                stop_loss=signal.stop_loss,
                expected_return=signal.expected_return,
                risk_score=signal.risk_score,
                timeframe=signal.timeframe,
                reasons=signal.reasons,
                technical_score=signal.technical_score,
                generated_at=signal.generated_at,
                is_active=True,
                expires_at=signal.generated_at + timedelta(days=7)
            ))
        
        return response_signals
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/performance")
async def get_strategy_performance(
    days_back: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyse de performance des différentes stratégies
    """
    try:
        # Simulation des performances des stratégies
        strategies_performance = {
            'BREAKOUT': {
                'total_signals': 45,
                'successful_signals': 28,
                'success_rate': 62.2,
                'average_return': 4.3,
                'max_return': 12.1,
                'min_return': -3.2,
                'average_holding_days': 5.2,
                'risk_adjusted_return': 2.1
            },
            'MEAN_REVERSION': {
                'total_signals': 52,
                'successful_signals': 35,
                'success_rate': 67.3,
                'average_return': 3.1,
                'max_return': 8.4,
                'min_return': -2.8,
                'average_holding_days': 8.1,
                'risk_adjusted_return': 2.4
            },
            'MOMENTUM': {
                'total_signals': 38,
                'successful_signals': 22,
                'success_rate': 57.9,
                'average_return': 5.7,
                'max_return': 15.3,
                'min_return': -4.1,
                'average_holding_days': 7.8,
                'risk_adjusted_return': 1.9
            },
            'STATISTICAL_ARBITRAGE': {
                'total_signals': 31,
                'successful_signals': 23,
                'success_rate': 74.2,
                'average_return': 2.8,
                'max_return': 6.1,
                'min_return': -1.9,
                'average_holding_days': 12.3,
                'risk_adjusted_return': 2.7
            }
        }
        
        # Calcul des métriques globales
        total_signals = sum(data['total_signals'] for data in strategies_performance.values())
        total_successful = sum(data['successful_signals'] for data in strategies_performance.values())
        overall_success_rate = (total_successful / total_signals) * 100 if total_signals > 0 else 0
        
        # Classement des stratégies
        ranked_strategies = sorted(
            strategies_performance.items(),
            key=lambda x: x[1]['risk_adjusted_return'],
            reverse=True
        )
        
        return {
            'status': 'success',
            'data': {
                'period_analyzed': f"{days_back} derniers jours",
                'overall_metrics': {
                    'total_signals': total_signals,
                    'successful_signals': total_successful,
                    'overall_success_rate': round(overall_success_rate, 1),
                    'best_strategy': ranked_strategies[0][0] if ranked_strategies else None,
                    'most_active_strategy': max(strategies_performance.items(), key=lambda x: x[1]['total_signals'])[0]
                },
                'strategies_performance': strategies_performance,
                'strategy_ranking': [
                    {
                        'strategy': strategy,
                        'rank': i + 1,
                        'score': data['risk_adjusted_return']
                    }
                    for i, (strategy, data) in enumerate(ranked_strategies)
                ],
                'generated_at': datetime.utcnow()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{strategy}")
async def backtest_strategy(
    strategy: str,
    etf_isin: str,
    start_date: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    initial_capital: float = Query(10000, ge=1000, le=1000000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Backtest d'une stratégie spécifique
    """
    try:
        # Validation de la stratégie
        try:
            strategy_type = StrategyType[strategy.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Stratégie inconnue: {strategy}")
        
        # Dates par défaut
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Simulation des résultats de backtest
        backtest_results = {
            'strategy': strategy_type.value,
            'etf_isin': etf_isin,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'trading_days': 126
            },
            'capital': {
                'initial': initial_capital,
                'final': initial_capital * 1.124,  # 12.4% de performance
                'max_drawdown': initial_capital * 0.058,  # 5.8% de drawdown max
                'total_return': 12.4,
                'annualized_return': 24.8,
                'sharpe_ratio': 1.83,
                'sortino_ratio': 2.41,
                'calmar_ratio': 4.28
            },
            'trades': {
                'total_trades': 23,
                'winning_trades': 15,
                'losing_trades': 8,
                'win_rate': 65.2,
                'average_win': 3.2,
                'average_loss': -1.8,
                'largest_win': 8.7,
                'largest_loss': -3.4,
                'profit_factor': 2.67
            },
            'monthly_returns': [
                {'month': '2024-01', 'return': 2.1},
                {'month': '2024-02', 'return': -0.8},
                {'month': '2024-03', 'return': 3.4},
                {'month': '2024-04', 'return': 1.2},
                {'month': '2024-05', 'return': 4.1},
                {'month': '2024-06', 'return': 2.4}
            ],
            'signals_generated': {
                'total': 23,
                'buy_signals': 12,
                'sell_signals': 11,
                'average_confidence': 73.2,
                'signals_executed': 23,
                'signals_missed': 0
            },
            'risk_metrics': {
                'volatility': 12.3,
                'var_95': 2.1,
                'expected_shortfall': 3.2,
                'maximum_drawdown_duration': 18,  # jours
                'recovery_time': 32  # jours
            }
        }
        
        return {
            'status': 'success',
            'data': backtest_results,
            'generated_at': datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _generate_mock_market_data(etf_isin: str, days: int = 100) -> pd.DataFrame:
    """
    Génère des données de marché mockées pour les tests
    """
    import numpy as np
    
    # Seed basé sur l'ISIN pour reproduire les mêmes données
    np.random.seed(hash(etf_isin) % 2**32)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Prix de base
    base_price = 100 + hash(etf_isin) % 100
    
    # Simulation d'une marche aléatoire avec tendance
    returns = np.random.normal(0.001, 0.02, days)  # 0.1% de rendement moyen, 2% de volatilité
    
    # Ajout de quelques tendances et patterns
    trend = np.sin(np.arange(days) / 20) * 0.005  # Tendance cyclique
    returns += trend
    
    # Calcul des prix
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Génération OHLC
    closes = np.array(prices)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.01, days)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.01, days)))
    opens = np.roll(closes, 1)
    opens[0] = closes[0]
    
    volumes = np.random.normal(1000000, 200000, days)
    volumes = np.maximum(volumes, 100000)  # Volume minimum
    
    return pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes.astype(int)
    }).set_index('date')