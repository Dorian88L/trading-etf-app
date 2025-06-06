from sqlalchemy import Column, String, DateTime, DECIMAL, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'etf_isin'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    quantity = Column(DECIMAL(12, 4), nullable=False)
    average_price = Column(DECIMAL(10, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    etf = relationship("ETF", back_populates="positions")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(DECIMAL(12, 4), nullable=False)
    price = Column(DECIMAL(10, 4), nullable=False)
    fees = Column(DECIMAL(10, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    etf = relationship("ETF", back_populates="transactions")