from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app
import time

from app.core.config import settings
from app.api.v1.api import api_router

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