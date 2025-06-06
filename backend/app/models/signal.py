from sqlalchemy import Column, String, DateTime, DECIMAL, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class SignalType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"


class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    confidence = Column(DECIMAL(5, 2), nullable=False)  # 0-100
    price_target = Column(DECIMAL(10, 4))
    stop_loss = Column(DECIMAL(10, 4))
    technical_score = Column(DECIMAL(5, 2))
    fundamental_score = Column(DECIMAL(5, 2))
    risk_score = Column(DECIMAL(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    etf = relationship("ETF", back_populates="signals")