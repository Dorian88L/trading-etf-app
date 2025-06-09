"""
Service de gestion des notifications push et alertes
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from pywebpush import webpush, WebPushException
import requests

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.notification import PushSubscription, NotificationHistory, UserNotificationPreferences
from app.models.user_preferences import UserAlert, UserSignalSubscription
from app.models.signal import Signal

logger = logging.getLogger(__name__)

class NotificationService:
    """Service principal pour les notifications push"""
    
    def __init__(self):
        # Configuration VAPID pour les notifications push
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        self.vapid_email = getattr(settings, 'VAPID_EMAIL', 'admin@trading-etf.com')
        
        # Configuration par défaut si les clés VAPID ne sont pas configurées
        if not self.vapid_private_key:
            logger.warning("VAPID keys not configured - notifications will use fallback mode")
    
    async def subscribe_user(self, user_id: int, subscription_data: Dict, db: Session) -> bool:
        """Enregistre un abonnement push pour un utilisateur"""
        try:
            # Vérifier si l'abonnement existe déjà
            existing = db.query(PushSubscription).filter(
                PushSubscription.endpoint == subscription_data['endpoint']
            ).first()
            
            if existing:
                # Mettre à jour l'abonnement existant
                existing.user_id = user_id
                existing.p256dh_key = subscription_data['keys']['p256dh']
                existing.auth_key = subscription_data['keys']['auth']
                existing.is_active = True
                existing.last_used_at = datetime.now()
            else:
                # Créer un nouvel abonnement
                subscription = PushSubscription(
                    user_id=user_id,
                    endpoint=subscription_data['endpoint'],
                    p256dh_key=subscription_data['keys']['p256dh'],
                    auth_key=subscription_data['keys']['auth'],
                    is_active=True
                )
                db.add(subscription)
            
            db.commit()
            logger.info(f"Push subscription registered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing user {user_id}: {e}")
            db.rollback()
            return False
    
    async def unsubscribe_user(self, endpoint: str, db: Session) -> bool:
        """Supprime un abonnement push"""
        try:
            subscription = db.query(PushSubscription).filter(
                PushSubscription.endpoint == endpoint
            ).first()
            
            if subscription:
                subscription.is_active = False
                db.commit()
                logger.info(f"Push subscription unsubscribed: {endpoint}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing {endpoint}: {e}")
            db.rollback()
            return False
    
    async def send_push_notification(
        self, 
        user_id: int, 
        title: str, 
        body: str, 
        data: Optional[Dict] = None,
        notification_type: str = "general",
        etf_isin: Optional[str] = None,
        etf_symbol: Optional[str] = None,
        signal_id: Optional[int] = None,
        db: Session = None
    ) -> bool:
        """Envoie une notification push à un utilisateur"""
        
        if not db:
            db = next(get_db())
        
        try:
            # Récupérer les abonnements actifs de l'utilisateur
            subscriptions = db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True
            ).all()
            
            if not subscriptions:
                logger.warning(f"No active push subscriptions for user {user_id}")
                return False
            
            # Vérifier les préférences de notification
            if not await self._should_send_notification(user_id, notification_type, db):
                logger.info(f"Notification blocked by user preferences for user {user_id}")
                return False
            
            # Préparer le payload
            payload = {
                "title": title,
                "body": body,
                "icon": "/logo192.png",
                "badge": "/logo192.png",
                "tag": f"{notification_type}-{datetime.now().timestamp()}",
                "requireInteraction": notification_type in ["signal", "alert"],
                "vibrate": [200, 100, 200],
                "data": data or {},
                "actions": self._get_notification_actions(notification_type)
            }
            
            success_count = 0
            
            # Envoyer à tous les abonnements
            for subscription in subscriptions:
                try:
                    # Créer l'entrée d'historique
                    notification_history = NotificationHistory(
                        user_id=user_id,
                        subscription_id=subscription.id,
                        notification_type=notification_type,
                        title=title,
                        body=body,
                        data=data,
                        etf_isin=etf_isin,
                        etf_symbol=etf_symbol,
                        signal_id=signal_id,
                        status='pending'
                    )
                    db.add(notification_history)
                    db.flush()  # Pour obtenir l'ID
                    
                    # Envoyer la notification
                    await self._send_to_subscription(subscription, payload, notification_history.id, db)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send to subscription {subscription.id}: {e}")
                    # Marquer comme failed dans l'historique
                    notification_history.status = 'failed'
                    notification_history.error_message = str(e)
                    continue
            
            db.commit()
            logger.info(f"Sent notification to {success_count}/{len(subscriptions)} subscriptions for user {user_id}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending push notification to user {user_id}: {e}")
            db.rollback()
            return False
    
    async def _send_to_subscription(
        self, 
        subscription: PushSubscription, 
        payload: Dict, 
        history_id: int,
        db: Session
    ):
        """Envoie la notification à un abonnement spécifique"""
        try:
            if self.vapid_private_key and self.vapid_public_key:
                # Utiliser webpush avec VAPID
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh_key,
                            "auth": subscription.auth_key
                        }
                    },
                    data=json.dumps(payload),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims={
                        "sub": f"mailto:{self.vapid_email}",
                        "aud": subscription.endpoint
                    }
                )
            else:
                # Mode fallback sans VAPID
                logger.warning("Sending notification without VAPID authentication")
                # Dans un vrai environnement, utiliser un service comme FCM
                # Pour le développement, simuler l'envoi
                await asyncio.sleep(0.1)  # Simuler latence réseau
            
            # Marquer comme envoyé
            history = db.query(NotificationHistory).get(history_id)
            if history:
                history.status = 'sent'
                history.sent_at = datetime.now()
            
            # Mettre à jour la dernière utilisation de l'abonnement
            subscription.last_used_at = datetime.now()
            
        except WebPushException as e:
            logger.error(f"WebPush error: {e}")
            # Marquer l'abonnement comme inactif si erreur permanente
            if e.response and e.response.status_code in [400, 404, 410]:
                subscription.is_active = False
                logger.info(f"Deactivated invalid subscription {subscription.id}")
            
            # Marquer dans l'historique
            history = db.query(NotificationHistory).get(history_id)
            if history:
                history.status = 'failed'
                history.error_message = str(e)
            
            raise e
    
    async def _should_send_notification(
        self, 
        user_id: int, 
        notification_type: str, 
        db: Session
    ) -> bool:
        """Vérifie si on doit envoyer la notification selon les préférences"""
        try:
            # Récupérer les préférences
            prefs = db.query(UserNotificationPreferences).filter(
                UserNotificationPreferences.user_id == user_id
            ).first()
            
            if not prefs:
                # Créer des préférences par défaut
                prefs = UserNotificationPreferences(user_id=user_id)
                db.add(prefs)
                db.commit()
            
            # Vérifier le type de notification
            type_enabled = {
                'signal': prefs.signal_notifications,
                'alert': prefs.price_alert_notifications,
                'market': prefs.market_alert_notifications,
                'portfolio': prefs.portfolio_notifications,
                'system': prefs.system_notifications
            }.get(notification_type, True)
            
            if not type_enabled:
                return False
            
            # Vérifier les heures de silence
            if not await self._is_within_allowed_hours(prefs):
                return False
            
            # Vérifier les limites de fréquence
            if not await self._check_rate_limits(user_id, prefs, db):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification preferences for user {user_id}: {e}")
            return True  # En cas d'erreur, autoriser par défaut
    
    async def _is_within_allowed_hours(self, prefs: UserNotificationPreferences) -> bool:
        """Vérifie si l'heure actuelle est dans les heures autorisées"""
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # Vérifier le weekend
            if not prefs.weekend_notifications and now.weekday() >= 5:  # Samedi=5, Dimanche=6
                return False
            
            # Vérifier les heures de silence
            quiet_start = prefs.quiet_hours_start
            quiet_end = prefs.quiet_hours_end
            
            if quiet_start and quiet_end:
                if quiet_start < quiet_end:
                    # Période normale (ex: 22:00 - 08:00 le lendemain)
                    return not (current_time >= quiet_start or current_time <= quiet_end)
                else:
                    # Période qui traverse minuit
                    return not (quiet_start <= current_time <= "23:59" or "00:00" <= current_time <= quiet_end)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking allowed hours: {e}")
            return True
    
    async def _check_rate_limits(
        self, 
        user_id: int, 
        prefs: UserNotificationPreferences, 
        db: Session
    ) -> bool:
        """Vérifie les limites de fréquence des notifications"""
        try:
            now = datetime.now()
            
            # Vérifier limite horaire
            hour_ago = now - timedelta(hours=1)
            hourly_count = db.query(NotificationHistory).filter(
                NotificationHistory.user_id == user_id,
                NotificationHistory.created_at >= hour_ago,
                NotificationHistory.status == 'sent'
            ).count()
            
            if hourly_count >= prefs.max_notifications_per_hour:
                return False
            
            # Vérifier limite journalière
            day_ago = now - timedelta(days=1)
            daily_count = db.query(NotificationHistory).filter(
                NotificationHistory.user_id == user_id,
                NotificationHistory.created_at >= day_ago,
                NotificationHistory.status == 'sent'
            ).count()
            
            if daily_count >= prefs.max_notifications_per_day:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limits for user {user_id}: {e}")
            return True
    
    def _get_notification_actions(self, notification_type: str) -> List[Dict]:
        """Retourne les actions disponibles selon le type de notification"""
        base_actions = [{"action": "dismiss", "title": "Ignorer"}]
        
        if notification_type == "signal":
            return [
                {"action": "view-signal", "title": "Voir signal"},
                {"action": "view-etf", "title": "Analyser ETF"},
                *base_actions
            ]
        elif notification_type == "alert":
            return [
                {"action": "view-alert", "title": "Voir alerte"},
                {"action": "view-portfolio", "title": "Portfolio"},
                *base_actions
            ]
        elif notification_type == "market":
            return [
                {"action": "view-market", "title": "Voir marché"},
                *base_actions
            ]
        else:
            return base_actions
    
    async def send_signal_notification(
        self, 
        user_id: int, 
        signal: Signal, 
        etf_name: str,
        db: Session
    ) -> bool:
        """Envoie une notification pour un signal de trading"""
        try:
            # Emoji selon le type de signal
            emoji = {
                'BUY': '📈',
                'SELL': '📉', 
                'HOLD': '⏸️',
                'WAIT': '⏳'
            }.get(signal.signal_type.value, '🔔')
            
            title = f"{emoji} Signal {signal.signal_type.value}"
            body = f"{etf_name}: Confiance {signal.confidence:.0f}%"
            
            if signal.price_target:
                body += f" • Objectif: {signal.price_target:.2f}€"
            
            data = {
                "signal_id": signal.id,
                "etf_isin": signal.etf_isin,
                "signal_type": signal.signal_type.value,
                "confidence": signal.confidence,
                "entry_price": signal.entry_price,
                "price_target": signal.price_target,
                "stop_loss": signal.stop_loss,
                "type": "trading-signal"
            }
            
            return await self.send_push_notification(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                notification_type="signal",
                etf_isin=signal.etf_isin,
                signal_id=signal.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")
            return False
    
    async def send_price_alert_notification(
        self, 
        user_id: int, 
        etf_symbol: str, 
        current_price: float, 
        target_price: float,
        alert_type: str = "price_target",
        db: Session = None
    ) -> bool:
        """Envoie une notification d'alerte de prix"""
        try:
            direction = "atteint" if current_price >= target_price else "approche"
            
            title = "💰 Alerte de Prix"
            body = f"{etf_symbol}: {current_price:.2f}€ {direction} votre objectif ({target_price:.2f}€)"
            
            data = {
                "etf_symbol": etf_symbol,
                "current_price": current_price,
                "target_price": target_price,
                "alert_type": alert_type,
                "type": "price-alert"
            }
            
            return await self.send_push_notification(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                notification_type="alert",
                etf_symbol=etf_symbol,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error sending price alert notification: {e}")
            return False
    
    async def get_notification_preferences(self, user_id: int, db: Session) -> Dict:
        """Récupère les préférences de notification d'un utilisateur"""
        try:
            prefs = db.query(UserNotificationPreferences).filter(
                UserNotificationPreferences.user_id == user_id
            ).first()
            
            if not prefs:
                # Créer des préférences par défaut
                prefs = UserNotificationPreferences(user_id=user_id)
                db.add(prefs)
                db.commit()
                db.refresh(prefs)
            
            return {
                "signal_notifications": prefs.signal_notifications,
                "price_alert_notifications": prefs.price_alert_notifications,
                "market_alert_notifications": prefs.market_alert_notifications,
                "portfolio_notifications": prefs.portfolio_notifications,
                "system_notifications": prefs.system_notifications,
                "min_signal_confidence": prefs.min_signal_confidence,
                "min_price_change_percent": prefs.min_price_change_percent,
                "min_volume_spike_percent": prefs.min_volume_spike_percent,
                "quiet_hours_start": prefs.quiet_hours_start,
                "quiet_hours_end": prefs.quiet_hours_end,
                "weekend_notifications": prefs.weekend_notifications,
                "max_notifications_per_hour": prefs.max_notifications_per_hour,
                "max_notifications_per_day": prefs.max_notifications_per_day
            }
            
        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return {}
    
    async def update_notification_preferences(
        self, 
        user_id: int, 
        preferences: Dict, 
        db: Session
    ) -> bool:
        """Met à jour les préférences de notification d'un utilisateur"""
        try:
            prefs = db.query(UserNotificationPreferences).filter(
                UserNotificationPreferences.user_id == user_id
            ).first()
            
            if not prefs:
                prefs = UserNotificationPreferences(user_id=user_id)
                db.add(prefs)
            
            # Mettre à jour les champs fournis
            for key, value in preferences.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            prefs.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            db.rollback()
            return False

# Instance globale du service
notification_service = NotificationService()