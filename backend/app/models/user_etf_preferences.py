"""
Modèle pour les préférences ETF par utilisateur
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserETFPreferences(Base):
    __tablename__ = "user_etf_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    is_visible_on_dashboard = Column(Boolean, default=True)
    is_visible_on_etf_list = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    custom_name = Column(String(255))  # Nom personnalisé par l'utilisateur
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="etf_preferences")
    etf = relationship("ETF")