from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    portfolios = relationship("Portfolio", back_populates="user")
    watchlist = relationship("UserWatchlist", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    user_alerts = relationship("UserAlert", back_populates="user")
    signal_subscriptions = relationship("UserSignalSubscription", back_populates="user")
    push_subscriptions = relationship("PushSubscription", back_populates="user")
    notification_preferences = relationship("UserNotificationPreferences", back_populates="user", uselist=False)
    etf_preferences = relationship("UserETFPreferences", back_populates="user")
    backtests = relationship("Backtest", back_populates="user")
    trading_simulations = relationship("TradingSimulation", back_populates="user")


