"""
Endpoints WebSocket pour les notifications temps réel
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.websocket_manager import manager, websocket_service
from app.core.security import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """Récupérer l'utilisateur à partir du token WebSocket"""
    try:
        user_id = verify_token(token)
        if user_id:
            from app.models.user import User
            import uuid
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            return user
    except Exception as e:
        logger.error(f"Erreur vérification token WebSocket: {e}")
    return None

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Endpoint WebSocket principal pour les notifications temps réel
    Le token JWT est passé dans l'URL pour l'authentification
    """
    db = next(get_db())
    
    try:
        # Vérifier l'authentification
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Token invalide")
            return
        
        user_id = str(user.id)
        
        # Établir la connexion
        await manager.connect(websocket, user_id)
        
        # Boucle de traitement des messages
        while True:
            try:
                # Recevoir message du client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(message, user_id, websocket)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Format JSON invalide"
                }))
            except Exception as e:
                logger.error(f"Erreur WebSocket pour {user_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": str(e)
                }))
                
    except Exception as e:
        logger.error(f"Erreur connexion WebSocket: {e}")
        await websocket.close(code=4000, reason="Erreur serveur")
    finally:
        if 'user_id' in locals():
            manager.disconnect(websocket, user_id)

async def handle_websocket_message(message: dict, user_id: str, websocket: WebSocket):
    """Traiter les messages reçus du client"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Répondre au ping
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": websocket_service.manager.manager if hasattr(websocket_service.manager, 'manager') else None
        }))
        
    elif message_type == "subscribe":
        # S'abonner à un type de données
        subscription_type = message.get("subscription_type")
        if subscription_type:
            success = manager.subscribe(user_id, subscription_type)
            await websocket.send_text(json.dumps({
                "type": "subscription_response",
                "subscription_type": subscription_type,
                "success": success
            }))
    
    elif message_type == "unsubscribe":
        # Se désabonner
        subscription_type = message.get("subscription_type")
        if subscription_type:
            success = manager.unsubscribe(user_id, subscription_type)
            await websocket.send_text(json.dumps({
                "type": "unsubscription_response",
                "subscription_type": subscription_type,
                "success": success
            }))
    
    elif message_type == "get_stats":
        # Retourner les statistiques
        stats = manager.get_stats()
        await websocket.send_text(json.dumps({
            "type": "stats",
            "data": stats
        }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Type de message non reconnu: {message_type}"
        }))

@router.get("/ws/stats")
async def get_websocket_stats(current_user: User = Depends(get_current_user)):
    """Statistiques des connexions WebSocket (admin uniquement)"""
    # Pour l'instant, accessible à tous les utilisateurs authentifiés
    stats = manager.get_stats()
    return {
        "status": "success",
        "data": stats
    }

@router.post("/ws/broadcast")
async def broadcast_message(
    message: str,
    subscription_type: str,
    current_user: User = Depends(get_current_user)
):
    """Diffuser un message à tous les abonnés (admin uniquement)"""
    try:
        # Vérification basique (à améliorer avec un système de rôles)
        if not getattr(current_user, 'is_admin', False):
            # Pour l'instant, autoriser tous les utilisateurs
            pass
        
        await manager.broadcast_to_subscribers({
            "type": "admin_broadcast",
            "message": message,
            "from": current_user.full_name or current_user.email,
            "timestamp": websocket_service.manager.manager if hasattr(websocket_service.manager, 'manager') else None
        }, subscription_type)
        
        return {
            "status": "success",
            "message": "Message diffusé",
            "recipients": len(manager.subscriptions.get(subscription_type, set()))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))