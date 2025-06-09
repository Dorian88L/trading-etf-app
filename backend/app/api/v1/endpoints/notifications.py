"""
Endpoints pour la gestion des notifications push
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.notification import NotificationHistory, UserNotificationPreferences
from app.services.notification_service import notification_service
from app.schemas.notification import (
    NotificationSubscriptionRequest,
    NotificationUnsubscribeRequest,
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse,
    TestNotificationRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/subscribe")
async def subscribe_to_notifications(
    subscription_data: NotificationSubscriptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Abonne un utilisateur aux notifications push"""
    try:
        # Extraire les données de l'abonnement
        subscription_info = {
            "endpoint": subscription_data.endpoint,
            "keys": {
                "p256dh": subscription_data.p256dh,
                "auth": subscription_data.auth
            }
        }
        
        # Enregistrer l'abonnement
        success = await notification_service.subscribe_user(
            user_id=current_user.id,
            subscription_data=subscription_info,
            db=db
        )
        
        if success:
            logger.info(f"User {current_user.id} subscribed to push notifications")
            return {
                "status": "success",
                "message": "Abonnement aux notifications activé",
                "endpoint": subscription_data.endpoint
            }
        else:
            raise HTTPException(status_code=400, detail="Échec de l'abonnement")
            
    except Exception as e:
        logger.error(f"Error subscribing user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'abonnement")

@router.post("/unsubscribe")
async def unsubscribe_from_notifications(
    unsubscribe_data: NotificationUnsubscribeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Désabonne un utilisateur des notifications push"""
    try:
        success = await notification_service.unsubscribe_user(
            endpoint=unsubscribe_data.endpoint,
            db=db
        )
        
        if success:
            logger.info(f"User {current_user.id} unsubscribed from push notifications")
            return {
                "status": "success",
                "message": "Désabonnement réussi"
            }
        else:
            return {
                "status": "warning",
                "message": "Abonnement non trouvé"
            }
            
    except Exception as e:
        logger.error(f"Error unsubscribing user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du désabonnement")

@router.post("/test")
async def send_test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Envoie une notification de test"""
    try:
        success = await notification_service.send_push_notification(
            user_id=current_user.id,
            title=test_data.title or "🧪 Test de Notification",
            body=test_data.body or "Les notifications fonctionnent correctement!",
            data={"type": "test", "timestamp": str(datetime.now())},
            notification_type="system",
            db=db
        )
        
        if success:
            return {
                "status": "success",
                "message": "Notification de test envoyée"
            }
        else:
            raise HTTPException(status_code=400, detail="Échec de l'envoi")
            
    except Exception as e:
        logger.error(f"Error sending test notification to user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du test")

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les préférences de notification de l'utilisateur"""
    try:
        preferences = await notification_service.get_notification_preferences(
            user_id=current_user.id,
            db=db
        )
        
        return NotificationPreferencesResponse(**preferences)
        
    except Exception as e:
        logger.error(f"Error getting preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des préférences")

@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Met à jour les préférences de notification de l'utilisateur"""
    try:
        # Convertir en dictionnaire en excluant les valeurs None
        preferences_dict = preferences.dict(exclude_unset=True)
        
        success = await notification_service.update_notification_preferences(
            user_id=current_user.id,
            preferences=preferences_dict,
            db=db
        )
        
        if success:
            return {
                "status": "success",
                "message": "Préférences mises à jour"
            }
        else:
            raise HTTPException(status_code=400, detail="Échec de la mise à jour")
            
    except Exception as e:
        logger.error(f"Error updating preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")

@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique des notifications de l'utilisateur"""
    try:
        query = db.query(NotificationHistory).filter(
            NotificationHistory.user_id == current_user.id
        )
        
        if notification_type:
            query = query.filter(NotificationHistory.notification_type == notification_type)
        
        total = query.count()
        notifications = query.order_by(
            NotificationHistory.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "offset": offset,
            "limit": limit,
            "data": [
                {
                    "id": notif.id,
                    "type": notif.notification_type,
                    "title": notif.title,
                    "body": notif.body,
                    "status": notif.status,
                    "etf_symbol": notif.etf_symbol,
                    "created_at": notif.created_at.isoformat(),
                    "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                    "clicked_at": notif.clicked_at.isoformat() if notif.clicked_at else None
                }
                for notif in notifications
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting notification history for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")

@router.post("/mark-clicked/{notification_id}")
async def mark_notification_clicked(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Marque une notification comme cliquée"""
    try:
        notification = db.query(NotificationHistory).filter(
            NotificationHistory.id == notification_id,
            NotificationHistory.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification non trouvée")
        
        if notification.status == 'sent':
            notification.status = 'clicked'
            notification.clicked_at = datetime.now()
            db.commit()
        
        return {
            "status": "success",
            "message": "Notification marquée comme cliquée"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as clicked: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")

@router.get("/stats")
async def get_notification_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques des notifications de l'utilisateur"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Statistiques générales
        total_sent = db.query(NotificationHistory).filter(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.status == 'sent'
        ).count()
        
        total_clicked = db.query(NotificationHistory).filter(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.status == 'clicked'
        ).count()
        
        # Statistiques par type (derniers 30 jours)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        type_stats = db.query(
            NotificationHistory.notification_type,
            func.count(NotificationHistory.id).label('count')
        ).filter(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.created_at >= thirty_days_ago,
            NotificationHistory.status == 'sent'
        ).group_by(NotificationHistory.notification_type).all()
        
        # Statistiques par jour (derniers 7 jours)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        daily_stats = db.query(
            func.date(NotificationHistory.created_at).label('date'),
            func.count(NotificationHistory.id).label('count')
        ).filter(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.created_at >= seven_days_ago,
            NotificationHistory.status == 'sent'
        ).group_by(func.date(NotificationHistory.created_at)).all()
        
        return {
            "status": "success",
            "data": {
                "total_sent": total_sent,
                "total_clicked": total_clicked,
                "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0,
                "type_distribution": {
                    stat.notification_type: stat.count for stat in type_stats
                },
                "daily_volume": {
                    stat.date.isoformat(): stat.count for stat in daily_stats
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")