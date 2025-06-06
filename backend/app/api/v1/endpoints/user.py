from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, UserPreferences
from app.models.watchlist import Watchlist
from app.schemas.user import UserResponse, UserPreferencesResponse, UserPreferencesUpdate
from app.schemas.watchlist import WatchlistResponse

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return current_user


@router.get("/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences


@router.put("/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)
    
    # Update only provided fields
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    return preferences


@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_user_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).all()
    return watchlist


@router.post("/watchlist")
def add_to_watchlist(
    etf_isin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add ETF to watchlist"""
    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.etf_isin == etf_isin
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ETF already in watchlist"
        )
    
    watchlist_item = Watchlist(
        user_id=current_user.id,
        etf_isin=etf_isin
    )
    db.add(watchlist_item)
    db.commit()
    
    return {"message": "ETF added to watchlist"}


@router.delete("/watchlist/{etf_isin}")
def remove_from_watchlist(
    etf_isin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove ETF from watchlist"""
    watchlist_item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.etf_isin == etf_isin
    ).first()
    
    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETF not found in watchlist"
        )
    
    db.delete(watchlist_item)
    db.commit()
    
    return {"message": "ETF removed from watchlist"}