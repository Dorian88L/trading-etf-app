"""
Schémas Pydantic pour les notifications
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationSubscriptionRequest(BaseModel):
    """Requête d'abonnement aux notifications push"""
    endpoint: str = Field(..., description="URL de l'endpoint push")
    p256dh: str = Field(..., description="Clé publique P256DH")
    auth: str = Field(..., description="Clé d'authentification")

class NotificationUnsubscribeRequest(BaseModel):
    """Requête de désabonnement aux notifications push"""
    endpoint: str = Field(..., description="URL de l'endpoint push à désabonner")

class TestNotificationRequest(BaseModel):
    """Requête pour envoyer une notification de test"""
    title: Optional[str] = Field(None, description="Titre de la notification")
    body: Optional[str] = Field(None, description="Corps de la notification")

class NotificationPreferencesUpdate(BaseModel):
    """Mise à jour des préférences de notification"""
    signal_notifications: Optional[bool] = Field(None, description="Notifications de signaux")
    price_alert_notifications: Optional[bool] = Field(None, description="Alertes de prix")
    market_alert_notifications: Optional[bool] = Field(None, description="Alertes de marché")
    portfolio_notifications: Optional[bool] = Field(None, description="Notifications de portfolio")
    system_notifications: Optional[bool] = Field(None, description="Notifications système")
    
    min_signal_confidence: Optional[float] = Field(None, ge=0, le=100, description="Confiance minimum pour signaux")
    min_price_change_percent: Optional[float] = Field(None, ge=0, description="Variation de prix minimum")
    min_volume_spike_percent: Optional[float] = Field(None, ge=0, description="Pic de volume minimum")
    
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Début heures de silence (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Fin heures de silence (HH:MM)")
    weekend_notifications: Optional[bool] = Field(None, description="Notifications le weekend")
    
    max_notifications_per_hour: Optional[int] = Field(None, ge=1, le=50, description="Maximum par heure")
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=200, description="Maximum par jour")

class NotificationPreferencesResponse(BaseModel):
    """Réponse avec les préférences de notification"""
    signal_notifications: bool
    price_alert_notifications: bool
    market_alert_notifications: bool
    portfolio_notifications: bool
    system_notifications: bool
    
    min_signal_confidence: float
    min_price_change_percent: float
    min_volume_spike_percent: float
    
    quiet_hours_start: str
    quiet_hours_end: str
    weekend_notifications: bool
    
    max_notifications_per_hour: int
    max_notifications_per_day: int

class NotificationHistoryItem(BaseModel):
    """Élément de l'historique des notifications"""
    id: int
    notification_type: str
    title: str
    body: str
    status: str
    etf_symbol: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

class PushNotificationPayload(BaseModel):
    """Payload d'une notification push"""
    title: str = Field(..., description="Titre de la notification")
    body: str = Field(..., description="Corps de la notification")
    icon: Optional[str] = Field(None, description="URL de l'icône")
    badge: Optional[str] = Field(None, description="URL du badge")
    tag: Optional[str] = Field(None, description="Tag pour grouper les notifications")
    requireInteraction: Optional[bool] = Field(False, description="Nécessite une interaction")
    data: Optional[Dict[str, Any]] = Field(None, description="Données supplémentaires")
    actions: Optional[list] = Field(None, description="Actions disponibles")

class SignalNotificationData(BaseModel):
    """Données spécifiques pour les notifications de signaux"""
    signal_id: int
    etf_isin: str
    etf_symbol: str
    signal_type: str  # BUY, SELL, HOLD, WAIT
    confidence: float
    entry_price: float
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None

class PriceAlertNotificationData(BaseModel):
    """Données spécifiques pour les alertes de prix"""
    etf_symbol: str
    current_price: float
    target_price: float
    alert_type: str  # price_target, stop_loss
    direction: str   # above, below