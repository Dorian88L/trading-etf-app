from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import re


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Mot de passe (min 8 caractères)")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """
        Validation robuste du mot de passe selon les standards de sécurité
        """
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        if len(v) > 128:
            raise ValueError('Le mot de passe ne peut pas dépasser 128 caractères')
        
        # Vérifications de complexité
        checks = {
            'lowercase': re.search(r'[a-z]', v),
            'uppercase': re.search(r'[A-Z]', v),
            'digit': re.search(r'[0-9]', v),
            'special': re.search(r'[!@#$%^&*(),.?":{}|<>_+=\-\[\]\\;\'`~]', v)
        }
        
        # Au moins 3 des 4 types de caractères requis
        valid_checks = sum(1 for check in checks.values() if check)
        if valid_checks < 3:
            raise ValueError(
                'Le mot de passe doit contenir au moins 3 types parmi: '
                'majuscules, minuscules, chiffres, caractères spéciaux'
            )
        
        # Mots de passe faibles interdits
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'user', 'test', 'guest',
            'trading', 'finance', 'investment', 'portfolio'
        ]
        
        if v.lower() in common_passwords:
            raise ValueError('Ce mot de passe est trop commun et donc interdit')
        
        # Pas de répétition excessive
        if re.search(r'(.)\1{3,}', v):  # Plus de 3 caractères identiques consécutifs
            raise ValueError('Le mot de passe ne peut pas contenir plus de 3 caractères identiques consécutifs')
        
        return v


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