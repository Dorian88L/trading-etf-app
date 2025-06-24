from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app
import time
import logging

from app.core.config import settings
from app.api.v1.api import api_router
from app.services.simulation_recovery_service import startup_recovery, schedule_periodic_cleanup

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Gestion de l'authentification et des utilisateurs"
        },
        {
            "name": "market",
            "description": "Données de marché temps réel et indices européens"
        },
        {
            "name": "signals",
            "description": "Signaux de trading automatisés"
        },
        {
            "name": "portfolio",
            "description": "Gestion des portfolios et positions"
        },
        {
            "name": "alerts",
            "description": "Système d'alertes et notifications"
        },
        {
            "name": "monitoring",
            "description": "Monitoring système et performance"
        }
    ]
)

# Request timing middleware (production-ready)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log only essential information in production
    if settings.DEBUG:
        print(f"⏱️ {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# CORS configuration using settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRFToken",
        "Cache-Control"
    ],
    expose_headers=[
        "Content-Length",
        "Content-Type", 
        "X-Total-Count",
        "X-Request-ID"
    ]
)

# Add security middleware for local development and production
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost", 
        "127.0.0.1",
        "investeclaire.fr",
        "www.investeclaire.fr",
        "api.investeclaire.fr"
    ]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Startup event for simulation recovery
@app.on_event("startup")
async def startup_event():
    """
    Événement de démarrage pour récupérer les simulations actives et initialiser les données
    """
    logger.info("🚀 Démarrage de l'application Trading ETF API")
    
    try:
        # 1. Initialiser la base de données et les ETFs si nécessaire
        await initialize_database_if_needed()
        
        # 2. Récupérer les simulations actives
        recovery_result = startup_recovery()
        logger.info(f"📊 Récupération des simulations: {recovery_result}")
        
        # 3. Programmer le nettoyage périodique
        schedule_periodic_cleanup()
        
        # 4. Forcer la collecte initiale de données si pas de données récentes
        await trigger_initial_data_collection()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        # Ne pas faire échouer le démarrage de l'API

async def initialize_database_if_needed():
    """
    Initialise la base de données avec les ETFs de base si elle est vide
    """
    try:
        from app.core.database import get_db
        from app.models.etf import ETF
        from sqlalchemy import text
        
        db = next(get_db())
        try:
            # Vérifier si des ETFs existent
            etf_count = db.query(ETF).count()
            logger.info(f"📊 ETFs en base: {etf_count}")
            
            if etf_count == 0:
                logger.info("🏗️ Aucun ETF trouvé - Initialisation des ETFs de base...")
                await populate_base_etfs(db)
            else:
                logger.info(f"✅ {etf_count} ETFs déjà présents en base")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur initialisation DB: {e}")

async def populate_base_etfs(db):
    """
    Peuple la base avec les ETFs européens essentiels
    """
    try:
        from app.models.etf import ETF
        from datetime import datetime
        
        # ETFs européens essentiels
        base_etfs = [
            {
                "isin": "IE00B4L5Y983",
                "name": "iShares Core MSCI World UCITS ETF USD (Acc)",
                "sector": "Global Equity",
                "currency": "USD",
                "ter": 0.20,
                "aum": 20000000000,
                "exchange": "XETRA"
            },
            {
                "isin": "IE00BK5BQT80", 
                "name": "Vanguard FTSE All-World UCITS ETF USD Acc",
                "sector": "Global Equity",
                "currency": "USD", 
                "ter": 0.22,
                "aum": 15000000000,
                "exchange": "XETRA"
            },
            {
                "isin": "IE00B5BMR087",
                "name": "iShares Core S&P 500 UCITS ETF USD Acc",
                "sector": "US Large Cap",
                "currency": "USD",
                "ter": 0.07,
                "aum": 30000000000,
                "exchange": "London"
            },
            {
                "isin": "DE0005933931",
                "name": "iShares Core DAX UCITS ETF",
                "sector": "German Large Cap",
                "currency": "EUR",
                "ter": 0.16,
                "aum": 6000000000,
                "exchange": "XETRA"
            },
            {
                "isin": "IE00B52VJ196",
                "name": "iShares Core EURO STOXX 50 UCITS ETF",
                "sector": "European Large Cap",
                "currency": "EUR",
                "ter": 0.10,
                "aum": 8500000000,
                "exchange": "XETRA"
            }
        ]
        
        created_count = 0
        for etf_data in base_etfs:
            # Vérifier si l'ETF existe déjà
            existing = db.query(ETF).filter(ETF.isin == etf_data["isin"]).first()
            if not existing:
                etf = ETF(
                    isin=etf_data["isin"],
                    name=etf_data["name"],
                    sector=etf_data["sector"],
                    currency=etf_data["currency"],
                    ter=etf_data["ter"],
                    aum=etf_data["aum"],
                    exchange=etf_data["exchange"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(etf)
                created_count += 1
        
        db.commit()
        logger.info(f"✅ {created_count} ETFs de base créés")
        
    except Exception as e:
        logger.error(f"❌ Erreur création ETFs de base: {e}")
        db.rollback()

async def trigger_initial_data_collection():
    """
    Lance la collecte initiale de données si nécessaire
    """
    try:
        from app.core.database import get_db
        from app.models.etf import MarketData
        from datetime import datetime, timedelta
        from app.services.tasks import collect_market_data
        
        db = next(get_db())
        try:
            # Vérifier s'il y a des données récentes (moins de 1h)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            recent_data_count = db.query(MarketData).filter(MarketData.time > cutoff_time).count()
            
            logger.info(f"📊 Données récentes (1h): {recent_data_count}")
            
            if recent_data_count == 0:
                logger.info("🔄 Aucune donnée récente - Lancement de la collecte initiale...")
                # Lancer la tâche de collecte en arrière-plan
                collect_market_data.delay()
                logger.info("✅ Collecte de données lancée en arrière-plan")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Erreur déclenchement collecte: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Événement d'arrêt pour nettoyer les ressources
    """
    logger.info("🛑 Arrêt de l'application Trading ETF API")


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Trading ETF API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8443,
        reload=settings.DEBUG
    )