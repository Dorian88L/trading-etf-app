"""
API pour gérer les préférences ETF par utilisateur
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.etf import ETF
from app.models.user_etf_preferences import UserETFPreferences
from app.schemas.user_etf_preferences import (
    UserETFPreferenceCreate,
    UserETFPreferenceUpdate,
    UserETFPreferenceResponse,
    ETFWithPreferences,
    AvailableETF,
    UserETFConfigurationResponse
)
from app.services.dynamic_etf_service import get_dynamic_etf_service

router = APIRouter()

@router.get("/configuration", response_model=UserETFConfigurationResponse)
async def get_user_etf_configuration(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère la configuration ETF complète de l'utilisateur"""
    
    # Récupérer les ETFs configurés par l'utilisateur
    user_preferences = db.query(UserETFPreferences).filter(
        UserETFPreferences.user_id == current_user.id
    ).all()
    
    # Récupérer tous les ETFs disponibles
    all_etfs = db.query(ETF).all()
    
    # ETFs configurés avec préférences
    configured_etfs = []
    configured_isins = set()
    
    for pref in user_preferences:
        etf = db.query(ETF).filter(ETF.isin == pref.etf_isin).first()
        if etf:
            configured_etfs.append(ETFWithPreferences(
                isin=etf.isin,
                name=etf.name,
                display_name=pref.custom_name or etf.name,
                sector=etf.sector or "Unknown",
                currency=etf.currency,
                exchange=etf.exchange or "Unknown",
                is_visible_on_dashboard=pref.is_visible_on_dashboard,
                is_visible_on_etf_list=pref.is_visible_on_etf_list,
                is_favorite=pref.is_favorite,
                display_order=pref.display_order,
                notes=pref.notes
            ))
            configured_isins.add(etf.isin)
    
    # ETFs disponibles (non encore configurés)
    available_etfs = []
    for etf in all_etfs:
        available_etfs.append(AvailableETF(
            isin=etf.isin,
            name=etf.name,
            sector=etf.sector or "Unknown",
            currency=etf.currency,
            exchange=etf.exchange or "Unknown",
            is_configured=etf.isin in configured_isins
        ))
    
    return UserETFConfigurationResponse(
        configured_etfs=configured_etfs,
        available_etfs=available_etfs,
        total_configured=len(configured_etfs),
        total_available=len(all_etfs)
    )

