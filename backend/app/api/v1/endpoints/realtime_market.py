"""
Endpoints pour les données de marché temps réel
WebSocket et REST API pour streaming et requêtes ponctuelles
"""
import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.realtime_market_service import realtime_service
from app.services.smart_market_data import get_smart_market_data_service, SmartMarketDataService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """
    WebSocket pour streaming des données de marché temps réel
    """
    await websocket.accept()
    await realtime_service.add_websocket_connection(websocket)
    
    try:
        while True:
            # Maintien de la connexion en attente de messages
            data = await websocket.receive_text()
            
            # Traitement des commandes du client
            try:
                message = json.loads(data)
                command = message.get('command')
                
                if command == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                elif command == 'subscribe':
                    symbols = message.get('symbols', [])
                    # Pour l'instant, on diffuse tous les symboles
                    await websocket.send_text(json.dumps({
                        'type': 'subscribed',
                        'symbols': symbols,
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.warning("Message WebSocket invalide reçu")
                
    except WebSocketDisconnect:
        await realtime_service.remove_websocket_connection(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        await realtime_service.remove_websocket_connection(websocket)

@router.get("/realtime/{symbol}")
async def get_realtime_quote(
    symbol: str,
    current_user: User = Depends(get_current_user),
    smart_service: SmartMarketDataService = Depends(get_smart_market_data_service),
    db: Session = Depends(get_db)
):
    """
    Récupère la cotation temps réel d'un symbole avec cache intelligent
    """
    try:
        # Utiliser le service intelligent qui vérifie d'abord les données récentes en base
        data = await smart_service.get_realtime_data_smart(symbol.upper(), db)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Symbole {symbol} non trouvé")
        
        return {
            'status': 'success',
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'smart_cache'  # Indicateur de la source
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime/multiple")
async def get_multiple_quotes(
    symbols: str = Query(..., description="Symboles séparés par des virgules"),
    current_user: User = Depends(get_current_user),
    smart_service: SmartMarketDataService = Depends(get_smart_market_data_service),
    db: Session = Depends(get_db)
):
    """
    Récupère les cotations de plusieurs symboles avec optimisation intelligente
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symboles autorisés")
        
        # Utiliser le service intelligent pour traitement en lot optimisé
        results = await smart_service.get_multiple_realtime_smart(symbol_list, db)
        
        return {
            'status': 'success',
            'data': results,
            'count': len(results),
            'source': 'smart_cache',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intraday/{symbol}")
async def get_intraday_data(
    symbol: str,
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures d'historique"),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les données intraday d'un symbole
    """
    try:
        data = await realtime_service.get_historical_intraday(symbol.upper(), hours)
        
        return {
            'status': 'success',
            'data': {
                'symbol': symbol.upper(),
                'period_hours': hours,
                'data_points': len(data),
                'historical_data': data
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-overview")
async def get_market_overview(
    current_user: User = Depends(get_current_user)
):
    """
    Aperçu général du marché temps réel
    """
    try:
        overview = await realtime_service.get_market_overview()
        
        return {
            'status': 'success',
            'data': overview,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
async def get_watchlist_data(
    current_user: User = Depends(get_current_user)
):
    """
    Données temps réel pour la watchlist par défaut
    """
    try:
        watchlist_data = {}
        
        for symbol in realtime_service.watchlist_etfs:
            data = await realtime_service.get_realtime_data(symbol)
            if data:
                watchlist_data[symbol] = data
        
        # Calcul de statistiques globales
        if watchlist_data:
            prices = [d['price'] for d in watchlist_data.values()]
            changes = [d.get('change_percent', 0) for d in watchlist_data.values()]
            
            stats = {
                'total_symbols': len(watchlist_data),
                'average_price': sum(prices) / len(prices),
                'average_change': sum(changes) / len(changes),
                'positive_changes': sum(1 for c in changes if c > 0),
                'negative_changes': sum(1 for c in changes if c < 0)
            }
        else:
            stats = {
                'total_symbols': 0,
                'average_price': 0,
                'average_change': 0,
                'positive_changes': 0,
                'negative_changes': 0
            }
        
        return {
            'status': 'success',
            'data': {
                'symbols': watchlist_data,
                'statistics': stats,
                'last_update': max([d.get('timestamp', '') for d in watchlist_data.values()]) if watchlist_data else datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-status")
async def get_market_status(
    current_user: User = Depends(get_current_user)
):
    """
    Statut des différents marchés
    """
    try:
        market_status = {
            'european_markets': {
                'status': realtime_service._get_market_status('IWDA.AS'),
                'description': 'Marchés européens (Euronext, XETRA)',
                'trading_hours': '09:00 - 17:30 CET'
            },
            'us_markets': {
                'status': realtime_service._get_market_status('SPY'),
                'description': 'Marchés américains (NYSE, NASDAQ)',
                'trading_hours': '09:30 - 16:00 EST'
            },
            'asian_markets': {
                'status': 'closed',  # Simplifié pour l'exemple
                'description': 'Marchés asiatiques',
                'trading_hours': '09:00 - 15:00 JST'
            }
        }
        
        # Statut global
        open_markets = sum(1 for m in market_status.values() if m['status'] == 'open')
        global_status = 'open' if open_markets > 0 else 'closed'
        
        return {
            'status': 'success',
            'data': {
                'global_status': global_status,
                'open_markets_count': open_markets,
                'markets': market_status,
                'server_time': datetime.utcnow().isoformat(),
                'timezone': 'UTC'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-collection/start")
async def start_data_collection(
    current_user: User = Depends(get_current_user)
):
    """
    Démarre la collecte de données temps réel (admin uniquement)
    """
    try:
        # Vérification des droits admin (simplifié)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Droits administrateur requis")
        
        # Le service se lance automatiquement, cette endpoint est pour le contrôle manuel
        return {
            'status': 'success',
            'message': 'Collecte de données démarrée',
            'active_connections': len(realtime_service.connected_websockets),
            'cached_symbols': len(realtime_service.data_cache),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_realtime_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Statistiques du service temps réel
    """
    try:
        stats = {
            'service_status': 'active',
            'connected_websockets': len(realtime_service.connected_websockets),
            'cached_symbols': len(realtime_service.data_cache),
            'watchlist_size': len(realtime_service.watchlist_etfs),
            'last_updates': {
                symbol: update_time.isoformat() 
                for symbol, update_time in realtime_service.last_update.items()
            },
            'data_sources': realtime_service.data_sources,
            'uptime': 'Service running',  # À implémenter avec un tracker de démarrage
        }
        
        return {
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))