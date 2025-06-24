"""
Modèles de base de données pour le backtesting
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Backtest(Base):
    """Modèle pour stocker les résultats de backtesting par utilisateur"""
    __tablename__ = "backtests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration du backtest
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    strategy_type = Column(String(50), nullable=False)
    strategy_params = Column(JSONB)
    etf_symbols = Column(JSONB)  # Liste des ETF utilisés
    rebalance_frequency = Column(String(20))
    transaction_cost_pct = Column(Float)
    stop_loss_pct = Column(Float)
    take_profit_pct = Column(Float)
    max_position_size_pct = Column(Float)
    
    # Résultats de performance
    total_return_pct = Column(Float)
    annualized_return_pct = Column(Float)
    volatility_pct = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    win_rate_pct = Column(Float)
    number_of_trades = Column(Integer)
    final_value = Column(Float)
    
    # Données détaillées (JSON)
    trades = Column(JSONB)  # Liste complète des trades
    equity_curve = Column(JSONB)  # Évolution de la valeur du portfolio
    risk_metrics = Column(JSONB)  # Métriques de risque avancées
    benchmark_comparison = Column(JSONB)  # Comparaison avec benchmark
    
    # Métadonnées
    execution_time_seconds = Column(Float)
    status = Column(String(20), default='completed')  # completed, failed, running
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="backtests")


class BacktestComparison(Base):
    """Modèle pour comparer plusieurs backtests"""
    __tablename__ = "backtest_comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    backtest_ids = Column(JSONB)  # Liste des IDs de backtests à comparer
    comparison_results = Column(JSONB)  # Résultats de la comparaison
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")