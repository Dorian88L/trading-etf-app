from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.models.trading_simulation import SimulationStatus, SimulationStrategy


class TradingSimulationBase(BaseModel):
    """Base schema pour les simulations de trading."""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la simulation")
    initial_capital: float = Field(..., gt=0, description="Capital initial en euros")
    duration_days: int = Field(..., ge=1, le=365, description="Durée de la simulation en jours")
    strategy_type: str = Field(default="technical", description="Type de stratégie de trading")
    risk_level: Optional[str] = Field(default="medium", description="Niveau de risque")
    rebalance_frequency_hours: Optional[int] = Field(default=24, ge=1, le=168, description="Fréquence de rééquilibrage en heures")
    auto_stop_loss: Optional[bool] = Field(default=True, description="Stop loss automatique")
    auto_take_profit: Optional[bool] = Field(default=True, description="Take profit automatique")
    etf_symbols: Optional[List[str]] = Field(default=[], description="Liste des symboles ETF")
    
    @validator('duration_days')
    def validate_duration_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('La durée doit être entre 1 et 365 jours')
        return v
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v < 100:
            raise ValueError('Le capital initial doit être d\'au moins 100€')
        if v > 1000000:
            raise ValueError('Le capital initial ne peut pas dépasser 1,000,000€')
        return v


class TradingSimulationCreate(TradingSimulationBase):
    """Schema pour créer une nouvelle simulation."""
    pass


class TradingSimulationUpdate(BaseModel):
    """Schema pour mettre à jour une simulation existante."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    strategy_type: Optional[str] = Field(None, description="Type de stratégie")
    risk_level: Optional[str] = Field(None, description="Niveau de risque")
    rebalance_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    auto_stop_loss: Optional[bool] = Field(None, description="Stop loss automatique")
    auto_take_profit: Optional[bool] = Field(None, description="Take profit automatique")


class TradingSimulationResponse(TradingSimulationBase):
    """Schema pour répondre avec les données d'une simulation."""
    id: str  # UUID converti en string
    user_id: str  # UUID converti en string
    status: SimulationStatus
    current_value: Optional[float]
    cash: Optional[float]
    total_return_pct: Optional[float]
    active_positions: Optional[Dict[str, Any]]
    daily_returns: Optional[List[float]]
    completed_trades: Optional[List[Dict[str, Any]]]
    risk_metrics: Optional[Dict[str, Any]]
    next_rebalance: Optional[datetime]
    target_end_date: Optional[datetime]
    days_remaining: Optional[int]
    celery_task_id: Optional[str]
    last_heartbeat: Optional[datetime]
    error_message: Optional[str]
    error_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_rebalance_at: Optional[datetime] = None
    
    @validator('id', 'user_id', pre=True)
    def convert_uuid_to_string(cls, v):
        """Convertir les UUID en string pour la sérialisation"""
        if hasattr(v, 'hex'):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class SimulationTradeBase(BaseModel):
    """Base schema pour les trades de simulation."""
    etf_isin: str = Field(..., min_length=12, max_length=12, description="Code ISIN de l'ETF")
    etf_symbol: str = Field(..., max_length=20, description="Symbole de l'ETF")
    trade_type: str = Field(..., description="Type de trade (BUY/SELL)")
    quantity: float = Field(..., gt=0, description="Quantité d'actions")
    price: float = Field(..., gt=0, description="Prix d'exécution")
    total_amount: float = Field(..., description="Montant total de la transaction")
    reason: Optional[str] = Field(None, max_length=500, description="Raison du trade")


class SimulationTradeResponse(SimulationTradeBase):
    """Schema pour répondre avec les données d'un trade."""
    id: int
    simulation_id: int
    executed_at: datetime
    portfolio_value_before: float
    portfolio_value_after: float
    profit_loss: Optional[float]
    fees: float
    
    class Config:
        from_attributes = True


class SimulationStatsResponse(BaseModel):
    """Schema pour les statistiques d'une simulation."""
    simulation_id: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    current_capital: float
    best_trade: Optional[float]
    worst_trade: Optional[float]
    average_trade: Optional[float]
    
    class Config:
        from_attributes = True


class SimulationPerformanceResponse(BaseModel):
    """Schema pour les données de performance d'une simulation."""
    date: datetime
    portfolio_value: float
    total_return: float
    total_return_percent: float
    drawdown: float
    positions_count: int
    
    class Config:
        from_attributes = True


class SimulationLeaderboardResponse(BaseModel):
    """Schema pour le classement des simulations."""
    rank: int
    simulation_id: int
    simulation_name: str
    user_id: int
    total_return_percent: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    total_trades: int
    duration_days: int
    
    class Config:
        from_attributes = True