from pydantic import BaseModel
from typing import Optional
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