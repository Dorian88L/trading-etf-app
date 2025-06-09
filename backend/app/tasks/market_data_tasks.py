"""
Tâches Celery pour la collecte de données de marché en temps réel
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Celery
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.external_apis import external_api_service
from app.services.etf_catalog import get_etf_catalog_service
from app.services.technical_analysis import TechnicalAnalyzer, SignalGenerator
from app.services.signal_generator import get_signal_generator_service
from app.models.etf import ETF, ETFData
from app.models.signal import Signal, SignalType
from app.models.user_preferences import UserSignalSubscription
from app.models.notification import PushSubscription
from app.services.notification_service import notification_service
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="collect_market_data")
def collect_market_data_task():
    """
    Tâche principale de collecte des données de marché
    Exécutée toutes les 5 minutes pendant les heures de marché
    """
    try:
        logger.info("Début de la collecte des données de marché")
        
        # Récupérer la liste des ETFs à surveiller
        catalog_service = get_etf_catalog_service()
        etfs = catalog_service.get_all_etfs()
        
        # Limiter aux ETFs les plus populaires pour éviter les surcharges API
        popular_etfs = sorted(etfs, key=lambda x: x.aum, reverse=True)[:50]
        
        # Collecter les données en parallèle
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            symbols = [etf.symbol for etf in popular_etfs]
            market_data = loop.run_until_complete(
                external_api_service.get_multiple_etfs(symbols)
            )
            
            # Sauvegarder en base de données
            with SessionLocal() as db:
                save_market_data_to_db(db, market_data)
                
            logger.info(f"Collecte réussie pour {len(market_data)} ETFs")
            
            # Déclencher l'analyse technique et génération de signaux
            analyze_technical_indicators_task.delay()
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des données de marché: {e}")
        raise

@celery_app.task(name="analyze_technical_indicators")
def analyze_technical_indicators_task():
    """
    Analyse les indicateurs techniques et génère des signaux
    """
    try:
        logger.info("Début de l'analyse technique")
        
        with SessionLocal() as db:
            # Récupérer les ETFs avec des données récentes
            recent_data = db.query(ETFData).filter(
                ETFData.timestamp >= datetime.now() - timedelta(hours=1)
            ).all()
            
            # Grouper par ETF
            etf_groups = {}
            for data in recent_data:
                if data.isin not in etf_groups:
                    etf_groups[data.isin] = []
                etf_groups[data.isin].append(data)
            
            signal_generator = get_signal_generator_service()
            
            for isin, data_points in etf_groups.items():
                try:
                    # Convertir en DataFrame pour l'analyse
                    df_data = []
                    for point in sorted(data_points, key=lambda x: x.timestamp):
                        df_data.append({
                            'date': point.timestamp,
                            'open': point.open_price,
                            'high': point.high_price,
                            'low': point.low_price,
                            'close': point.close_price,
                            'volume': point.volume
                        })
                    
                    if len(df_data) >= 20:  # Minimum de données pour l'analyse
                        import pandas as pd
                        df = pd.DataFrame(df_data)
                        
                        # Générer un signal
                        etf_symbol = data_points[0].symbol if data_points else isin
                        signal = signal_generator.generate_signal(df, isin, etf_symbol)
                        
                        if signal:
                            save_signal_to_db(db, signal)
                            
                            # Notifier les utilisateurs abonnés
                            notify_subscribed_users_task.delay(signal.etf_isin, signal.signal_type.value, signal.confidence, signal.id)
                            
                except Exception as e:
                    logger.error(f"Erreur analyse technique pour {isin}: {e}")
                    continue
            
            logger.info("Analyse technique terminée")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse technique: {e}")
        raise

@celery_app.task(name="update_market_indices")
def update_market_indices_task():
    """
    Met à jour les indices de marché européens
    """
    try:
        logger.info("Mise à jour des indices de marché")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            indices_data = loop.run_until_complete(
                external_api_service.get_market_indices()
            )
            
            with SessionLocal() as db:
                # Sauvegarder les données des indices
                for index_name, data in indices_data.items():
                    if data:
                        save_index_data_to_db(db, index_name, data)
                        
            logger.info(f"Indices mis à jour: {list(indices_data.keys())}")
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur mise à jour indices: {e}")
        raise

@celery_app.task(name="notify_subscribed_users")
def notify_subscribed_users_task(etf_isin: str, signal_type: str, confidence: float, signal_id: int):
    """
    Notifie les utilisateurs abonnés aux signaux d'un ETF
    """
    try:
        with SessionLocal() as db:
            # Récupérer les abonnements actifs pour cet ETF
            subscriptions = db.query(UserSignalSubscription).filter(
                UserSignalSubscription.etf_isin == etf_isin,
                UserSignalSubscription.is_active == True,
                UserSignalSubscription.min_confidence <= confidence
            ).all()
            
            # Récupérer le signal complet
            signal = db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                logger.error(f"Signal {signal_id} non trouvé")
                return
            
            # Récupérer le nom de l'ETF
            from app.services.etf_catalog import get_etf_catalog_service
            catalog_service = get_etf_catalog_service()
            etf_info = catalog_service.get_etf_by_isin(etf_isin)
            etf_name = etf_info.name if etf_info else etf_isin
            
            notification_count = 0
            
            for subscription in subscriptions:
                # Vérifier si le type de signal correspond aux préférences
                if signal_type in subscription.signal_types:
                    try:
                        # Envoyer la notification push
                        asyncio.run(notification_service.send_signal_notification(
                            user_id=subscription.user_id,
                            signal=signal,
                            etf_name=etf_name,
                            db=db
                        ))
                        notification_count += 1
                        logger.info(f"Notification signal envoyée à user {subscription.user_id} pour {etf_isin}: {signal_type}")
                        
                    except Exception as e:
                        logger.error(f"Erreur notification user {subscription.user_id}: {e}")
                        continue
            
            logger.info(f"Notifications envoyées: {notification_count}/{len(subscriptions)} pour signal {signal_id}")
            
    except Exception as e:
        logger.error(f"Erreur notification utilisateurs: {e}")

@celery_app.task(name="check_price_alerts")
def check_price_alerts_task():
    """
    Vérifie les alertes de prix personnalisées des utilisateurs
    """
    try:
        logger.info("Vérification des alertes de prix")
        
        with SessionLocal() as db:
            from app.models.user_preferences import UserAlert
            from app.services.external_apis import external_api_service
            
            # Récupérer toutes les alertes actives non déclenchées
            active_alerts = db.query(UserAlert).filter(
                UserAlert.is_active == True,
                UserAlert.is_triggered == False
            ).all()
            
            triggered_count = 0
            
            for alert in active_alerts:
                try:
                    # Récupérer le prix actuel
                    from app.services.etf_catalog import get_etf_catalog_service
                    catalog_service = get_etf_catalog_service()
                    etf_info = catalog_service.get_etf_by_isin(alert.etf_isin)
                    
                    if not etf_info:
                        continue
                    
                    # Récupérer le prix via l'API externe
                    market_data = asyncio.run(external_api_service.get_etf_data(etf_info.symbol))
                    
                    if not market_data or not market_data.get('price'):
                        continue
                    
                    current_price = market_data['price']
                    alert.current_value = current_price
                    
                    # Vérifier si l'alerte doit se déclencher
                    should_trigger = False
                    
                    if alert.condition_type == 'above' and current_price >= alert.target_value:
                        should_trigger = True
                    elif alert.condition_type == 'below' and current_price <= alert.target_value:
                        should_trigger = True
                    elif alert.condition_type == 'equals' and abs(current_price - alert.target_value) < 0.01:
                        should_trigger = True
                    
                    if should_trigger:
                        # Marquer comme déclenchée
                        alert.is_triggered = True
                        alert.triggered_at = datetime.now()
                        
                        if alert.trigger_once:
                            alert.is_active = False
                        
                        # Envoyer la notification
                        asyncio.run(notification_service.send_price_alert_notification(
                            user_id=alert.user_id,
                            etf_symbol=alert.etf_symbol,
                            current_price=current_price,
                            target_price=alert.target_value,
                            alert_type=alert.alert_type,
                            db=db
                        ))
                        
                        triggered_count += 1
                        logger.info(f"Alerte déclenchée pour user {alert.user_id}: {alert.etf_symbol} {current_price}")
                        
                except Exception as e:
                    logger.error(f"Erreur vérification alerte {alert.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Vérification alertes terminée: {triggered_count} alertes déclenchées")
            
    except Exception as e:
        logger.error(f"Erreur vérification alertes de prix: {e}")
        raise

@celery_app.task(name="cleanup_old_data")
def cleanup_old_data_task():
    """
    Nettoie les anciennes données pour optimiser la base de données
    """
    try:
        logger.info("Nettoyage des anciennes données")
        
        with SessionLocal() as db:
            from app.models.notification import NotificationHistory
            
            # Supprimer les données de marché de plus de 30 jours
            cutoff_date = datetime.now() - timedelta(days=30)
            
            deleted_count = db.query(ETFData).filter(
                ETFData.timestamp < cutoff_date
            ).delete()
            
            # Supprimer les anciens signaux (plus de 7 jours)
            signal_cutoff = datetime.now() - timedelta(days=7)
            deleted_signals = db.query(Signal).filter(
                Signal.timestamp < signal_cutoff
            ).delete()
            
            # Supprimer l'historique des notifications (plus de 30 jours)
            deleted_notifications = db.query(NotificationHistory).filter(
                NotificationHistory.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Nettoyage terminé: {deleted_count} données marché, {deleted_signals} signaux, {deleted_notifications} notifications supprimés")
            
    except Exception as e:
        logger.error(f"Erreur nettoyage données: {e}")
        raise

def save_market_data_to_db(db: Session, market_data: Dict[str, Any]):
    """Sauvegarde les données de marché en base"""
    for symbol, data in market_data.items():
        if data and data.get('price'):
            try:
                # Récupérer l'ETF correspondant
                etf = db.query(ETF).filter(ETF.symbol == symbol).first()
                
                if etf:
                    # Créer une nouvelle entrée de données
                    etf_data = ETFData(
                        etf_id=etf.id,
                        isin=etf.isin,
                        symbol=symbol,
                        open_price=data.get('open', data['price']),
                        high_price=data.get('high', data['price']),
                        low_price=data.get('low', data['price']),
                        close_price=data['price'],
                        volume=data.get('volume', 0),
                        timestamp=datetime.now()
                    )
                    
                    db.add(etf_data)
                    
            except Exception as e:
                logger.error(f"Erreur sauvegarde données {symbol}: {e}")
                continue
    
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Erreur commit données de marché: {e}")
        db.rollback()

def save_signal_to_db(db: Session, trading_signal):
    """Sauvegarde un signal de trading en base"""
    try:
        signal = Signal(
            etf_isin=trading_signal.etf_isin,
            signal_type=SignalType(trading_signal.signal_type.value),
            confidence=trading_signal.confidence,
            price_target=trading_signal.price_target,
            stop_loss=trading_signal.stop_loss,
            entry_price=trading_signal.entry_price,
            technical_score=trading_signal.technical_score,
            risk_score=trading_signal.risk_score,
            reasons=trading_signal.reasons,
            timestamp=trading_signal.timestamp
        )
        
        db.add(signal)
        db.commit()
        
        logger.info(f"Signal sauvegardé: {trading_signal.symbol} - {trading_signal.signal_type.value}")
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde signal: {e}")
        db.rollback()

def save_index_data_to_db(db: Session, index_name: str, data: Dict[str, Any]):
    """Sauvegarde les données d'indices en base"""
    # Ici, nous pourrions avoir une table séparée pour les indices
    # Pour l'instant, on log juste
    logger.info(f"Index {index_name}: {data.get('price', 'N/A')} ({data.get('change_percent', 0):.2f}%)")

# Configuration des tâches périodiques
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure les tâches périodiques"""
    
    # Collecte des données de marché toutes les 5 minutes (heures de marché)
    sender.add_periodic_task(
        300.0,  # 5 minutes
        collect_market_data_task.s(),
        name='Collecte données marché'
    )
    
    # Mise à jour des indices toutes les 10 minutes
    sender.add_periodic_task(
        600.0,  # 10 minutes
        update_market_indices_task.s(),
        name='Mise à jour indices'
    )
    
    # Vérification des alertes de prix toutes les 15 minutes
    sender.add_periodic_task(
        900.0,  # 15 minutes
        check_price_alerts_task.s(),
        name='Vérification alertes prix'
    )
    
    # Nettoyage quotidien à 2h du matin
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_data_task.s(),
        name='Nettoyage quotidien'
    )

# Pour les imports crontab si nécessaire
try:
    from celery.schedules import crontab
except ImportError:
    # Fallback pour les environnements sans crontab
    def crontab(*args, **kwargs):
        return None