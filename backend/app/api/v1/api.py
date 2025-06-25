from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, market, signals, portfolio, user, alerts, real_market, 
    advanced_signals, monitoring, etf_selection, notifications, 
    etf_scoring, trading_algorithms, realtime_market, backtesting, 
    websocket, advanced_backtesting, historical_data, optimized_etf_data,
    portfolio_management, user_etf_preferences, watchlist, etf_data_sources,
    simulation_monitoring, trading_simulation
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(real_market.router, prefix="/real-market", tags=["real-market"])
api_router.include_router(optimized_etf_data.router, prefix="/optimized-market", tags=["optimized-market"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(advanced_signals.router, prefix="", tags=["advanced-signals"])  # Pas de préfixe pour garder /signals/advanced
api_router.include_router(etf_selection.router, prefix="/etfs", tags=["etf-selection"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(portfolio_management.router, prefix="/portfolio-management", tags=["portfolio-management"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(etf_scoring.router, prefix="/etf-scoring", tags=["etf-scoring"])
api_router.include_router(historical_data.router, prefix="/historical", tags=["historical-data"])
api_router.include_router(trading_algorithms.router, prefix="/trading-algorithms", tags=["trading-algorithms"])
api_router.include_router(realtime_market.router, prefix="/realtime-market", tags=["realtime-market"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["backtesting"])
api_router.include_router(advanced_backtesting.router, prefix="/advanced-backtesting", tags=["advanced-backtesting"])
api_router.include_router(websocket.router, prefix="/websocket", tags=["websocket"])
api_router.include_router(user_etf_preferences.router, prefix="/user-etf-preferences", tags=["user-etf-preferences"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(etf_data_sources.router, prefix="/etf-data-sources", tags=["etf-data-sources"])
api_router.include_router(simulation_monitoring.router, prefix="/simulation-monitoring", tags=["simulation-monitoring"])
api_router.include_router(trading_simulation.router, prefix="/simulations", tags=["trading-simulation"])