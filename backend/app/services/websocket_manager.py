"""
Gestionnaire WebSocket pour les notifications et données temps réel
"""
import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gestionnaire des connexions WebSocket"""
    
    def __init__(self):
        # Stockage des connexions actives par utilisateur
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Abonnements par type de données
        self.subscriptions: Dict[str, Set[str]] = {
            "market_data": set(),
            "signals": set(), 
            "notifications": set(),
            "portfolio": set()
        }
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Nouvelle connexion WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"Nouvelle connexion WebSocket pour user {user_id}")
        
        # Envoyer message de bienvenue
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connexion WebSocket établie"
        }, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Déconnexion WebSocket"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Nettoyer si plus de connexions
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Désabonner de tous les services
                for subscription_type in self.subscriptions:
                    self.subscriptions[subscription_type].discard(user_id)
        
        logger.info(f"Déconnexion WebSocket pour user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Envoyer un message à un utilisateur spécifique"""
        if user_id in self.active_connections:
            message_str = json.dumps(message)
            
            # Envoyer à toutes les connexions de l'utilisateur
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Erreur envoi message à {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Nettoyer les connexions fermées
            for ws in disconnected:
                self.disconnect(ws, user_id)
    
    async def broadcast_to_subscribers(self, message: dict, subscription_type: str):
        """Diffuser un message à tous les abonnés d'un type"""
        if subscription_type not in self.subscriptions:
            return
        
        message_str = json.dumps(message)
        
        for user_id in self.subscriptions[subscription_type].copy():
            if user_id in self.active_connections:
                disconnected = []
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(message_str)
                    except Exception as e:
                        logger.error(f"Erreur broadcast à {user_id}: {e}")
                        disconnected.append(websocket)
                
                # Nettoyer connexions fermées
                for ws in disconnected:
                    self.disconnect(ws, user_id)
    
    def subscribe(self, user_id: str, subscription_type: str):
        """Abonner un utilisateur à un type de données"""
        if subscription_type in self.subscriptions:
            self.subscriptions[subscription_type].add(user_id)
            logger.info(f"User {user_id} abonné à {subscription_type}")
            return True
        return False
    
    def unsubscribe(self, user_id: str, subscription_type: str):
        """Désabonner un utilisateur"""
        if subscription_type in self.subscriptions:
            self.subscriptions[subscription_type].discard(user_id)
            logger.info(f"User {user_id} désabonné de {subscription_type}")
            return True
        return False
    
    def get_stats(self):
        """Statistiques des connexions"""
        return {
            "total_connections": sum(len(connections) for connections in self.active_connections.values()),
            "total_users": len(self.active_connections),
            "subscriptions": {
                sub_type: len(users) for sub_type, users in self.subscriptions.items()
            }
        }

# Instance globale
manager = ConnectionManager()

class WebSocketService:
    """Service pour les notifications WebSocket"""
    
    def __init__(self):
        self.manager = manager
    
    async def send_signal_notification(self, user_id: str, signal_data: dict):
        """Envoyer notification de nouveau signal"""
        message = {
            "type": "new_signal",
            "data": signal_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.manager.send_personal_message(message, user_id)
    
    async def send_market_update(self, market_data: dict):
        """Diffuser mise à jour de marché"""
        message = {
            "type": "market_update",
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.manager.broadcast_to_subscribers(message, "market_data")
    
    async def send_portfolio_update(self, user_id: str, portfolio_data: dict):
        """Envoyer mise à jour de portefeuille"""
        message = {
            "type": "portfolio_update",
            "data": portfolio_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.manager.send_personal_message(message, user_id)
    
    async def send_price_alert(self, user_id: str, alert_data: dict):
        """Envoyer alerte de prix"""
        message = {
            "type": "price_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        await self.manager.send_personal_message(message, user_id)
    
    async def send_system_notification(self, message_text: str, priority: str = "info"):
        """Envoyer notification système à tous"""
        message = {
            "type": "system_notification",
            "message": message_text,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Diffuser à tous les types d'abonnements
        for subscription_type in self.manager.subscriptions:
            await self.manager.broadcast_to_subscribers(message, subscription_type)

# Instance globale du service
websocket_service = WebSocketService()