from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
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
    risk_tolerance: Optional[float] = 0.5
    min_signal_confidence: Optional[float] = 60.0
    notification_settings: Optional[Dict[str, Any]] = {
        "email": True, 
        "push": True, 
        "sms": False
    }
    trading_preferences: Optional[Dict[str, Any]] = {
        "max_position_size": 0.1, 
        "stop_loss_pct": 0.05
    }


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