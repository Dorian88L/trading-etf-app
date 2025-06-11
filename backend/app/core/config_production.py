"""
Configuration sécurisée pour la production
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import secrets


class ProductionSettings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Trading ETF API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Security - OBLIGATOIRE: Utiliser des valeurs sécurisées
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1  # Réduire en production
    
    # Database - Credentials sécurisés obligatoires
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Redis - Avec mot de passe obligatoire
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "")
    
    # CORS - Strictement configuré pour la production
    BACKEND_CORS_ORIGINS: List[str] = []
    ALLOWED_HOSTS: Optional[List[str]] = None
    
    # External APIs - Vraies clés requises
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    YAHOO_FINANCE_API_KEY: Optional[str] = os.getenv("YAHOO_FINANCE_API_KEY")
    FINANCIAL_MODELING_PREP_API_KEY: Optional[str] = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    
    # Push Notifications (VAPID) - Clés obligatoires
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_EMAIL: str = os.getenv("VAPID_EMAIL", "")
    
    # Security Headers
    SECURE_SSL_REDIRECT: bool = True
    SECURE_HSTS_SECONDS: int = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True
    SECURE_BROWSER_XSS_FILTER: bool = True
    
    # Rate Limiting - Plus strict en production
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "50"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Cache Settings - TTL plus courts en production
    CACHE_TTL_MARKET_DATA: int = 180  # 3 minutes
    CACHE_TTL_STATIC_DATA: int = 1800  # 30 minutes
    CACHE_TTL_USER_SESSION: int = 3600  # 1 heure
    CACHE_TTL_SIGNALS: int = 600  # 10 minutes
    
    # Market Data Settings
    MARKET_DATA_UPDATE_INTERVAL: int = 180  # 3 minutes
    TECHNICAL_INDICATORS_UPDATE_INTERVAL: int = 600  # 10 minutes
    SIGNALS_UPDATE_INTERVAL: int = 900  # 15 minutes
    
    # Risk Management
    MAX_POSITION_SIZE: float = 0.05  # 5% max en production
    DEFAULT_STOP_LOSS_PCT: float = 0.03  # 3% stop-loss
    MIN_SIGNAL_CONFIDENCE: float = 75.0  # Plus strict
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validation des variables critiques
        self._validate_critical_settings()
        
        # Configuration CORS depuis les variables d'environnement
        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if cors_origins:
            self.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
        
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
        if allowed_hosts:
            self.ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(",")]
        else:
            self.ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    
    def _validate_critical_settings(self):
        """Valide que toutes les variables critiques sont configurées"""
        critical_vars = [
            ("SECRET_KEY", self.SECRET_KEY),
            ("DATABASE_URL", self.DATABASE_URL),
            ("REDIS_URL", self.REDIS_URL),
        ]
        
        missing_vars = []
        weak_keys = []
        
        for var_name, var_value in critical_vars:
            if not var_value:
                missing_vars.append(var_name)
            elif var_name == "SECRET_KEY" and (
                len(var_value) < 32 or 
                var_value in ["your-secret-key-change-in-production", "dev-key", "test"]
            ):
                weak_keys.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Variables d'environnement critiques manquantes: {', '.join(missing_vars)}")
        
        if weak_keys:
            raise ValueError(f"Clés faibles détectées (doivent être générées aléatoirement): {', '.join(weak_keys)}")
    
    class Config:
        case_sensitive = True
        env_file = ".env.production"
        extra = "ignore"


# Pour la production, utiliser cette configuration
def get_production_settings() -> ProductionSettings:
    return ProductionSettings()