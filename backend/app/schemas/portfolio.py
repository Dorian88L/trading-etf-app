from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid
from app.models.portfolio import TransactionType


class PortfolioBase(BaseModel):
    name: str


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PositionBase(BaseModel):
    etf_isin: str
    quantity: Decimal
    average_price: Decimal


class PositionResponse(PositionBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    etf_isin: str
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    fees: Optional[Decimal] = 0


class TransactionCreate(TransactionBase):
    portfolio_id: uuid.UUID


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True