"""
Application FastAPI sécurisée pour la production
"""
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import logging

# Import des configurations selon l'environnement
if os.getenv("ENVIRONMENT") == "production":
    from app.core.config_production import get_production_settings
    from app.core.security_middleware import SecurityMiddleware
    settings = get_production_settings()
else:
    from app.core.config import settings

from app.api.v1.api import api_router

# Configuration du logging pour la production
if settings.ENVIRONMENT == "production":
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.WARNING),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./logs/app.log'),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Créer l'application FastAPI avec configuration sécurisée
app_config = {
    "title": settings.PROJECT_NAME,
    "version": settings.VERSION,
    "openapi_url": f"{settings.API_V1_STR}/openapi.json" if not settings.ENVIRONMENT == "production" else None,
    "docs_url": "/docs" if not settings.ENVIRONMENT == "production" else None,
    "redoc_url": "/redoc" if not settings.ENVIRONMENT == "production" else None,
}

# En production, désactiver la documentation automatique
if settings.ENVIRONMENT == "production":
    app_config.update({
        "openapi_url": None,
        "docs_url": None,
        "redoc_url": None
    })

app = FastAPI(**app_config)

# Middleware de sécurité pour la production
if settings.ENVIRONMENT == "production":
    app.add_middleware(SecurityMiddleware, settings=settings)

# Trusted Host Middleware
if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
    allowed_hosts = [host.strip() for host in settings.ALLOWED_HOSTS.split(",")]
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=allowed_hosts
    )

# CORS Middleware avec configuration stricte
cors_origins = settings.BACKEND_CORS_ORIGINS if hasattr(settings, 'BACKEND_CORS_ORIGINS') else [
    "http://localhost:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400 if settings.ENVIRONMENT == "production" else 600
)

# Health check endpoint (toujours disponible)
@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }

# Endpoint de monitoring pour Prometheus (en production)
if settings.ENVIRONMENT == "production":
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Routes principales
app.include_router(api_router, prefix=settings.API_V1_STR)

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreurs global pour la production"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    
    if settings.ENVIRONMENT == "production":
        # En production, ne pas exposer les détails de l'erreur
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        # En développement, afficher l'erreur
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Événements au démarrage"""
    logger.info(f"🚀 Démarrage de l'application Trading ETF en mode {settings.ENVIRONMENT}")
    
    if settings.ENVIRONMENT == "production":
        logger.info("🔒 Sécurité activée : middleware, CORS strict, logs configurés")

@app.on_event("shutdown")
async def shutdown_event():
    """Événements à l'arrêt"""
    logger.info("⏹️ Arrêt de l'application Trading ETF")

# Root endpoint
@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Trading ETF API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else "Disabled in production",
        "health_check": "/health"
    }