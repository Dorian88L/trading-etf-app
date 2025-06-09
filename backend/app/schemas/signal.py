from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid
from app.models.signal import SignalType


class SignalBase(BaseModel):
    etf_isin: str
    signal_type: SignalType
    confidence: Decimal
    price_target: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    technical_score: Optional[Decimal] = None
    fundamental_score: Optional[Decimal] = None
    risk_score: Optional[Decimal] = None
    expires_at: Optional[datetime] = None


class SignalCreate(SignalBase):
    pass


class SignalResponse(SignalBase):
    id: uuid.UUID
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class TradingSignalResponse(BaseModel):
    id: str
    etf_isin: str
    signal_type: str
    strategy: str
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    expected_return: float
    risk_score: float
    timeframe: str
    reasons: List[str]
    technical_score: float
    generated_at: datetime
    is_active: bool
    expires_at: datetime
    
    class Config:
        from_attributes = True