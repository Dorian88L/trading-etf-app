from sqlalchemy import Column, String, DateTime, DECIMAL, BigInteger, ForeignKey, PrimaryKeyConstraint, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ETF(Base):
    __tablename__ = "etfs"
    
    isin = Column(String(12), primary_key=True)
    symbol = Column(String(20), nullable=False)  # Symbole principal pour trading
    name = Column(String(255), nullable=False)
    description = Column(Text)  # Description complète de l'ETF
    sector = Column(String(100))
    currency = Column(String(3), default="EUR")
    ter = Column(DECIMAL(5, 4))  # Total Expense Ratio
    aum = Column(BigInteger)  # Assets Under Management
    exchange = Column(String(50))
    
    # Nouvelles données essentielles
    dividend_yield = Column(DECIMAL(5, 4))  # Rendement dividende
    pe_ratio = Column(DECIMAL(8, 2))  # Price-to-Earnings ratio
    beta = Column(DECIMAL(6, 4))  # Volatilité relative
    inception_date = Column(DateTime(timezone=True))  # Date de création
    
    # Informations géographiques et thématiques
    geography = Column(String(100))  # Géographie (Europe, US, Global, etc.)
    investment_theme = Column(String(100))  # Thème d'investissement
    replication_method = Column(String(50))  # Physical, Synthetic, etc.
    
    # Métadonnées de qualité
    data_quality_score = Column(DECIMAL(3, 2), default=1.0)  # Score qualité données
    last_data_update = Column(DateTime(timezone=True))  # Dernière mise à jour
    is_active = Column(Boolean, default=True)  # ETF actif ou suspendu
    
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
    
    # Nouvelles données de marché
    change_absolute = Column(DECIMAL(10, 4))  # Variation absolue
    change_percent = Column(DECIMAL(6, 4))  # Variation en %
    market_cap = Column(BigInteger)  # Capitalisation
    
    # Données de trading avancées
    bid_price = Column(DECIMAL(10, 4))  # Prix d'achat
    ask_price = Column(DECIMAL(10, 4))  # Prix de vente
    spread = Column(DECIMAL(8, 4))  # Écart bid-ask
    
    # Métadonnées de source
    data_source = Column(String(50))  # investing_com, yahoo, etc.
    confidence_score = Column(DECIMAL(3, 2), default=1.0)  # Confiance donnée
    is_realtime = Column(Boolean, default=True)  # Temps réel ou différé
    
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
    
    # Configuration d'affichage avancée
    preferred_chart_type = Column(String(20), default='line')  # line, candle, area
    show_technical_indicators = Column(Boolean, default=True)
    default_timeframe = Column(String(10), default='1D')  # 1D, 1W, 1M, etc.
    
    # Alertes et notifications
    enable_price_alerts = Column(Boolean, default=False)
    enable_volume_alerts = Column(Boolean, default=False)
    alert_threshold_percent = Column(DECIMAL(5, 2), default=2.0)
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    etf = relationship("ETF", back_populates="display_config")


# Nouvelle table pour les données historiques
class ETFHistoricalData(Base):
    __tablename__ = "etf_historical_data"
    __table_args__ = (
        PrimaryKeyConstraint('etf_isin', 'date'),
        Index('idx_etf_historical_date', 'etf_isin', 'date'),
        Index('idx_etf_historical_latest', 'etf_isin', 'date', 'close_price'),
    )
    
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Prix OHLC
    open_price = Column(DECIMAL(10, 4), nullable=False)
    high_price = Column(DECIMAL(10, 4), nullable=False)
    low_price = Column(DECIMAL(10, 4), nullable=False)
    close_price = Column(DECIMAL(10, 4), nullable=False)
    adjusted_close = Column(DECIMAL(10, 4))  # Prix ajusté dividendes
    
    # Volume et valeur
    volume = Column(BigInteger)
    value_traded = Column(BigInteger)  # Valeur échangée
    
    # Données de performance
    change_percent = Column(DECIMAL(6, 4))
    volatility = Column(DECIMAL(6, 4))  # Volatilité quotidienne
    
    # Métadonnées
    data_source = Column(String(50))
    is_trading_day = Column(Boolean, default=True)
    
    # Relationships
    etf = relationship("ETF")


# Nouvelle table pour les alertes de marché
class ETFMarketAlert(Base):
    __tablename__ = "etf_market_alerts"
    
    id = Column(String, primary_key=True)  # UUID
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price_change, volume_spike, etc.
    threshold_value = Column(DECIMAL(10, 4))
    current_value = Column(DECIMAL(10, 4))
    alert_message = Column(Text)
    
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    etf = relationship("ETF")


# Table pour les données de qualité et sources
class ETFDataQuality(Base):
    __tablename__ = "etf_data_quality"
    __table_args__ = (
        PrimaryKeyConstraint('etf_isin', 'check_date'),
    )
    
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    check_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Scores de qualité par source
    scraping_score = Column(DECIMAL(3, 2))  # Score du scraping
    api_score = Column(DECIMAL(3, 2))  # Score des APIs
    overall_score = Column(DECIMAL(3, 2))  # Score global
    
    # Disponibilité des sources
    scraping_available = Column(Boolean, default=False)
    yahoo_api_available = Column(Boolean, default=False)
    investing_available = Column(Boolean, default=False)
    
    # Métriques de performance
    last_update_delay = Column(BigInteger)  # Délai dernière MAJ en secondes
    data_freshness_minutes = Column(BigInteger)  # Fraîcheur en minutes
    
    # Source privilégiée pour cet ETF
    preferred_source = Column(String(50))
    
    # Relationships
    etf = relationship("ETF")