"""
Schémas Pydantic pour les préférences ETF utilisateur
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserETFPreferenceBase(BaseModel):
    etf_isin: str
    is_visible_on_dashboard: bool = True
    is_visible_on_etf_list: bool = True
    is_favorite: bool = False
    display_order: int = 0
    custom_name: Optional[str] = None
    notes: Optional[str] = None

class UserETFPreferenceCreate(UserETFPreferenceBase):
    pass

class UserETFPreferenceUpdate(BaseModel):
    is_visible_on_dashboard: Optional[bool] = None
    is_visible_on_etf_list: Optional[bool] = None
    is_favorite: Optional[bool] = None
    display_order: Optional[int] = None
    custom_name: Optional[str] = None
    notes: Optional[str] = None

class UserETFPreferenceResponse(UserETFPreferenceBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ETFWithPreferences(BaseModel):
    """ETF avec les préférences utilisateur"""
    isin: str
    name: str
    display_name: str  # Nom personnalisé ou nom par défaut
    sector: str
    currency: str
    exchange: str
    is_visible_on_dashboard: bool
    is_visible_on_etf_list: bool
    is_favorite: bool
    display_order: int
    notes: Optional[str] = None
    trading_symbol: Optional[str] = None
    
    # Données de marché temps réel (optionnelles)
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    last_update: Optional[datetime] = None

class AvailableETF(BaseModel):
    """ETF disponible pour sélection"""
    isin: str
    name: str
    sector: str
    currency: str
    exchange: str
    is_configured: bool = False  # L'utilisateur a-t-il déjà configuré cet ETF ?

class UserETFConfigurationResponse(BaseModel):
    """Réponse complète de configuration ETF utilisateur"""
    configured_etfs: List[ETFWithPreferences]
    available_etfs: List[AvailableETF]
    total_configured: int
    total_available: int