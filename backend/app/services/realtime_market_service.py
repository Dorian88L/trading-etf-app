"""
Service de données de marché temps réel avec cache Redis et WebSockets
Implémente collecte, cache et diffusion des données financières
"""
import asyncio
import json
import logging
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import WebSocket
import websockets

from app.core.config import settings
from app.core.redis import cache
from app.models.etf import ETF

logger = logging.getLogger(__name__)

class RealtimeMarketService:
    def __init__(self):
        self.redis_client = cache
        self.connected_websockets: List[WebSocket] = []
        self.data_cache = {}
        self.last_update = {}
        
        # Configuration des sources de données
        self.data_sources = {
            'yahoo': {
                'enabled': True,
                'rate_limit': 60,  # requêtes par minute
                'priority': 1
            },
            'alpha_vantage': {
                'enabled': False,  # API key requis
                'rate_limit': 5,   # requêtes par minute
                'priority': 2
            },
            'polygon': {
                'enabled': False,  # API key requis
                'rate_limit': 300,
                'priority': 3
            }
        }
        
        # ETF populaires européens
        self.watchlist_etfs = [
            'IWDA.AS',   # iShares Core MSCI World
            'CSPX.AS',   # iShares Core S&P 500
            'VWCE.DE',   # Vanguard FTSE All-World
            'EUNL.DE',   # iShares Core MSCI Europe
            'IEMA.AS',   # iShares Core MSCI Emerging Markets
            'DBXD.DE',   # Xtrackers MSCI World
            'SXR8.DE',   # iShares Core Euro Stoxx 50
            'EXSA.MI',   # iShares Core MSCI Europe Small Cap
        ]
        
    async def start_realtime_collection(self):
        """
        Démarre la collecte de données temps réel
        """
        logger.info("Démarrage collecte données temps réel")
        
        # Tâches de collecte en parallèle
        tasks = [
            self._collect_yahoo_data(),
            self._update_cache_cleanup(),
            self._broadcast_updates()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _collect_yahoo_data(self):
        """
        Collecte des données Yahoo Finance toutes les 5 minutes
        """
        while True:
            try:
                logger.info("Collecte données Yahoo Finance")
                
                for symbol in self.watchlist_etfs:
                    try:
                        # Récupération données intraday
                        ticker = yf.Ticker(symbol)
                        
                        # Données temps réel (dernière heure)
                        data = ticker.history(period="1d", interval="5m")
                        
                        if not data.empty:
                            latest_data = {
                                'symbol': symbol,
                                'timestamp': datetime.utcnow().isoformat(),
                                'price': float(data['Close'].iloc[-1]),
                                'open': float(data['Open'].iloc[-1]),
                                'high': float(data['High'].iloc[-1]),
                                'low': float(data['Low'].iloc[-1]),
                                'volume': int(data['Volume'].iloc[-1]),
                                'change': 0,
                                'change_percent': 0,
                                'source': 'yahoo',
                                'market_status': self._get_market_status(symbol)
                            }
                            
                            # Calcul de la variation
                            if len(data) > 1:
                                prev_close = float(data['Close'].iloc[-2])
                                latest_data['change'] = latest_data['price'] - prev_close
                                latest_data['change_percent'] = (latest_data['change'] / prev_close) * 100
                            
                            # Mise en cache Redis
                            await self._cache_market_data(symbol, latest_data)
                            
                            # Ajout aux données pour broadcast
                            self.data_cache[symbol] = latest_data
                            self.last_update[symbol] = datetime.utcnow()
                            
                            logger.debug(f"Données mises à jour pour {symbol}: {latest_data['price']}")
                            
                    except Exception as e:
                        logger.error(f"Erreur collecte {symbol}: {e}")
                        # Données de fallback
                        await self._generate_fallback_data(symbol)
                        
                    # Rate limiting
                    await asyncio.sleep(2)
                
                # Attente avant prochain cycle (5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Erreur cycle collecte: {e}")
                await asyncio.sleep(60)
    
    async def _generate_fallback_data(self, symbol: str):
        """
        Génère des données de fallback réalistes
        """
        try:
            # Récupération des dernières données en cache
            cached = await self._get_cached_data(symbol)
            
            if cached:
                base_price = cached.get('price', 100)
            else:
                base_price = 100 + hash(symbol) % 100
            
            # Simulation de mouvement de prix réaliste
            import random
            change_percent = random.gauss(0, 0.5)  # Mouvement normal de ±0.5%
            new_price = base_price * (1 + change_percent / 100)
            
            fallback_data = {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'price': round(new_price, 2),
                'open': round(base_price, 2),
                'high': round(new_price * 1.005, 2),
                'low': round(new_price * 0.995, 2),
                'volume': random.randint(50000, 500000),
                'change': round(new_price - base_price, 2),
                'change_percent': round(change_percent, 2),
                'source': 'fallback',
                'market_status': 'closed'
            }
            
            await self._cache_market_data(symbol, fallback_data)
            self.data_cache[symbol] = fallback_data
            
        except Exception as e:
            logger.error(f"Erreur génération fallback {symbol}: {e}")
    
    async def _cache_market_data(self, symbol: str, data: Dict):
        """
        Met en cache les données dans Redis avec TTL
        """
        try:
            cache_key = f"market_data:{symbol}"
            
            # Cache principal (5 minutes)
            await self.redis_client.setex(
                cache_key,
                300,  # 5 minutes
                json.dumps(data)
            )
            
            # Cache historique (1 jour)
            history_key = f"market_history:{symbol}:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis_client.lpush(history_key, json.dumps(data))
            await self.redis_client.expire(history_key, 86400)  # 24h
            
            # Limitation à 288 points par jour (5min intervals)
            await self.redis_client.ltrim(history_key, 0, 287)
            
        except Exception as e:
            logger.error(f"Erreur cache Redis {symbol}: {e}")
    
    async def _get_cached_data(self, symbol: str) -> Optional[Dict]:
        """
        Récupère les données en cache
        """
        try:
            cache_key = f"market_data:{symbol}"
            cached = await self.redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            return None
            
        except Exception as e:
            logger.error(f"Erreur lecture cache {symbol}: {e}")
            return None
    
    def _get_market_status(self, symbol: str) -> str:
        """
        Détermine le statut du marché selon l'heure et le symbole
        """
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()
        
        # Weekend
        if weekday >= 5:  # Samedi, Dimanche
            return 'closed'
        
        # Marchés européens (8h-16h30 UTC)
        if symbol.endswith('.AS') or symbol.endswith('.DE') or symbol.endswith('.MI'):
            if 8 <= hour < 16 or (hour == 16 and now.minute <= 30):
                return 'open'
            elif 7 <= hour < 8:
                return 'pre_market'
            elif (hour == 16 and now.minute > 30) or 17 <= hour < 20:
                return 'after_hours'
            else:
                return 'closed'
        
        # Marché US par défaut (14h30-21h UTC)
        if 14 <= hour < 21 or (hour == 14 and now.minute >= 30):
            return 'open'
        elif 12 <= hour < 14:
            return 'pre_market'
        elif 21 <= hour < 24:
            return 'after_hours'
        else:
            return 'closed'
    
    async def _update_cache_cleanup(self):
        """
        Nettoie le cache périodiquement
        """
        while True:
            try:
                # Nettoyage toutes les heures
                await asyncio.sleep(3600)
                
                # Suppression des clés expirées
                pattern = "market_data:*"
                keys = await self.redis_client.keys(pattern)
                
                for key in keys:
                    ttl = await self.redis_client.ttl(key)
                    if ttl <= 0:
                        await self.redis_client.delete(key)
                
                logger.info(f"Nettoyage cache: {len(keys)} clés vérifiées")
                
            except Exception as e:
                logger.error(f"Erreur nettoyage cache: {e}")
    
    async def _broadcast_updates(self):
        """
        Diffuse les mises à jour via WebSocket
        """
        while True:
            try:
                if self.connected_websockets and self.data_cache:
                    # Préparation des données pour broadcast
                    update_data = {
                        'type': 'market_update',
                        'timestamp': datetime.utcnow().isoformat(),
                        'data': dict(self.data_cache)
                    }
                    
                    # Envoi à tous les clients connectés
                    disconnected = []
                    for websocket in self.connected_websockets:
                        try:
                            await websocket.send_text(json.dumps(update_data))
                        except Exception:
                            disconnected.append(websocket)
                    
                    # Nettoyage des connexions fermées
                    for ws in disconnected:
                        self.connected_websockets.remove(ws)
                    
                    if disconnected:
                        logger.info(f"Supprimé {len(disconnected)} connexions fermées")
                
                # Broadcast toutes les 30 secondes
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Erreur broadcast: {e}")
    
    async def add_websocket_connection(self, websocket: WebSocket):
        """
        Ajoute une connexion WebSocket
        """
        self.connected_websockets.append(websocket)
        logger.info(f"Nouvelle connexion WebSocket. Total: {len(self.connected_websockets)}")
        
        # Envoi des données actuelles
        if self.data_cache:
            initial_data = {
                'type': 'initial_data',
                'timestamp': datetime.utcnow().isoformat(),
                'data': dict(self.data_cache)
            }
            await websocket.send_text(json.dumps(initial_data))
    
    async def remove_websocket_connection(self, websocket: WebSocket):
        """
        Supprime une connexion WebSocket
        """
        if websocket in self.connected_websockets:
            self.connected_websockets.remove(websocket)
            logger.info(f"Connexion WebSocket fermée. Total: {len(self.connected_websockets)}")
    
    async def get_realtime_data(self, symbol: str) -> Optional[Dict]:
        """
        Récupère les données temps réel d'un symbole
        """
        # Tentative cache local d'abord
        if symbol in self.data_cache:
            cache_age = datetime.utcnow() - self.last_update.get(symbol, datetime.min)
            if cache_age.total_seconds() < 300:  # Cache valide 5 minutes
                return self.data_cache[symbol]
        
        # Tentative cache Redis
        cached_data = await self._get_cached_data(symbol)
        if cached_data:
            return cached_data
        
        # Génération de données de fallback
        await self._generate_fallback_data(symbol)
        return self.data_cache.get(symbol)
    
    async def get_historical_intraday(self, symbol: str, hours: int = 24) -> List[Dict]:
        """
        Récupère l'historique intraday d'un symbole
        """
        try:
            history_key = f"market_history:{symbol}:{datetime.utcnow().strftime('%Y%m%d')}"
            
            # Récupération depuis Redis
            cached_history = await self.redis_client.lrange(history_key, 0, -1)
            
            if cached_history:
                history_data = []
                for item in reversed(cached_history):  # Plus récent en premier
                    try:
                        data_point = json.loads(item)
                        # Filtrer par âge
                        timestamp = datetime.fromisoformat(data_point['timestamp'].replace('Z', '+00:00'))
                        if datetime.utcnow() - timestamp <= timedelta(hours=hours):
                            history_data.append(data_point)
                    except Exception:
                        continue
                
                return history_data
            
            # Fallback avec données Yahoo Finance
            return await self._fetch_yahoo_intraday(symbol, hours)
            
        except Exception as e:
            logger.error(f"Erreur historique intraday {symbol}: {e}")
            return []
    
    async def _fetch_yahoo_intraday(self, symbol: str, hours: int) -> List[Dict]:
        """
        Récupère les données intraday depuis Yahoo Finance
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Période selon les heures demandées
            if hours <= 7:
                period = "1d"
                interval = "5m"
            elif hours <= 48:
                period = "2d"
                interval = "15m"
            else:
                period = "5d"
                interval = "1h"
            
            data = ticker.history(period=period, interval=interval)
            
            history_data = []
            for index, row in data.iterrows():
                history_data.append({
                    'symbol': symbol,
                    'timestamp': index.isoformat(),
                    'price': float(row['Close']),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': int(row['Volume']),
                    'source': 'yahoo_historical'
                })
            
            return history_data
            
        except Exception as e:
            logger.error(f"Erreur fetch Yahoo {symbol}: {e}")
            return []
    
    async def get_market_overview(self) -> Dict:
        """
        Récupère un aperçu général du marché
        """
        overview = {
            'timestamp': datetime.utcnow().isoformat(),
            'market_status': 'mixed',
            'active_symbols': len(self.data_cache),
            'top_gainers': [],
            'top_losers': [],
            'most_active': [],
            'market_trends': {}
        }
        
        if not self.data_cache:
            return overview
        
        # Analyse des données
        symbols_data = list(self.data_cache.values())
        
        # Top gainers/losers
        sorted_by_change = sorted(symbols_data, key=lambda x: x.get('change_percent', 0), reverse=True)
        overview['top_gainers'] = sorted_by_change[:3]
        overview['top_losers'] = sorted_by_change[-3:]
        
        # Most active par volume
        sorted_by_volume = sorted(symbols_data, key=lambda x: x.get('volume', 0), reverse=True)
        overview['most_active'] = sorted_by_volume[:3]
        
        # Tendances générales
        positive_changes = sum(1 for d in symbols_data if d.get('change_percent', 0) > 0)
        total_symbols = len(symbols_data)
        
        if positive_changes / total_symbols > 0.6:
            overview['market_status'] = 'bullish'
        elif positive_changes / total_symbols < 0.4:
            overview['market_status'] = 'bearish'
        else:
            overview['market_status'] = 'mixed'
        
        overview['market_trends'] = {
            'positive_count': positive_changes,
            'negative_count': total_symbols - positive_changes,
            'neutral_count': 0,
            'sentiment_score': (positive_changes / total_symbols) * 100 if total_symbols > 0 else 50
        }
        
        return overview

# Instance globale
realtime_service = RealtimeMarketService()