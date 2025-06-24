"""
Endpoints unifiés pour la gestion des watchlists
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.etf import ETF
from app.schemas.watchlist import WatchlistResponse, WatchlistCreate
from app.services.multi_source_etf_data import get_multi_source_etf_service

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

class WatchlistItemCreate(BaseModel):
    etf_symbol: str

class WatchlistItemResponse(BaseModel):
    id: str
    symbol: str
    isin: str
    name: str
    current_price: float
    change: float
    change_percent: float
    currency: str
    sector: str
    exchange: str
    added_at: datetime
    
    # Données temps réel
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    confidence_score: Optional[float] = None
    is_realtime: Optional[bool] = None
    source: Optional[str] = None

@router.get("/watchlist", response_model=List[WatchlistItemResponse])
async def get_user_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la watchlist de l'utilisateur avec données temps réel
    """
    try:
        logger.info(f"Récupération watchlist pour utilisateur {current_user.id}")
        
        # Récupérer la watchlist depuis la base
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).all()
        
        if not watchlist_items:
            logger.info(f"Watchlist vide pour utilisateur {current_user.id}")
            return []
        
        # Récupérer les données temps réel pour chaque ETF
        etf_service = get_multi_source_etf_service()
        result = []
        
        for item in watchlist_items:
            try:
                # Récupérer l'ETF depuis la base
                etf = db.query(ETF).filter(ETF.isin == item.etf_isin).first()
                if not etf:
                    logger.warning(f"ETF non trouvé pour ISIN {item.etf_isin}")
                    continue
                
                # Récupérer les données temps réel
                etf_data = await etf_service.get_etf_data_by_isin(item.etf_isin)
                
                if etf_data:
                    watchlist_item = WatchlistItemResponse(
                        id=str(item.id),
                        symbol=etf_data.symbol,
                        isin=etf_data.isin,
                        name=etf_data.name,
                        current_price=etf_data.current_price,
                        change=etf_data.change,
                        change_percent=etf_data.change_percent,
                        currency=etf_data.currency,
                        sector=etf_data.sector,
                        exchange=etf_data.exchange,
                        added_at=item.created_at,
                        volume=etf_data.volume,
                        market_cap=etf_data.market_cap,
                        confidence_score=etf_data.confidence_score,
                        is_realtime=True,
                        source=etf_data.source if hasattr(etf_data, 'source') else 'multi_source'
                    )
                else:
                    # Fallback avec données de base
                    watchlist_item = WatchlistItemResponse(
                        id=str(item.id),
                        symbol=etf.symbol,
                        isin=etf.isin,
                        name=etf.name,
                        current_price=0.0,
                        change=0.0,
                        change_percent=0.0,
                        currency=etf.currency,
                        sector=etf.sector,
                        exchange=etf.exchange,
                        added_at=item.created_at,
                        confidence_score=0.5,
                        is_realtime=False,
                        source='database_fallback'
                    )
                
                result.append(watchlist_item)
                
            except Exception as e:
                logger.error(f"Erreur traitement watchlist item {item.id}: {e}")
                continue
        
        logger.info(f"Watchlist récupérée: {len(result)} items pour utilisateur {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur récupération watchlist: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération watchlist: {str(e)}")

@router.post("/watchlist", response_model=Dict[str, str])
async def add_to_watchlist(
    item: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ajoute un ETF à la watchlist de l'utilisateur
    """
    try:
        logger.info(f"Ajout {item.etf_symbol} à la watchlist de {current_user.id}")
        
        # Trouver l'ETF par symbole
        etf = db.query(ETF).filter(
            (ETF.symbol == item.etf_symbol) | (ETF.isin == item.etf_symbol)
        ).first()
        
        if not etf:
            raise HTTPException(status_code=404, detail=f"ETF {item.etf_symbol} non trouvé")
        
        # Vérifier si déjà dans la watchlist
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id,
            Watchlist.etf_isin == etf.isin
        ).first()
        
        if existing:
            return {"status": "success", "message": f"ETF {item.etf_symbol} déjà dans la watchlist"}
        
        # Ajouter à la watchlist
        watchlist_item = Watchlist(
            id=uuid.uuid4(),
            user_id=current_user.id,
            etf_isin=etf.isin
        )
        
        db.add(watchlist_item)
        db.commit()
        
        logger.info(f"ETF {item.etf_symbol} ajouté à la watchlist de {current_user.id}")
        return {"status": "success", "message": f"ETF {item.etf_symbol} ajouté à la watchlist"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur ajout watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur ajout watchlist: {str(e)}")

@router.delete("/watchlist/{symbol}", response_model=Dict[str, str])
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un ETF de la watchlist de l'utilisateur
    """
    try:
        logger.info(f"Suppression {symbol} de la watchlist de {current_user.id}")
        
        # Trouver l'ETF
        etf = db.query(ETF).filter(
            (ETF.symbol == symbol) | (ETF.isin == symbol)
        ).first()
        
        if not etf:
            raise HTTPException(status_code=404, detail=f"ETF {symbol} non trouvé")
        
        # Supprimer de la watchlist
        deleted = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id,
            Watchlist.etf_isin == etf.isin
        ).delete()
        
        if deleted == 0:
            raise HTTPException(status_code=404, detail=f"ETF {symbol} non trouvé dans la watchlist")
        
        db.commit()
        
        logger.info(f"ETF {symbol} supprimé de la watchlist de {current_user.id}")
        return {"status": "success", "message": f"ETF {symbol} supprimé de la watchlist"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur suppression watchlist: {str(e)}")

@router.delete("/watchlist", response_model=Dict[str, str])
async def clear_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Vide complètement la watchlist de l'utilisateur
    """
    try:
        logger.info(f"Vidage watchlist de {current_user.id}")
        
        deleted = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        logger.info(f"Watchlist vidée: {deleted} items supprimés pour {current_user.id}")
        return {"status": "success", "message": f"Watchlist vidée ({deleted} items supprimés)"}
        
    except Exception as e:
        logger.error(f"Erreur vidage watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur vidage watchlist: {str(e)}")

@router.get("/watchlist/stats", response_model=Dict[str, Any])
async def get_watchlist_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de la watchlist
    """
    try:
        watchlist_count = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).count()
        
        # Récupérer quelques statistiques sur les ETFs suivis
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).all()
        
        sectors = []
        exchanges = []
        
        for item in watchlist_items:
            etf = db.query(ETF).filter(ETF.isin == item.etf_isin).first()
            if etf:
                if etf.sector:
                    sectors.append(etf.sector)
                if etf.exchange:
                    exchanges.append(etf.exchange)
        
        return {
            "total_items": watchlist_count,
            "sectors": list(set(sectors)),
            "exchanges": list(set(exchanges)),
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur stats watchlist: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur stats watchlist: {str(e)}")