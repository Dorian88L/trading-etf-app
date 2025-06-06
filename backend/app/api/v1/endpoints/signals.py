from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.signal import Signal, SignalType
from app.schemas.signal import SignalResponse, SignalCreate

router = APIRouter()


@router.get("/active", response_model=List[SignalResponse])
def get_active_signals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    signal_type: Optional[SignalType] = None,
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    etf_isin: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get active signals"""
    query = db.query(Signal).filter(Signal.is_active == True)
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    if min_confidence:
        query = query.filter(Signal.confidence >= min_confidence)
    if etf_isin:
        query = query.filter(Signal.etf_isin == etf_isin)
    
    # Apply user preferences for minimum confidence
    if current_user.preferences and current_user.preferences.min_signal_confidence:
        query = query.filter(Signal.confidence >= current_user.preferences.min_signal_confidence)
    
    signals = query.order_by(Signal.confidence.desc(), Signal.created_at.desc()).offset(skip).limit(limit).all()
    return signals


@router.get("/history", response_model=List[SignalResponse])
def get_signal_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    signal_type: Optional[SignalType] = None,
    etf_isin: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get signal history"""
    query = db.query(Signal)
    
    # Default to last 30 days if no dates provided
    if not start_date and not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    if start_date:
        query = query.filter(Signal.created_at >= start_date)
    if end_date:
        query = query.filter(Signal.created_at <= end_date)
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    if etf_isin:
        query = query.filter(Signal.etf_isin == etf_isin)
    
    signals = query.order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()
    return signals


@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal(
    signal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get signal by ID"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )
    return signal


@router.get("/etf/{isin}/latest", response_model=List[SignalResponse])
def get_latest_signals_for_etf(
    isin: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get latest signals for specific ETF"""
    signals = (
        db.query(Signal)
        .filter(Signal.etf_isin == isin)
        .order_by(Signal.created_at.desc())
        .limit(limit)
        .all()
    )
    return signals


@router.get("/top-performers")
def get_top_performing_signals(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get top performing signals (mock data for now)"""
    # This would normally calculate actual performance based on signal outcomes
    return [
        {
            "etf_isin": "FR0010296061",
            "signal_type": "BUY",
            "confidence": 85.5,
            "performance": 3.2,
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "etf_isin": "IE00B4L5Y983",
            "signal_type": "SELL",
            "confidence": 78.3,
            "performance": 2.8,
            "created_at": "2024-01-14T14:20:00Z"
        }
    ]