from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Trading ETF API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "ETF Trading Application with Real-time Signals"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
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
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000"
    ]
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    YAHOO_FINANCE_API_KEY: Optional[str] = os.getenv("YAHOO_FINANCE_API_KEY")
    
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


settings = Settings()