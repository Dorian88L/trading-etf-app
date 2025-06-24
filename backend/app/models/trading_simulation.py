"""
Modèles de base de données pour les simulations de trading automatique
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Integer, Float, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from enum import Enum


class SimulationStatus(str, Enum):
    """Statuts possibles d'une simulation"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


class TradingSimulation(Base):
    """Modèle pour stocker les simulations de trading automatique par utilisateur"""
    __tablename__ = "trading_simulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration de la simulation
    name = Column(String(255), nullable=False)
    initial_capital = Column(Float, nullable=False)
    duration_days = Column(Integer, nullable=False)
    strategy_type = Column(String(50), nullable=False)
    risk_level = Column(String(20))  # conservative, moderate, aggressive
    allowed_etf_sectors = Column(JSONB)  # Secteurs d'ETF autorisés
    rebalance_frequency_hours = Column(Integer)
    auto_stop_loss = Column(Boolean, default=True)
    auto_take_profit = Column(Boolean, default=True)
    
    # ETFs sélectionnés automatiquement
    etf_symbols = Column(JSONB)
    
    # État actuel de la simulation
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING, index=True)
    current_value = Column(Float)
    cash = Column(Float)
    total_return_pct = Column(Float)
    
    # Données de performance
    daily_returns = Column(JSONB)  # Historique des retours quotidiens
    active_positions = Column(JSONB)  # Positions actuellement détenues
    completed_trades = Column(JSONB)  # Historique des trades terminés
    risk_metrics = Column(JSONB)  # Métriques de risque temps réel
    
    # Planification
    next_rebalance = Column(DateTime)
    target_end_date = Column(DateTime)
    days_remaining = Column(Integer)
    
    # Résultats finaux (quand completed)
    final_metrics = Column(JSONB)
    benchmark_comparison = Column(JSONB)
    
    # Métadonnées de tâche Celery
    celery_task_id = Column(String(255), index=True)  # ID de la tâche Celery
    last_heartbeat = Column(DateTime)  # Dernière activité de la tâche
    
    # Informations d'erreur
    error_message = Column(Text)
    error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="trading_simulations")
    simulation_trades = relationship("SimulationTrade", back_populates="simulation", cascade="all, delete-orphan")


class SimulationTrade(Base):
    """Modèle pour stocker chaque trade individuel d'une simulation"""
    __tablename__ = "simulation_trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("trading_simulations.id"), nullable=False, index=True)
    
    # Détails du trade
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    commission = Column(Float, default=0)
    
    # Contexte du trade
    reason = Column(Text)  # Raison du signal de trading
    confidence = Column(Float)  # Confiance du signal (0-100)
    signal_type = Column(String(50))  # Type de signal technique
    
    # Résultats (pour les ventes)
    pnl = Column(Float)  # Profit/Loss réalisé
    pnl_pct = Column(Float)  # Pourcentage de gain/perte
    holding_period_hours = Column(Integer)  # Durée de détention
    
    # Relationships
    simulation = relationship("TradingSimulation", back_populates="simulation_trades")


class SimulationPerformanceSnapshot(Base):
    """Modèle pour stocker des snapshots de performance à intervalles réguliers"""
    __tablename__ = "simulation_performance_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("trading_simulations.id"), nullable=False, index=True)
    
    # Moment du snapshot
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Valeurs du portfolio
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    
    # Performance
    total_return_pct = Column(Float)
    daily_return_pct = Column(Float)
    
    # Métriques de risque
    volatility_30d = Column(Float)
    sharpe_ratio_30d = Column(Float)
    max_drawdown_pct = Column(Float)
    
    # Détails des positions
    positions_count = Column(Integer)
    largest_position_pct = Column(Float)
    sector_allocation = Column(JSONB)
    
    # Relationships
    simulation = relationship("TradingSimulation")


class SimulationLeaderboard(Base):
    """Modèle pour le classement des simulations"""
    __tablename__ = "simulation_leaderboard"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Période du classement
    period = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly, all_time
    rank = Column(Integer, nullable=False)
    
    # Simulation référencée
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("trading_simulations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Données du classement
    simulation_name = Column(String(255))
    return_pct = Column(Float)
    risk_level = Column(String(20))
    duration_days = Column(Integer)
    
    # Métadonnées
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    simulation = relationship("TradingSimulation")
    user = relationship("User")