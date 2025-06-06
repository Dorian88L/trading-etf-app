"""
Endpoints pour les données de marché réelles
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.schemas.etf import ETFResponse

router = APIRouter()

@router.get("/real-etfs")
async def get_real_etf_data(
    symbols: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère les données réelles des ETFs européens
    symbols: Liste de symboles séparés par des virgules (optionnel)
    """
    try:
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
            etf_data = []
            for symbol in symbol_list:
                data = market_service.get_real_etf_data(symbol)
                if data:
                    etf_data.append({
                        'symbol': data.symbol,
                        'isin': data.isin,
                        'name': data.name,
                        'current_price': data.current_price,
                        'change': data.change,
                        'change_percent': data.change_percent,
                        'volume': data.volume,
                        'market_cap': data.market_cap,
                        'currency': data.currency,
                        'exchange': data.exchange,
                        'sector': data.sector,
                        'last_update': data.last_update.isoformat()
                    })
        else:
            # Récupérer tous les ETFs configurés
            etf_data_list = await market_service.collect_all_etf_data()
            etf_data = []
            for data in etf_data_list:
                etf_data.append({
                    'symbol': data.symbol,
                    'isin': data.isin,
                    'name': data.name,
                    'current_price': data.current_price,
                    'change': data.change,
                    'change_percent': data.change_percent,
                    'volume': data.volume,
                    'market_cap': data.market_cap,
                    'currency': data.currency,
                    'exchange': data.exchange,
                    'sector': data.sector,
                    'last_update': data.last_update.isoformat()
                })
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

@router.get("/real-indices")
async def get_real_market_indices(
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Récupère les données réelles des indices de marché européens"""
    try:
        indices_data = market_service.get_market_indices()
        
        return {
            'status': 'success',
            'count': len(indices_data),
            'data': indices_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indices: {str(e)}")

@router.get("/real-market-data/{symbol}")
async def get_real_historical_data(
    symbol: str,
    period: str = "1mo",
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère les données historiques réelles d'un ETF
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        historical_data = market_service.get_historical_data(symbol, period)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour le symbole {symbol}")
        
        # Convertir en format API
        data_points = []
        for point in historical_data:
            data_points.append({
                'timestamp': point.timestamp.isoformat(),
                'open_price': point.open_price,
                'high_price': point.high_price,
                'low_price': point.low_price,
                'close_price': point.close_price,
                'volume': point.volume,
                'adj_close': point.adj_close
            })
        
        return {
            'status': 'success',
            'symbol': symbol,
            'period': period,
            'count': len(data_points),
            'data': data_points,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")

@router.post("/update-database")
async def update_database_with_real_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Met à jour la base de données avec les données réelles (tâche en arrière-plan)"""
    try:
        background_tasks.add_task(market_service.update_database_with_real_data)
        
        return {
            'status': 'success',
            'message': 'Mise à jour de la base de données lancée en arrière-plan',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la mise à jour: {str(e)}")

@router.get("/available-etfs")
async def get_available_etfs(
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Retourne la liste des ETFs européens disponibles"""
    etf_list = []
    
    for symbol, info in market_service.EUROPEAN_ETFS.items():
        etf_list.append({
            'symbol': symbol,
            'isin': info['isin'],
            'name': info['name'],
            'sector': info['sector'],
            'exchange': info['exchange']
        })
    
    return {
        'status': 'success',
        'count': len(etf_list),
        'etfs': etf_list,
        'timestamp': datetime.now().isoformat()
    }

@router.get("/market-status")
async def get_market_status(
    current_user: User = Depends(get_current_active_user)
):
    """Retourne le statut des marchés (ouvert/fermé)"""
    now = datetime.now()
    
    # Logique simplifiée pour les heures de marché européen
    hour = now.hour
    weekday = now.weekday()  # 0 = lundi, 6 = dimanche
    
    # Marchés européens généralement ouverts de 9h à 17h30, lundi à vendredi
    market_open = (weekday < 5) and (9 <= hour < 17)
    
    return {
        'status': 'success',
        'market_open': market_open,
        'current_time': now.isoformat(),
        'next_open': 'Lundi 9h00' if weekday >= 5 else 'Demain 9h00' if hour >= 17 else 'Maintenant',
        'timezone': 'CET/CEST'
    }