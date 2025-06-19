from sqlalchemy import Column, String, DateTime, DECIMAL, BigInteger, ForeignKey, PrimaryKeyConstraint, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ETF(Base):
    __tablename__ = "etfs"
    
    isin = Column(String(12), primary_key=True)
    symbol = Column(String(20), nullable=False)  # Symbole principal pour trading
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
    symbol_mappings = relationship("ETFSymbolMapping", back_populates="etf")
    display_config = relationship("ETFDisplayConfig", back_populates="etf", uselist=False)


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


class ETFSymbolMapping(Base):
    __tablename__ = "etf_symbol_mappings"
    
    id = Column(String, primary_key=True)  # Composite: isin_exchange
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    exchange_code = Column(String(10), nullable=False)  # AS, DE, L, PA
    trading_symbol = Column(String(20), nullable=False)  # CSPX.AS, IWDA.L
    currency = Column(String(3), nullable=False)  # EUR, USD, GBP
    is_primary = Column(Boolean, default=False)  # Symbole principal pour les données temps réel
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    etf = relationship("ETF", back_populates="symbol_mappings")


class ETFDisplayConfig(Base):
    __tablename__ = "etf_display_config"
    
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), primary_key=True)
    is_visible_on_dashboard = Column(Boolean, default=True)
    is_visible_on_etf_list = Column(Boolean, default=True)
    display_order = Column(DECIMAL(3, 1), default=0)  # Pour l'ordre d'affichage
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    etf = relationship("ETF", back_populates="display_config")