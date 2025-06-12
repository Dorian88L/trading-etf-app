from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserPreferencesBase(BaseModel):
    # Préférences de trading
    risk_tolerance: Optional[str] = "moderate"
    preferred_sectors: Optional[List[str]] = None
    preferred_regions: Optional[List[str]] = None
    max_position_size: Optional[float] = 0.05
    max_ter: Optional[float] = 0.50
    min_aum: Optional[float] = 100000000
    
    # Préférences d'alertes
    email_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = True
    sms_notifications: Optional[bool] = False
    min_signal_confidence: Optional[float] = 60.0
    
    # Préférences d'affichage
    dashboard_layout: Optional[Dict[str, Any]] = None
    theme: Optional[str] = "light"
    language: Optional[str] = "fr"
    timezone: Optional[str] = "Europe/Paris"


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True