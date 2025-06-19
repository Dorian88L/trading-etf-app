"""
Service ETF avec cache automatique en base de données
Optimise les performances en évitant les requêtes répétées
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.database import SessionLocal
from app.models.etf import ETF, MarketData
from app.services.multi_source_etf_data import MultiSourceETFDataService, ETFDataPoint
from app.services.etf_scraping_service import ETFScrapingService

logger = logging.getLogger(__name__)

class CachedETFService:
    """Service ETF avec cache intelligent en base de données"""
    
    def __init__(self):
        self.api_service = MultiSourceETFDataService()
        self.scraping_service = ETFScrapingService()
        self.cache_duration_minutes = 5  # Cache de 5 minutes pour temps réel
        
    def _is_data_fresh(self, last_update: datetime) -> bool:
        """Vérifie si les données sont encore fraîches"""
        return (datetime.now() - last_update).total_seconds() < (self.cache_duration_minutes * 60)
    
    async def get_cached_etf_data(self, symbol: str, db: Session) -> Optional[ETFDataPoint]:
        """Récupère les données ETF depuis le cache ou les sources externes"""
        
        # 1. Chercher d'abord les ETF dans le catalogue
        etf_record = db.query(ETF).filter(ETF.symbol == symbol).first()
        if not etf_record:
            logger.warning(f"ETF {symbol} non trouvé dans le catalogue")
            return None
        
        # 2. Vérifier les données en cache (MarketData récente)
        cached_data = db.query(MarketData).filter(
            MarketData.etf_isin == etf_record.isin
        ).order_by(desc(MarketData.time)).first()
        
        if cached_data and self._is_data_fresh(cached_data.time):
            logger.info(f"Données fraîches trouvées en cache pour {symbol}")
            return self._convert_cached_to_datapoint(etf_record, cached_data)
        
        # 3. Données expirées ou inexistantes, récupérer depuis les sources
        logger.info(f"Récupération de nouvelles données pour {symbol}")
        
        # Essayer d'abord les APIs
        fresh_data = await self.api_service.get_etf_data(symbol)
        
        # Si les APIs échouent, utiliser le scraping
        if not fresh_data:
            logger.info(f"APIs échouées pour {symbol}, tentative de scraping")
            scraped_data = await self.scraping_service.scrape_etf_data(etf_record.isin)
            
            if scraped_data:
                fresh_data = ETFDataPoint(
                    symbol=symbol,
                    isin=etf_record.isin,
                    name=scraped_data.name,
                    current_price=scraped_data.current_price,
                    change=scraped_data.change,
                    change_percent=scraped_data.change_percent,
                    volume=scraped_data.volume or 0,
                    market_cap=None,
                    currency=scraped_data.currency,
                    exchange=scraped_data.exchange,
                    sector=etf_record.sector,
                    last_update=scraped_data.last_update,
                    source='scraping_realtime',
                    confidence_score=0.95,
                    data_quality='scraped_realtime',
                    reliability_icon='🌐'
                )
        
        # 4. Sauvegarder en cache si on a récupéré des données
        if fresh_data:
            self._save_to_cache(fresh_data, db)
            return fresh_data
        
        # 5. Aucune donnée disponible
        logger.error(f"Impossible de récupérer des données pour {symbol}")
        return None
    
    def _convert_cached_to_datapoint(self, etf: ETF, market_data: MarketData) -> ETFDataPoint:
        """Convertit les données en cache en ETFDataPoint"""
        
        # Calculer la variation
        change = float(market_data.close_price - market_data.open_price)
        change_percent = (change / float(market_data.open_price)) * 100 if market_data.open_price > 0 else 0
        
        return ETFDataPoint(
            symbol=etf.symbol if hasattr(etf, 'symbol') else etf.isin,
            isin=etf.isin,
            name=etf.name,
            current_price=float(market_data.close_price),
            change=change,
            change_percent=change_percent,
            volume=int(market_data.volume) if market_data.volume else 0,
            market_cap=etf.aum,
            currency=etf.currency,
            exchange=etf.exchange,
            sector=etf.sector,
            last_update=market_data.time,
            source='database_cache',
            confidence_score=1.0,
            data_quality='cached',
            reliability_icon='💾'
        )
    
    def _save_to_cache(self, data: ETFDataPoint, db: Session):
        """Sauvegarde les données en cache dans MarketData"""
        try:
            # Chercher l'ETF par ISIN
            etf = db.query(ETF).filter(ETF.isin == data.isin).first()
            if not etf:
                logger.warning(f"ETF {data.isin} non trouvé pour sauvegarde cache")
                return
            
            # Créer un nouvel enregistrement MarketData
            market_data = MarketData(
                time=data.last_update,
                etf_isin=data.isin,
                open_price=data.current_price - data.change,  # Prix d'ouverture estimé
                high_price=data.current_price,  # Pour simplifier
                low_price=data.current_price,   # Pour simplifier  
                close_price=data.current_price,
                volume=data.volume,
                nav=data.current_price  # Net Asset Value = prix actuel
            )
            
            db.add(market_data)
            db.commit()
            logger.info(f"Données sauvegardées en cache pour {data.symbol}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache pour {data.symbol}: {e}")
            db.rollback()
    
    async def get_all_cached_etfs(self, db: Session) -> List[ETFDataPoint]:
        """Récupère tous les ETFs avec cache intelligent"""
        
        # Récupérer tous les ETFs du catalogue
        all_etfs = db.query(ETF).all()
        
        tasks = []
        for etf in all_etfs:
            # Utiliser le meilleur symbole disponible
            symbol = getattr(etf, 'symbol', etf.isin)
            tasks.append(self.get_cached_etf_data(symbol, db))
        
        # Exécuter toutes les requêtes en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les résultats valides
        valid_results = []
        for result in results:
            if isinstance(result, ETFDataPoint):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur récupération ETF: {result}")
        
        logger.info(f"Récupéré {len(valid_results)}/{len(all_etfs)} ETFs avec succès")
        return valid_results
    
    async def force_refresh_all(self, db: Session) -> Dict[str, str]:
        """Force le rafraîchissement de tous les ETFs"""
        
        logger.info("🔄 Début du rafraîchissement forcé de tous les ETFs")
        
        all_etfs = db.query(ETF).all()
        results = {
            'total': len(all_etfs),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for etf in all_etfs:
            try:
                symbol = getattr(etf, 'symbol', etf.isin)
                
                # Supprimer les données en cache pour forcer le refresh
                db.query(MarketData).filter(
                    MarketData.etf_isin == etf.isin
                ).delete()
                
                # Récupérer de nouvelles données
                fresh_data = await self.get_cached_etf_data(symbol, db)
                
                if fresh_data:
                    results['success'] += 1
                    results['details'].append(f"✅ {symbol}: {fresh_data.current_price} {fresh_data.currency}")
                else:
                    results['failed'] += 1
                    results['details'].append(f"❌ {symbol}: Aucune donnée")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"❌ {symbol}: Erreur {e}")
        
        logger.info(f"🎉 Rafraîchissement terminé: {results['success']} succès, {results['failed']} échecs")
        return results

def get_cached_etf_service() -> CachedETFService:
    """Factory function pour le service ETF en cache"""
    return CachedETFService()