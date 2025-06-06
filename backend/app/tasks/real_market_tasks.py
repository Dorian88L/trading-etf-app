"""
Tâches Celery pour la collecte automatique de données de marché réelles
"""

import logging
from celery import Celery
from datetime import datetime

from app.services.real_market_data import RealMarketDataService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuration Celery
celery_app = Celery(
    "trading_etf_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    beat_schedule={
        # Collecte des données toutes les 5 minutes pendant les heures de marché
        'collect-real-market-data': {
            'task': 'app.tasks.real_market_tasks.collect_real_market_data',
            'schedule': 300.0,  # 5 minutes
        },
        # Mise à jour de la base de données toutes les heures
        'update-database-with-real-data': {
            'task': 'app.tasks.real_market_tasks.update_database_with_real_data',
            'schedule': 3600.0,  # 1 heure
        },
    },
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def collect_real_market_data(self):
    """
    Tâche pour collecter les données de marché réelles
    Exécutée toutes les 5 minutes
    """
    try:
        logger.info("Début de la collecte des données de marché réelles")
        
        # Vérifier si c'est pendant les heures de marché
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0 = lundi, 6 = dimanche
        
        # Marchés européens généralement ouverts de 9h à 17h30, lundi à vendredi
        if weekday >= 5 or hour < 9 or hour >= 18:
            logger.info("Marché fermé, saut de la collecte")
            return {"status": "skipped", "reason": "market_closed", "timestamp": now.isoformat()}
        
        market_service = RealMarketDataService()
        
        # Collecter les données des ETFs
        etf_data_count = 0
        for symbol in market_service.EUROPEAN_ETFS.keys():
            try:
                data = market_service.get_real_etf_data(symbol)
                if data:
                    etf_data_count += 1
                    logger.info(f"Données collectées pour {symbol}: {data.current_price} {data.currency}")
            except Exception as e:
                logger.error(f"Erreur pour {symbol}: {e}")
                continue
        
        # Collecter les données des indices
        indices_data = market_service.get_market_indices()
        indices_count = len(indices_data)
        
        result = {
            "status": "success",
            "etfs_collected": etf_data_count,
            "indices_collected": indices_count,
            "timestamp": now.isoformat()
        }
        
        logger.info(f"Collecte terminée: {etf_data_count} ETFs, {indices_count} indices")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la collecte des données: {exc}")
        
        # Retry avec backoff exponentiel
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
        
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def update_database_with_real_data(self):
    """
    Tâche pour mettre à jour la base de données avec les données réelles
    Exécutée toutes les heures
    """
    try:
        logger.info("Début de la mise à jour de la base de données")
        
        market_service = RealMarketDataService()
        
        # Exécuter la mise à jour de manière asynchrone
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(market_service.update_database_with_real_data())
        finally:
            loop.close()
        
        result = {
            "status": "success", 
            "message": "Base de données mise à jour avec succès",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Mise à jour de la base de données terminée")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour de la base de données: {exc}")
        
        # Retry avec délai
        raise self.retry(exc=exc, countdown=300)  # Retry après 5 minutes

@celery_app.task
def get_real_etf_price(symbol: str):
    """
    Tâche pour récupérer le prix d'un ETF spécifique
    Utile pour les mises à jour à la demande
    """
    try:
        market_service = RealMarketDataService()
        data = market_service.get_real_etf_data(symbol)
        
        if data:
            return {
                "status": "success",
                "symbol": symbol,
                "price": data.current_price,
                "change": data.change,
                "change_percent": data.change_percent,
                "volume": data.volume,
                "timestamp": data.last_update.isoformat()
            }
        else:
            return {
                "status": "error",
                "symbol": symbol,
                "message": "Aucune donnée trouvée"
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du prix pour {symbol}: {e}")
        return {
            "status": "error",
            "symbol": symbol,
            "message": str(e)
        }

@celery_app.task
def monitor_etf_alerts(etf_isin: str, target_price: float, alert_type: str):
    """
    Tâche pour surveiller les alertes de prix ETF
    alert_type: 'above' ou 'below'
    """
    try:
        market_service = RealMarketDataService()
        
        # Trouver le symbole par ISIN
        symbol = None
        for sym, info in market_service.EUROPEAN_ETFS.items():
            if info['isin'] == etf_isin:
                symbol = sym
                break
        
        if not symbol:
            return {"status": "error", "message": f"ETF avec ISIN {etf_isin} non trouvé"}
        
        data = market_service.get_real_etf_data(symbol)
        
        if data:
            current_price = data.current_price
            alert_triggered = False
            
            if alert_type == 'above' and current_price >= target_price:
                alert_triggered = True
            elif alert_type == 'below' and current_price <= target_price:
                alert_triggered = True
            
            return {
                "status": "success",
                "etf_isin": etf_isin,
                "symbol": symbol,
                "current_price": current_price,
                "target_price": target_price,
                "alert_type": alert_type,
                "alert_triggered": alert_triggered,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"status": "error", "message": "Impossible de récupérer les données"}
            
    except Exception as e:
        logger.error(f"Erreur lors de la surveillance des alertes pour {etf_isin}: {e}")
        return {"status": "error", "message": str(e)}

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)