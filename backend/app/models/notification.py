"""
Modèles pour les notifications push et abonnements
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class PushSubscription(Base):
    """Table des abonnements push notifications"""
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Données de l'abonnement push
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh_key = Column(Text, nullable=False)
    auth_key = Column(Text, nullable=False)
    
    # Métadonnées
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="push_subscriptions")

class NotificationHistory(Base):
    """Historique des notifications envoyées"""
    __tablename__ = "notification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("push_subscriptions.id"), nullable=True)
    
    # Type et contenu
    notification_type = Column(String(50), nullable=False)  # signal, alert, price, market
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    
    # Statut
    status = Column(String(20), default='pending')  # pending, sent, failed, clicked
    error_message = Column(Text, nullable=True)
    
    # ETF associé (optionnel)
    etf_isin = Column(String(12), nullable=True, index=True)
    etf_symbol = Column(String(20), nullable=True)
    
    # Signal associé (optionnel)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    user = relationship("User")
    subscription = relationship("PushSubscription")

class UserNotificationPreferences(Base):
    """Préférences de notifications par utilisateur"""
    __tablename__ = "user_notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Types de notifications activées
    signal_notifications = Column(Boolean, default=True)
    price_alert_notifications = Column(Boolean, default=True)
    market_alert_notifications = Column(Boolean, default=True)
    portfolio_notifications = Column(Boolean, default=True)
    system_notifications = Column(Boolean, default=False)
    
    # Seuils
    min_signal_confidence = Column(Float, default=60.0)
    min_price_change_percent = Column(Float, default=3.0)
    min_volume_spike_percent = Column(Float, default=50.0)
    
    # Horaires (JSON avec format "HH:MM")
    quiet_hours_start = Column(String(5), default="22:00")  # Début période silence
    quiet_hours_end = Column(String(5), default="08:00")    # Fin période silence
    weekend_notifications = Column(Boolean, default=False)
    
    # Fréquence
    max_notifications_per_hour = Column(Integer, default=5)
    max_notifications_per_day = Column(Integer, default=20)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="notification_preferences")