@router.post("/preferences", response_model=UserETFPreferenceResponse)
async def create_user_etf_preference(
    preference: UserETFPreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ajoute un ETF aux préférences de l'utilisateur"""
    
    # Vérifier que l'ETF existe
    etf = db.query(ETF).filter(ETF.isin == preference.etf_isin).first()
    if not etf:
        raise HTTPException(status_code=404, detail=f"ETF {preference.etf_isin} non trouvé")
    
    # Vérifier si la préférence existe déjà
    existing = db.query(UserETFPreferences).filter(
        UserETFPreferences.user_id == current_user.id,
        UserETFPreferences.etf_isin == preference.etf_isin
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Préférence déjà existante pour cet ETF")
    
    # Créer la nouvelle préférence
    db_preference = UserETFPreferences(
        user_id=current_user.id,
        **preference.dict()
    )
    
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    
    return db_preference

@router.put("/preferences/{etf_isin}", response_model=UserETFPreferenceResponse)
async def update_user_etf_preference(
    etf_isin: str,
    preference_update: UserETFPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Met à jour les préférences ETF de l'utilisateur"""
    
    # Récupérer la préférence existante
    db_preference = db.query(UserETFPreferences).filter(
        UserETFPreferences.user_id == current_user.id,
        UserETFPreferences.etf_isin == etf_isin
    ).first()
    
    if not db_preference:
        raise HTTPException(status_code=404, detail="Préférence non trouvée")
    
    # Mettre à jour les champs fournis
    update_data = preference_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preference, field, value)
    
    db_preference.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_preference)
    
    return db_preference

@router.delete("/preferences/{etf_isin}")
async def delete_user_etf_preference(
    etf_isin: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprime un ETF des préférences de l'utilisateur"""
    
    db_preference = db.query(UserETFPreferences).filter(
        UserETFPreferences.user_id == current_user.id,
        UserETFPreferences.etf_isin == etf_isin
    ).first()
    
    if not db_preference:
        raise HTTPException(status_code=404, detail="Préférence non trouvée")
    
    db.delete(db_preference)
    db.commit()
    
    return {"message": "Préférence supprimée avec succès"}

@router.get("/dashboard-etfs")
async def get_user_dashboard_etfs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les ETFs configurés pour le dashboard avec données temps réel"""
    
    # Récupérer les ETFs visibles sur le dashboard
    dashboard_prefs = db.query(UserETFPreferences).filter(
        UserETFPreferences.user_id == current_user.id,
        UserETFPreferences.is_visible_on_dashboard == True
    ).order_by(
        UserETFPreferences.display_order,
        UserETFPreferences.is_favorite.desc()
    ).all()
    
    if not dashboard_prefs:
        return {
            'status': 'success',
            'count': 0,
            'data': [],
            'message': 'Aucun ETF configuré pour le dashboard'
        }
    
    # Récupérer les données temps réel via le service dynamique
    dynamic_service = get_dynamic_etf_service()
    etf_data_list = []
    
    for pref in dashboard_prefs:
        try:
            # Créer une config temporaire pour l'ETF
            etf = db.query(ETF).filter(ETF.isin == pref.etf_isin).first()
            if etf:
                from app.services.dynamic_etf_service import ETFConfig
                
                # Récupérer le symbole principal depuis les mappings
                from app.models.etf import ETFSymbolMapping
                primary_mapping = db.query(ETFSymbolMapping).filter(
                    ETFSymbolMapping.etf_isin == etf.isin,
                    ETFSymbolMapping.is_primary == True
                ).first()
                
                etf_config = ETFConfig(
                    isin=etf.isin,
                    name=pref.custom_name or etf.name,
                    sector=etf.sector or "Unknown",
                    currency=etf.currency,
                    exchange=etf.exchange or "Unknown",
                    ter=float(etf.ter) if etf.ter else None,
                    aum=etf.aum,
                    primary_trading_symbol=primary_mapping.trading_symbol if primary_mapping else None,
                    alternative_symbols=[],
                    is_visible_dashboard=True,
                    is_visible_etf_list=pref.is_visible_on_etf_list,
                    display_order=float(pref.display_order)
                )
                
                # Récupérer les données temps réel
                realtime_data = await dynamic_service.get_realtime_data_for_etf(etf_config)
                
                if realtime_data:
                    etf_data_list.append({
                        'symbol': realtime_data.symbol,
                        'isin': realtime_data.isin,
                        'name': pref.custom_name or realtime_data.name,
                        'current_price': realtime_data.current_price,
                        'change': realtime_data.change,
                        'change_percent': realtime_data.change_percent,
                        'volume': realtime_data.volume,
                        'market_cap': realtime_data.market_cap,
                        'currency': realtime_data.currency,
                        'exchange': realtime_data.exchange,
                        'sector': realtime_data.sector,
                        'last_update': realtime_data.last_update.isoformat(),
                        'source': realtime_data.source.value,
                        'confidence_score': realtime_data.confidence_score,
                        'is_favorite': pref.is_favorite,
                        'display_order': pref.display_order,
                        'custom_name': pref.custom_name
                    })
        except Exception as e:
            print(f"Erreur pour ETF {pref.etf_isin}: {e}")
            continue
    
    return {
        'status': 'success',
        'count': len(etf_data_list),
        'data': etf_data_list,
        'timestamp': datetime.now().isoformat(),
        'data_source': 'user_preferences_with_realtime'
    }

@router.post("/quick-setup")
async def quick_setup_popular_etfs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Configuration rapide avec les ETFs populaires"""
    
    # ETFs populaires à ajouter par défaut
    popular_etfs = [
        "IE00B5BMR087",  # iShares Core S&P 500
        "IE00B4L5Y983",  # iShares Core MSCI World
        "IE00BK5BQT80",  # Vanguard FTSE All-World
        "IE00B3XXRP09",  # Vanguard S&P 500
        "IE00B1YZSC51",  # iShares Core MSCI Europe
    ]
    
    added_count = 0
    for i, isin in enumerate(popular_etfs):
        # Vérifier si l'ETF existe
        etf = db.query(ETF).filter(ETF.isin == isin).first()
        if not etf:
            continue
            
        # Vérifier si l'utilisateur a déjà cette préférence
        existing = db.query(UserETFPreferences).filter(
            UserETFPreferences.user_id == current_user.id,
            UserETFPreferences.etf_isin == isin
        ).first()
        
        if not existing:
            preference = UserETFPreferences(
                user_id=current_user.id,
                etf_isin=isin,
                is_visible_on_dashboard=True,
                is_visible_on_etf_list=True,
                is_favorite=i < 3,  # Les 3 premiers sont favoris
                display_order=i
            )
            db.add(preference)
            added_count += 1
    
    db.commit()
    
    return {
        'status': 'success',
        'message': f'{added_count} ETFs populaires ajoutés à votre configuration',
        'added_count': added_count
    }