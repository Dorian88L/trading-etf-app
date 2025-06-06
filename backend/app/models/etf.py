from sqlalchemy import Column, String, DateTime, DECIMAL, BigInteger, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ETF(Base):
    __tablename__ = "etfs"
    
    isin = Column(String(12), primary_key=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    currency = Column(String(3), default="EUR")
    ter = Column(DECIMAL(5, 4))  # Total Expense Ratio
    aum = Column(BigInteger)  # Assets Under Management
    exchange = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    market_data = relationship("MarketData", back_populates="etf")
    technical_indicators = relationship("TechnicalIndicators", back_populates="etf")
    signals = relationship("Signal", back_populates="etf")
    positions = relationship("Position", back_populates="etf")
    transactions = relationship("Transaction", back_populates="etf")
    watchlists = relationship("Watchlist", back_populates="etf")


class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = (
        PrimaryKeyConstraint('time', 'etf_isin'),
    )
    
    time = Column(DateTime(timezone=True), nullable=False)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    open_price = Column(DECIMAL(10, 4))
    high_price = Column(DECIMAL(10, 4))
    low_price = Column(DECIMAL(10, 4))
    close_price = Column(DECIMAL(10, 4))
    volume = Column(BigInteger)
    nav = Column(DECIMAL(10, 4))  # Net Asset Value
    
    # Relationships
    etf = relationship("ETF", back_populates="market_data")


class TechnicalIndicators(Base):
    __tablename__ = "technical_indicators"
    __table_args__ = (
        PrimaryKeyConstraint('time', 'etf_isin'),
    )
    
    time = Column(DateTime(timezone=True), nullable=False)
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    
    # Moving Averages
    sma_20 = Column(DECIMAL(10, 4))
    sma_50 = Column(DECIMAL(10, 4))
    sma_200 = Column(DECIMAL(10, 4))
    ema_20 = Column(DECIMAL(10, 4))
    ema_50 = Column(DECIMAL(10, 4))
    
    # Oscillators
    rsi = Column(DECIMAL(5, 2))
    macd = Column(DECIMAL(10, 6))
    macd_signal = Column(DECIMAL(10, 6))
    macd_histogram = Column(DECIMAL(10, 6))
    
    # Bollinger Bands
    bb_upper = Column(DECIMAL(10, 4))
    bb_middle = Column(DECIMAL(10, 4))
    bb_lower = Column(DECIMAL(10, 4))
    
    # Other indicators
    atr = Column(DECIMAL(10, 4))  # Average True Range
    obv = Column(BigInteger)  # On Balance Volume
    vwap = Column(DECIMAL(10, 4))  # Volume Weighted Average Price
    
    # Relationships
    etf = relationship("ETF", back_populates="technical_indicators")