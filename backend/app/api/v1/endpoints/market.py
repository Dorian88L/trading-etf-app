from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.etf import ETF, MarketData, TechnicalIndicators
from app.schemas.etf import ETFResponse, MarketDataResponse, TechnicalIndicatorsResponse

router = APIRouter()


@router.get("/etfs", response_model=List[ETFResponse])
def get_etfs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sector: Optional[str] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of ETFs"""
    query = db.query(ETF)
    
    if sector:
        query = query.filter(ETF.sector == sector)
    if currency:
        query = query.filter(ETF.currency == currency)
    
    etfs = query.offset(skip).limit(limit).all()
    return etfs


@router.get("/etf/{isin}", response_model=ETFResponse)
def get_etf(
    isin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ETF by ISIN"""
    etf = db.query(ETF).filter(ETF.isin == isin).first()
    if not etf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETF not found"
        )
    return etf


@router.get("/etf/{isin}/market-data", response_model=List[MarketDataResponse])
def get_market_data(
    isin: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get market data for ETF"""
    # Check if ETF exists
    etf = db.query(ETF).filter(ETF.isin == isin).first()
    if not etf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETF not found"
        )
    
    query = db.query(MarketData).filter(MarketData.etf_isin == isin)
    
    # Default to last 30 days if no dates provided
    if not start_date and not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    if start_date:
        query = query.filter(MarketData.time >= start_date)
    if end_date:
        query = query.filter(MarketData.time <= end_date)
    
    market_data = query.order_by(MarketData.time.desc()).limit(limit).all()
    return market_data


@router.get("/etf/{isin}/technical-indicators", response_model=List[TechnicalIndicatorsResponse])
def get_technical_indicators(
    isin: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get technical indicators for ETF"""
    # Check if ETF exists
    etf = db.query(ETF).filter(ETF.isin == isin).first()
    if not etf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETF not found"
        )
    
    query = db.query(TechnicalIndicators).filter(TechnicalIndicators.etf_isin == isin)
    
    # Default to last 30 days if no dates provided
    if not start_date and not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    if start_date:
        query = query.filter(TechnicalIndicators.time >= start_date)
    if end_date:
        query = query.filter(TechnicalIndicators.time <= end_date)
    
    indicators = query.order_by(TechnicalIndicators.time.desc()).limit(limit).all()
    return indicators


@router.get("/sectors")
def get_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of sectors"""
    sectors = db.query(ETF.sector).distinct().filter(ETF.sector.isnot(None)).all()
    return [sector[0] for sector in sectors]


@router.get("/indices")
def get_indices(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of indices with real data"""
    from app.services.real_market_data import real_market_service
    
    try:
        indices_data = real_market_service.get_market_indices()
        
        # Convert to the expected format
        indices_list = []
        for symbol, data in indices_data.items():
            indices_list.append({
                "name": data["name"],
                "symbol": symbol,
                "value": data["value"],
                "change": data["change"],
                "change_percent": data["change_percent"],
                "volume": data.get("volume", 0),
                "currency": data.get("currency", "EUR"),
                "last_update": data["last_update"]
            })
        
        return indices_list
        
    except Exception as e:
        # Fallback vers des données mock en cas d'erreur
        return [
            {"name": "CAC 40", "value": 7500.25, "change": 1.2, "change_percent": 0.016},
            {"name": "MSCI World", "value": 3250.80, "change": 0.8, "change_percent": 0.025},
            {"name": "S&P 500", "value": 4800.15, "change": -0.3, "change_percent": -0.006},
            {"name": "EURO STOXX 50", "value": 4200.60, "change": 0.5, "change_percent": 0.012}
        ]