from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "trading_etf",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.services.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    # Collect real-time market data every 5 minutes
    "collect-market-data": {
        "task": "app.services.tasks.collect_market_data",
        "schedule": settings.MARKET_DATA_UPDATE_INTERVAL,
    },
    # Update technical indicators every 15 minutes
    "update-technical-indicators": {
        "task": "app.services.tasks.update_technical_indicators",
        "schedule": settings.TECHNICAL_INDICATORS_UPDATE_INTERVAL,
    },
    # Generate signals every 30 minutes
    "generate-signals": {
        "task": "app.services.tasks.generate_trading_signals",
        "schedule": settings.SIGNALS_UPDATE_INTERVAL,
    },
    # Clean up expired signals daily
    "cleanup-expired-signals": {
        "task": "app.services.tasks.cleanup_expired_signals",
        "schedule": 86400,  # Daily
    },
}