from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.alert import Alert, AlertType
from app.schemas.alert import AlertResponse, AlertCreate

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    alert_type: Optional[AlertType] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's alerts"""
    query = db.query(Alert).filter(Alert.user_id == current_user.id)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return alerts


@router.post("/", response_model=AlertResponse)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new alert"""
    db_alert = Alert(
        user_id=current_user.id,
        **alert.dict()
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


@router.put("/{alert_id}/read")
def mark_alert_as_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark alert as read"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}


@router.put("/mark-all-read")
def mark_all_alerts_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all alerts as read"""
    db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return {"message": "All alerts marked as read"}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Alert deleted"}


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread alerts"""
    count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).count()
    
    return {"unread_count": count}