"""
Modèles pour les préférences utilisateur et watchlists
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserWatchlist(Base):
    """Table des ETFs suivis par l'utilisateur"""
    __tablename__ = "user_watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    etf_isin = Column(String(12), nullable=False, index=True)
    etf_symbol = Column(String(20), nullable=False)
    added_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relation avec l'utilisateur
    user = relationship("User", back_populates="watchlist")

class UserPreferences(Base):
    """Table des préférences utilisateur"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Préférences de trading
    risk_tolerance = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    preferred_sectors = Column(JSON, nullable=True)  # Liste des secteurs préférés
    preferred_regions = Column(JSON, nullable=True)  # Liste des régions préférées
    max_position_size = Column(Float, default=0.05)  # 5% max par position
    max_ter = Column(Float, default=0.50)  # TER maximum accepté
    min_aum = Column(Float, default=100000000)  # AUM minimum (100M€)
    
    # Préférences d'alertes
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    min_signal_confidence = Column(Float, default=60.0)  # Confiance minimum pour les signaux
    
    # Préférences d'affichage
    dashboard_layout = Column(JSON, nullable=True)
    theme = Column(String(20), default="light")
    language = Column(String(5), default="fr")
    timezone = Column(String(50), default="Europe/Paris")
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relation avec l'utilisateur
    user = relationship("User", back_populates="preferences")

class UserAlert(Base):
    """Table des alertes personnalisées utilisateur"""
    __tablename__ = "user_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    etf_isin = Column(String(12), nullable=False, index=True)
    etf_symbol = Column(String(20), nullable=False)
    
    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # price_target, stop_loss, volume_spike, signal
    
    # Conditions
    condition_type = Column(String(20), nullable=False)  # above, below, equals
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    trigger_once = Column(Boolean, default=True)  # Se déclenche une seule fois
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    message = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relation avec l'utilisateur
    user = relationship("User", back_populates="user_alerts")


class UserSignalSubscription(Base):
    """Table des abonnements aux signaux par ETF"""
    __tablename__ = "user_signal_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    etf_isin = Column(String(12), nullable=False, index=True)
    etf_symbol = Column(String(20), nullable=False)
    
    # Configuration des signaux
    min_confidence = Column(Float, default=60.0)
    signal_types = Column(JSON, nullable=True)  # Types de signaux souhaités
    max_risk_score = Column(Float, default=70.0)
    
    # Statut
    is_active = Column(Boolean, default=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relation avec l'utilisateur
    user = relationship("User", back_populates="signal_subscriptions")