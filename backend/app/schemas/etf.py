from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ETFBase(BaseModel):
    isin: str
    name: str
    sector: Optional[str] = None
    currency: str = "EUR"
    ter: Optional[Decimal] = None
    aum: Optional[int] = None
    exchange: Optional[str] = None


class ETFResponse(ETFBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MarketDataBase(BaseModel):
    time: datetime
    etf_isin: str
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    nav: Optional[Decimal] = None


class MarketDataResponse(MarketDataBase):
    class Config:
        from_attributes = True


class TechnicalIndicatorsBase(BaseModel):
    time: datetime
    etf_isin: str
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    sma_200: Optional[Decimal] = None
    ema_20: Optional[Decimal] = None
    ema_50: Optional[Decimal] = None
    rsi: Optional[Decimal] = None
    macd: Optional[Decimal] = None
    macd_signal: Optional[Decimal] = None
    macd_histogram: Optional[Decimal] = None
    bb_upper: Optional[Decimal] = None
    bb_middle: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None
    atr: Optional[Decimal] = None
    obv: Optional[int] = None
    vwap: Optional[Decimal] = None


class TechnicalIndicatorsResponse(TechnicalIndicatorsBase):
    class Config:
        from_attributes = True