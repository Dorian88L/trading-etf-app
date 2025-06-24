from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Trading ETF API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = """
    **Application de Trading ETF avec Signaux Temps Réel**
    
    Cette API fournit des données de marché temps réel pour les ETFs européens, 
    des signaux de trading automatisés et une gestion complète de portfolio.
    
    ## Fonctionnalités principales :
    
    * 📊 **Données temps réel** : Prix et variations des ETFs européens (IWDA, VWCE, CSPX, etc.)
    * 🎯 **Signaux intelligents** : Algorithmes d'analyse technique pour BUY/SELL/HOLD/WAIT
    * 💼 **Gestion portfolio** : Suivi des positions, P&L et performance
    * 🚨 **Alertes** : Notifications sur mouvements significatifs
    * 📈 **Indices européens** : CAC 40, DAX, FTSE 100, EURO STOXX 50
    * 🔍 **Monitoring** : Surveillance système et cache intelligent
    
    ## Sources de données :
    
    * Yahoo Finance (principal)
    * TwelveData, EODHD, Finnhub (prioritaires)
    * Alpha Vantage, FMP, Marketstack (fallback)
    * Cache intelligent pour performance optimale
    
    ## Authentification :
    
    Certains endpoints nécessitent une authentification JWT. 
    Utilisez `/auth/login` pour obtenir un token d'accès.
    """
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Security - Configuration renforcée
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))
    
    # Validation de la clé secrète
    def __post_init__(self):
        if not self.SECRET_KEY:
            raise ValueError(
                "🚨 ERREUR SÉCURITÉ: JWT_SECRET_KEY manquante!\n"
                "Générez une clé forte: openssl rand -hex 32\n"
                "Puis: export JWT_SECRET_KEY=your_generated_key"
            )
        # En développement, permettre la clé par défaut avec un avertissement
        if self.SECRET_KEY == "your-secret-key-change-in-production" and self.ENVIRONMENT == "production":
            raise ValueError(
                "🚨 ERREUR SÉCURITÉ: JWT_SECRET_KEY par défaut en production!\n"
                "Générez une clé forte: openssl rand -hex 32"
            )
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://trading_user:trading_password@localhost:5432/trading_etf"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Celery
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # CORS - Production et développement
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:80",
        "http://localhost:3000",
        "http://127.0.0.1:80", 
        "http://127.0.0.1:3000",
        "http://investeclaire.fr",
        "http://www.investeclaire.fr",
        "https://investeclaire.fr",
        "https://www.investeclaire.fr",
        "https://api.investeclaire.fr"
    ]
    
    # Allowed hosts for Host header validation
    @property
    def ALLOWED_HOSTS(self) -> Optional[list[str]]:
        hosts_env = os.getenv("ALLOWED_HOSTS")
        if hosts_env:
            return [host.strip() for host in hosts_env.split(",")]
        return None
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    YAHOO_FINANCE_API_KEY: Optional[str] = os.getenv("YAHOO_FINANCE_API_KEY")
    FINANCIAL_MODELING_PREP_API_KEY: Optional[str] = os.getenv("FINANCIAL_MODELING_PREP_API_KEY", "demo")
    
    # Alternative data sources
    EODHD_API_KEY: Optional[str] = os.getenv("EODHD_API_KEY")
    FINNHUB_API_KEY: Optional[str] = os.getenv("FINNHUB_API_KEY")
    MARKETSTACK_API_KEY: Optional[str] = os.getenv("MARKETSTACK_API_KEY")
    TWELVEDATA_API_KEY: Optional[str] = os.getenv("TWELVEDATA_API_KEY")
    
    # Push Notifications (VAPID)
    VAPID_PRIVATE_KEY: Optional[str] = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_PUBLIC_KEY: Optional[str] = os.getenv("VAPID_PUBLIC_KEY")
    VAPID_EMAIL: str = os.getenv("VAPID_EMAIL", "admin@trading-etf.com")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Cache Settings
    CACHE_TTL_MARKET_DATA: int = 300  # 5 minutes
    CACHE_TTL_STATIC_DATA: int = 3600  # 1 hour
    CACHE_TTL_USER_SESSION: int = 86400  # 24 hours
    CACHE_TTL_SIGNALS: int = 900  # 15 minutes
    
    # Market Data Settings
    MARKET_DATA_UPDATE_INTERVAL: int = 300  # 5 minutes
    TECHNICAL_INDICATORS_UPDATE_INTERVAL: int = 900  # 15 minutes
    SIGNALS_UPDATE_INTERVAL: int = 1800  # 30 minutes
    
    # Risk Management
    MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio
    DEFAULT_STOP_LOSS_PCT: float = 0.05  # 5%
    MIN_SIGNAL_CONFIDENCE: float = 60.0
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()