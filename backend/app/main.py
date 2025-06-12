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

# Middleware de debugging pour voir toutes les requêtes
@app.middleware("http")
async def debug_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log de la requête entrante
    print(f"🔧 DEBUG REQUEST: {request.method} {request.url}")
    print(f"🔧 DEBUG HEADERS: {dict(request.headers)}")
    print(f"🔧 DEBUG CLIENT: {request.client}")
    
    response = await call_next(request)
    
    # Log de la réponse
    process_time = time.time() - start_time
    print(f"🔧 DEBUG RESPONSE: {response.status_code} - {process_time:.4f}s")
    print(f"🔧 DEBUG RESPONSE HEADERS: {dict(response.headers)}")
    
    return response

# Add CORS middleware - Configuration pour développement local
origins = [
    "http://localhost:80",
    "http://localhost:3000",
    "http://127.0.0.1:80",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add security middleware for local development
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost", 
        "127.0.0.1"
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