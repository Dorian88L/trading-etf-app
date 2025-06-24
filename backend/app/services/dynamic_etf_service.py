"""
Service dynamique pour les données ETF
Récupère les ETFs depuis la base de données et mappe les symboles de trading
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass

from app.core.database import SessionLocal
from app.models.etf import ETF, ETFSymbolMapping, ETFDisplayConfig
from app.services.multi_source_etf_data import MultiSourceETFDataService, ETFDataPoint, DataSource
from app.services.etf_scraping_service import get_etf_scraping_service, ETFScrapingService

logger = logging.getLogger(__name__)

@dataclass
class ETFConfig:
    """Configuration d'un ETF avec ses symboles de trading"""
    isin: str
    name: str
    sector: str
    currency: str
    exchange: str
    ter: Optional[float]
    aum: Optional[int]
    primary_trading_symbol: Optional[str]  # Symbole principal pour les données temps réel
    alternative_symbols: List[str]  # Symboles alternatifs
    is_visible_dashboard: bool
    is_visible_etf_list: bool
    display_order: float

class DynamicETFService:
    """Service dynamique pour les données ETF basé sur la configuration en base"""
    
    def __init__(self):
        self.market_data_service = MultiSourceETFDataService()
        self.scraping_service = get_etf_scraping_service()
        self._etf_configs: Optional[List[ETFConfig]] = None
        self._last_refresh = None
        self.cache_duration = 300  # 5 minutes
        self.prefer_scraping = True  # Préférer le scraping aux APIs
    
    def get_etf_configs_from_database(self) -> List[ETFConfig]:
        """Récupère la configuration des ETFs depuis la base de données"""
        db = SessionLocal()
        try:
            # Récupérer tous les ETFs avec leurs configurations
            etfs = db.query(ETF).join(ETFDisplayConfig, ETF.isin == ETFDisplayConfig.etf_isin, isouter=True).all()
            
            configs = []
            for etf in etfs:
                # Récupérer les mappings de symboles
                symbol_mappings = db.query(ETFSymbolMapping).filter(
                    ETFSymbolMapping.etf_isin == etf.isin,
                    ETFSymbolMapping.is_active == True
                ).all()
                
                # Trouver le symbole principal
                primary_symbol = None
                alternative_symbols = []
                
                for mapping in symbol_mappings:
                    if mapping.is_primary:
                        primary_symbol = mapping.trading_symbol
                    else:
                        alternative_symbols.append(mapping.trading_symbol)
                
                # Configuration d'affichage
                display_config = etf.display_config if hasattr(etf, 'display_config') and etf.display_config else None
                
                config = ETFConfig(
                    isin=etf.isin,
                    name=etf.name,
                    sector=etf.sector or "Unknown",
                    currency=etf.currency,
                    exchange=etf.exchange or "Unknown",
                    ter=float(etf.ter) if etf.ter else None,
                    aum=etf.aum,
                    primary_trading_symbol=primary_symbol,
                    alternative_symbols=alternative_symbols,
                    is_visible_dashboard=display_config.is_visible_on_dashboard if display_config else True,
                    is_visible_etf_list=display_config.is_visible_on_etf_list if display_config else True,
                    display_order=float(display_config.display_order) if display_config and display_config.display_order else 0
                )
                configs.append(config)
            
            logger.info(f"Configuration récupérée pour {len(configs)} ETFs depuis la base de données")
            return configs
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des configurations ETF: {e}")
            return []
        finally:
            db.close()
    
    def get_etf_configs(self, force_refresh: bool = False) -> List[ETFConfig]:
        """Récupère les configurations ETF avec cache"""
        now = datetime.now()
        
        if (force_refresh or 
            self._etf_configs is None or 
            self._last_refresh is None or 
            (now - self._last_refresh).total_seconds() > self.cache_duration):
            
            self._etf_configs = self.get_etf_configs_from_database()
            self._last_refresh = now
            logger.info("Configurations ETF rafraîchies depuis la base de données")
        
        return self._etf_configs or []
    
    def get_visible_etfs_for_dashboard(self) -> List[ETFConfig]:
        """Récupère les ETFs visibles sur le dashboard"""
        configs = self.get_etf_configs()
        visible = [config for config in configs if config.is_visible_dashboard]
        # Trier par ordre d'affichage puis par nom
        visible.sort(key=lambda x: (x.display_order, x.name))
        return visible
    
    def get_visible_etfs_for_list(self) -> List[ETFConfig]:
        """Récupère les ETFs visibles sur la page ETF list"""
        configs = self.get_etf_configs()
        visible = [config for config in configs if config.is_visible_etf_list]
        # Trier par ordre d'affichage puis par nom
        visible.sort(key=lambda x: (x.display_order, x.name))
        return visible
    
    async def get_realtime_data_for_etf(self, etf_config: ETFConfig) -> Optional[ETFDataPoint]:
        """Récupère les données temps réel pour un ETF spécifique"""
        
        # Stratégie 1: Scraping (prioritaire pour économiser les APIs)
        if self.prefer_scraping:
            try:
                scraped_data = await self.scraping_service.scrape_etf_data(etf_config.isin)
                if scraped_data and scraped_data.current_price > 0:
                    # Convertir en ETFDataPoint
                    etf_info = {
                        'sector': etf_config.sector,
                        'exchange': etf_config.exchange
                    }
                    data = self.scraping_service.convert_to_etf_data_point(scraped_data, etf_info)
                    logger.info(f"Données scrapées pour {etf_config.name}: {data.current_price} {data.currency}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur scraping pour {etf_config.name}: {e}")
        
        # Stratégie 2: APIs (fallback) - Essayer d'abord avec le symbole principal
        if etf_config.primary_trading_symbol:
            try:
                data = await self.market_data_service.get_etf_data(etf_config.primary_trading_symbol)
                if data and data.current_price > 0:
                    # Mettre à jour les informations ETF avec celles de la base
                    data.isin = etf_config.isin
                    data.name = etf_config.name
                    data.sector = etf_config.sector
                    data.exchange = etf_config.exchange
                    logger.info(f"Données API pour {etf_config.name}: {data.current_price} {data.currency}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur avec symbole principal {etf_config.primary_trading_symbol}: {e}")
        
        # Stratégie 3: Essayer avec les symboles alternatifs
        for alt_symbol in etf_config.alternative_symbols:
            try:
                data = await self.market_data_service.get_etf_data(alt_symbol)
                if data and data.current_price > 0:
                    # Mettre à jour les informations ETF
                    data.isin = etf_config.isin
                    data.name = etf_config.name
                    data.sector = etf_config.sector
                    data.exchange = etf_config.exchange
                    logger.info(f"Données API alt pour {etf_config.name}: {data.current_price} {data.currency}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur avec symbole alternatif {alt_symbol}: {e}")
                continue
        
        logger.warning(f"Aucune donnée temps réel trouvée pour {etf_config.name} ({etf_config.isin})")
        return None
    
    async def get_all_realtime_data_for_dashboard(self) -> List[ETFDataPoint]:
        """Récupère toutes les données temps réel pour le dashboard"""
        visible_etfs = self.get_visible_etfs_for_dashboard()
        
        tasks = []
        for etf_config in visible_etfs:
            tasks.append(self.get_realtime_data_for_etf(etf_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, ETFDataPoint):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur pour ETF {visible_etfs[i].name}: {result}")
        
        logger.info(f"Données temps réel récupérées pour {len(valid_results)}/{len(visible_etfs)} ETFs du dashboard")
        return valid_results
    
    async def get_all_realtime_data_for_etf_list(self) -> List[ETFDataPoint]:
        """Récupère toutes les données temps réel pour la page ETF list"""
        visible_etfs = self.get_visible_etfs_for_list()
        
        tasks = []
        for etf_config in visible_etfs:
            tasks.append(self.get_realtime_data_for_etf(etf_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        scraped_data_to_save = []
        
        for i, result in enumerate(results):
            if isinstance(result, ETFDataPoint):
                valid_results.append(result)
                
                # Si c'est une donnée scrapée, la préparer pour sauvegarde
                if result.source in [DataSource.CACHE, DataSource.HYBRID] and 'SCRAPED_' in result.symbol:
                    scraped_data_to_save.append(result)
                    
            elif isinstance(result, Exception):
                logger.error(f"Erreur pour ETF {visible_etfs[i].name}: {result}")
        
        # Sauvegarder les données scrapées en base
        if scraped_data_to_save and self.prefer_scraping:
            try:
                # Convertir ETFDataPoint vers ScrapedETFData pour la sauvegarde
                from app.services.etf_scraping_service import ScrapedETFData
                scraped_for_db = []
                
                for etf_data in scraped_data_to_save:
                    scraped_for_db.append(ScrapedETFData(
                        isin=etf_data.isin,
                        name=etf_data.name,
                        current_price=etf_data.current_price,
                        change=etf_data.change,
                        change_percent=etf_data.change_percent,
                        volume=etf_data.volume,
                        currency=etf_data.currency,
                        exchange=etf_data.exchange,
                        last_update=etf_data.last_update,
                        source="scraping"
                    ))
                
                await self.scraping_service.save_to_database(scraped_for_db)
                logger.info(f"Sauvegardé {len(scraped_for_db)} données scrapées en base")
                
            except Exception as e:
                logger.error(f"Erreur sauvegarde données scrapées: {e}")
        
        logger.info(f"Données temps réel récupérées pour {len(valid_results)}/{len(visible_etfs)} ETFs de la liste")
        return valid_results
    
    def get_etf_config_by_isin(self, isin: str) -> Optional[ETFConfig]:
        """Récupère la configuration d'un ETF par son ISIN"""
        configs = self.get_etf_configs()
        for config in configs:
            if config.isin == isin:
                return config
        return None
    
    async def close(self):
        """Ferme les connexions"""
        await self.market_data_service.close()

# Instance globale
dynamic_etf_service = None

def get_dynamic_etf_service() -> DynamicETFService:
    """Dependency injection pour FastAPI"""
    global dynamic_etf_service
    if dynamic_etf_service is None:
        dynamic_etf_service = DynamicETFService()
    return dynamic_etf_service