"""
Service intelligent de gestion des données de marché
Vérifie d'abord en base de données avant les appels API pour optimiser l'utilisation des clés
Sauvegarde automatiquement les nouvelles données pour éviter les doublons
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.core.database import get_db
from app.models.etf import MarketData, ETF, TechnicalIndicators
from app.services.real_market_data import RealMarketDataService, RealMarketDataPoint
from app.services.external_apis import ExternalAPIService
from app.core.cache import cache

logger = logging.getLogger(__name__)

class SmartMarketDataService:
    """Service intelligent de données de marché avec cache en base de données"""
    
    def __init__(self):
        self.real_market_service = RealMarketDataService()
        self.external_api_service = ExternalAPIService()
    
    async def get_historical_data_smart(
        self, 
        symbol: str, 
        period: str = "1y",
        db: Session = None
    ) -> List[Dict]:
        """
        Récupère les données historiques en vérifiant d'abord la base de données
        Args:
            symbol: Symbole de l'ETF (ex: "IWDA.L")
            period: Période (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            db: Session de base de données
        """
        if not db:
            db = next(get_db())
        
        try:
            # 1. Convertir la période en dates
            end_date = datetime.now().date()
            start_date = self._period_to_start_date(period, end_date)
            
            logger.info(f"Récupération données historiques pour {symbol} de {start_date} à {end_date}")
            
            # 2. Vérifier quelles données existent déjà en base
            existing_data = await self._get_existing_market_data(db, symbol, start_date, end_date)
            
            # 3. Identifier les dates manquantes
            missing_dates = self._find_missing_dates(start_date, end_date, existing_data)
            
            if missing_dates:
                logger.info(f"{len(missing_dates)} dates manquantes pour {symbol}, appel API nécessaire")
                # 4. Récupérer les données manquantes via API
                new_data = await self._fetch_and_save_historical_data(db, symbol, missing_dates)
                
                # 5. Combiner avec les données existantes
                all_data = existing_data + new_data
            else:
                logger.info(f"Toutes les données pour {symbol} sont déjà en cache")
                all_data = existing_data
            
            # 6. Trier et formater les données
            formatted_data = self._format_historical_data(all_data)
            
            # 7. Cache les résultats
            cache_key = f"historical:{symbol}:{period}"
            cache.set(cache_key, formatted_data, 300)  # 5 minutes
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données historiques pour {symbol}: {e}")
            # Fallback sur l'ancien service
            return await self._fallback_historical_data(symbol, period)
    
    async def get_realtime_data_smart(
        self, 
        symbol: str,
        db: Session = None
    ) -> Optional[Dict]:
        """
        Récupère les données temps réel en vérifiant d'abord si on a des données récentes
        """
        if not db:
            db = next(get_db())
        
        try:
            # 1. Vérifier les données récentes (dernière heure)
            recent_data = await self._get_recent_market_data(db, symbol, hours=1)
            
            if recent_data:
                logger.info(f"Données récentes trouvées pour {symbol}")
                return self._format_realtime_data(recent_data)
            
            # 2. Pas de données récentes, appel API nécessaire
            logger.info(f"Appel API nécessaire pour données temps réel de {symbol}")
            new_data = await self._fetch_and_save_realtime_data(db, symbol)
            
            if new_data:
                return self._format_realtime_data(new_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données temps réel pour {symbol}: {e}")
            return None
    
    async def get_multiple_realtime_smart(
        self,
        symbols: List[str],
        db: Session = None
    ) -> Dict[str, Dict]:
        """
        Récupère les données temps réel pour plusieurs symboles intelligemment
        """
        if not db:
            db = next(get_db())
        
        results = {}
        symbols_need_api = []
        
        # 1. Vérifier quels symboles ont des données récentes
        for symbol in symbols:
            recent_data = await self._get_recent_market_data(db, symbol, hours=1)
            if recent_data:
                results[symbol] = self._format_realtime_data(recent_data)
            else:
                symbols_need_api.append(symbol)
        
        # 2. Faire un appel API groupé pour les symboles manquants
        if symbols_need_api:
            logger.info(f"Appel API pour {len(symbols_need_api)} symboles: {symbols_need_api}")
            new_data_batch = await self._fetch_and_save_multiple_realtime(db, symbols_need_api)
            results.update(new_data_batch)
        
        return results
    
    # Méthodes privées utilitaires
    
    def _period_to_start_date(self, period: str, end_date: date) -> date:
        """Convertit une période en date de début"""
        if period == "1d":
            return end_date - timedelta(days=1)
        elif period == "5d":
            return end_date - timedelta(days=5)
        elif period == "1mo":
            return end_date - timedelta(days=30)
        elif period == "3mo":
            return end_date - timedelta(days=90)
        elif period == "6mo":
            return end_date - timedelta(days=180)
        elif period == "1y":
            return end_date - timedelta(days=365)
        elif period == "2y":
            return end_date - timedelta(days=730)
        elif period == "5y":
            return end_date - timedelta(days=1825)
        elif period == "10y":
            return end_date - timedelta(days=3650)
        elif period == "ytd":
            return date(end_date.year, 1, 1)
        elif period == "max":
            return date(2000, 1, 1)  # Date arbitraire très ancienne
        else:
            return end_date - timedelta(days=365)  # Par défaut 1 an
    
    async def _get_existing_market_data(
        self, 
        db: Session, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[MarketData]:
        """Récupère les données existantes en base pour la période donnée"""
        try:
            # Trouver l'ETF par symbole (approximation)
            etf = db.query(ETF).filter(ETF.name.ilike(f"%{symbol}%")).first()
            if not etf:
                # Essayer de trouver par le symbole dans le nom ou créer un placeholder
                logger.warning(f"ETF non trouvé pour le symbole {symbol}")
                return []
            
            # Récupérer les données de marché existantes
            market_data = db.query(MarketData).filter(
                and_(
                    MarketData.etf_isin == etf.isin,
                    MarketData.time >= start_date,
                    MarketData.time <= end_date
                )
            ).order_by(MarketData.time).all()
            
            logger.info(f"Trouvé {len(market_data)} enregistrements existants pour {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données existantes: {e}")
            return []
    
    async def _get_recent_market_data(
        self, 
        db: Session, 
        symbol: str, 
        hours: int = 1
    ) -> Optional[MarketData]:
        """Récupère les données les plus récentes pour un symbole"""
        try:
            # Trouver l'ETF par symbole
            etf = db.query(ETF).filter(ETF.name.ilike(f"%{symbol}%")).first()
            if not etf:
                return None
            
            # Récupérer la donnée la plus récente dans la période
            recent_time = datetime.now() - timedelta(hours=hours)
            market_data = db.query(MarketData).filter(
                and_(
                    MarketData.etf_isin == etf.isin,
                    MarketData.time >= recent_time
                )
            ).order_by(desc(MarketData.time)).first()
            
            return market_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données récentes: {e}")
            return None
    
    def _find_missing_dates(
        self, 
        start_date: date, 
        end_date: date, 
        existing_data: List[MarketData]
    ) -> List[date]:
        """Identifie les dates manquantes dans les données existantes"""
        existing_dates = set()
        for data in existing_data:
            if isinstance(data.time, datetime):
                existing_dates.add(data.time.date())
            else:
                existing_dates.add(data.time)
        
        # Générer toutes les dates dans la période (jours ouvrables uniquement)
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            # Exclure weekends (samedi=5, dimanche=6)
            if current_date.weekday() < 5:
                all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Trouver les dates manquantes
        missing_dates = [d for d in all_dates if d not in existing_dates]
        return missing_dates
    
    async def _fetch_and_save_historical_data(
        self, 
        db: Session, 
        symbol: str, 
        missing_dates: List[date]
    ) -> List[MarketData]:
        """Récupère les données manquantes via API et les sauvegarde"""
        try:
            # Calculer la période nécessaire pour couvrir toutes les dates manquantes
            if not missing_dates:
                return []
            
            start_date = min(missing_dates)
            end_date = max(missing_dates)
            
            # Appel API pour récupérer les données
            historical_data = self.real_market_service.get_historical_data(
                symbol, 
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if not historical_data:
                logger.warning(f"Aucune donnée reçue de l'API pour {symbol}")
                return []
            
            # Sauvegarder en base
            saved_data = await self._save_historical_data_to_db(db, symbol, historical_data)
            
            logger.info(f"Sauvegardé {len(saved_data)} nouveaux enregistrements pour {symbol}")
            return saved_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération et sauvegarde des données: {e}")
            return []
    
    async def _fetch_and_save_realtime_data(
        self, 
        db: Session, 
        symbol: str
    ) -> Optional[MarketData]:
        """Récupère les données temps réel via API et les sauvegarde"""
        try:
            # Appel API pour données temps réel
            realtime_data = self.real_market_service.get_real_etf_data(symbol)
            
            if not realtime_data:
                logger.warning(f"Aucune donnée temps réel reçue pour {symbol}")
                return None
            
            # Sauvegarder en base
            saved_data = await self._save_realtime_data_to_db(db, symbol, realtime_data)
            
            logger.info(f"Sauvegardé nouvelle donnée temps réel pour {symbol}")
            return saved_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération et sauvegarde temps réel: {e}")
            return None
    
    async def _fetch_and_save_multiple_realtime(
        self, 
        db: Session, 
        symbols: List[str]
    ) -> Dict[str, Dict]:
        """Récupère les données temps réel pour plusieurs symboles"""
        results = {}
        
        # Pour optimiser, on pourrait faire des appels parallèles
        tasks = [self._fetch_and_save_realtime_data(db, symbol) for symbol in symbols]
        saved_data_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, saved_data in zip(symbols, saved_data_list):
            if isinstance(saved_data, Exception):
                logger.error(f"Erreur pour {symbol}: {saved_data}")
                continue
            
            if saved_data:
                results[symbol] = self._format_realtime_data(saved_data)
        
        return results
    
    async def _save_historical_data_to_db(
        self, 
        db: Session, 
        symbol: str, 
        historical_data: List[RealMarketDataPoint]
    ) -> List[MarketData]:
        """Sauvegarde les données historiques en base avec prévention des doublons"""
        try:
            # Trouver ou créer l'ETF
            etf = await self._get_or_create_etf(db, symbol)
            if not etf:
                return []
            
            saved_records = []
            
            for data_point in historical_data:
                # Vérifier si la donnée existe déjà
                existing = db.query(MarketData).filter(
                    and_(
                        MarketData.etf_isin == etf.isin,
                        MarketData.time == data_point.timestamp.date()
                    )
                ).first()
                
                if existing:
                    # Mettre à jour si nécessaire
                    existing.open_price = data_point.open_price
                    existing.high_price = data_point.high_price
                    existing.low_price = data_point.low_price
                    existing.close_price = data_point.close_price
                    existing.volume = data_point.volume
                    saved_records.append(existing)
                else:
                    # Créer nouveau record
                    new_record = MarketData(
                        time=data_point.timestamp.date(),
                        etf_isin=etf.isin,
                        open_price=data_point.open_price,
                        high_price=data_point.high_price,
                        low_price=data_point.low_price,
                        close_price=data_point.close_price,
                        volume=data_point.volume
                    )
                    db.add(new_record)
                    saved_records.append(new_record)
            
            db.commit()
            return saved_records
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données historiques: {e}")
            db.rollback()
            return []
    
    async def _save_realtime_data_to_db(
        self, 
        db: Session, 
        symbol: str, 
        realtime_data
    ) -> Optional[MarketData]:
        """Sauvegarde les données temps réel en base"""
        try:
            # Trouver ou créer l'ETF
            etf = await self._get_or_create_etf(db, symbol)
            if not etf:
                return None
            
            today = datetime.now().date()
            
            # Vérifier si on a déjà une donnée pour aujourd'hui
            existing = db.query(MarketData).filter(
                and_(
                    MarketData.etf_isin == etf.isin,
                    MarketData.time == today
                )
            ).first()
            
            if existing:
                # Mettre à jour avec les dernières données
                existing.close_price = realtime_data.current_price
                existing.volume = realtime_data.volume
                # On pourrait aussi mettre à jour high/low si approprié
                db.commit()
                return existing
            else:
                # Créer nouveau record avec les données temps réel
                new_record = MarketData(
                    time=today,
                    etf_isin=etf.isin,
                    open_price=realtime_data.current_price,  # Approximation
                    high_price=realtime_data.current_price,
                    low_price=realtime_data.current_price,
                    close_price=realtime_data.current_price,
                    volume=realtime_data.volume
                )
                db.add(new_record)
                db.commit()
                return new_record
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données temps réel: {e}")
            db.rollback()
            return None
    
    async def _get_or_create_etf(self, db: Session, symbol: str) -> Optional[ETF]:
        """Trouve ou crée un ETF basé sur le symbole"""
        try:
            # D'abord essayer de trouver par le mapping des ETFs connus
            etf_info = self.real_market_service.EUROPEAN_ETFS.get(symbol)
            
            if etf_info:
                # Chercher par ISIN d'abord
                etf = db.query(ETF).filter(ETF.isin == etf_info['isin']).first()
                if etf:
                    return etf
                
                # Créer si n'existe pas
                new_etf = ETF(
                    isin=etf_info['isin'],
                    name=etf_info['name'],
                    sector=etf_info.get('sector', 'Unknown'),
                    currency=etf_info.get('currency', 'EUR'),
                    exchange=etf_info.get('exchange', 'Unknown')
                )
                db.add(new_etf)
                db.commit()
                return new_etf
            
            # Fallback: essayer de trouver par nom contenant le symbole
            etf = db.query(ETF).filter(ETF.name.ilike(f"%{symbol}%")).first()
            return etf
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche/création de l'ETF pour {symbol}: {e}")
            return None
    
    def _format_historical_data(self, market_data: List[MarketData]) -> List[Dict]:
        """Formate les données de marché pour l'API"""
        formatted_data = []
        for data in market_data:
            formatted_data.append({
                'date': data.time.isoformat() if isinstance(data.time, (date, datetime)) else str(data.time),
                'open': float(data.open_price) if data.open_price else None,
                'high': float(data.high_price) if data.high_price else None,
                'low': float(data.low_price) if data.low_price else None,
                'close': float(data.close_price) if data.close_price else None,
                'volume': int(data.volume) if data.volume else 0,
                'adj_close': float(data.close_price) if data.close_price else None
            })
        
        return sorted(formatted_data, key=lambda x: x['date'])
    
    def _format_realtime_data(self, market_data: MarketData) -> Dict:
        """Formate les données temps réel pour l'API"""
        return {
            'symbol': 'Unknown',  # On pourrait enrichir avec le symbole
            'price': float(market_data.close_price) if market_data.close_price else None,
            'change': 0.0,  # On pourrait calculer vs jour précédent
            'change_percent': 0.0,
            'volume': int(market_data.volume) if market_data.volume else 0,
            'last_update': market_data.time.isoformat() if isinstance(market_data.time, (date, datetime)) else str(market_data.time)
        }
    
    async def _fallback_historical_data(self, symbol: str, period: str) -> List[Dict]:
        """Fallback sur l'ancien service en cas d'erreur"""
        try:
            return self.real_market_service.get_historical_data(symbol, period)
        except Exception as e:
            logger.error(f"Erreur fallback pour {symbol}: {e}")
            return []


# Instance globale du service
smart_market_service = SmartMarketDataService()

def get_smart_market_data_service() -> SmartMarketDataService:
    """Dependency injection pour le service intelligent"""
    return smart_market_service