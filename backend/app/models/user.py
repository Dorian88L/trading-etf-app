from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, ForeignKey
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
    watchlists = relationship("Watchlist", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    risk_tolerance = Column(DECIMAL(3, 2), default=0.5)
    min_signal_confidence = Column(DECIMAL(5, 2), default=60)
    notification_settings = Column(
        JSONB, 
        default={"email": True, "push": True, "sms": False}
    )
    trading_preferences = Column(
        JSONB,
        default={"max_position_size": 0.1, "stop_loss_pct": 0.05}
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")