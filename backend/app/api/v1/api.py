from fastapi import APIRouter
from app.api.v1.endpoints import auth, market, signals, portfolio, user, alerts, real_market

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(real_market.router, prefix="/real-market", tags=["real-market"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])