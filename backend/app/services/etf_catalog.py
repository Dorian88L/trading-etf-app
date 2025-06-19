"""
Service de catalogue d'ETFs européens
Gère la large gamme d'ETFs disponibles pour sélection utilisateur
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.etf import ETF

logger = logging.getLogger(__name__)

@dataclass
class ETFInfo:
    """Information complète sur un ETF"""
    isin: str
    symbol: str
    name: str
    sector: str
    region: str
    currency: str
    ter: float  # Total Expense Ratio
    aum: float  # Assets Under Management
    exchange: str
    description: str
    benchmark: str
    inception_date: str
    dividend_frequency: str
    replication_method: str

class ETFCatalogService:
    """Service de gestion du catalogue d'ETFs"""
    
    # Catalogue complet d'ETFs européens populaires
    ETF_CATALOG = {
        # ETFs Monde/Global
        'IWDA.AS': ETFInfo(
            isin='IE00B4L5Y983',
            symbol='IWDA.AS',
            name='iShares Core MSCI World UCITS ETF',
            sector='Global',
            region='World',
            currency='USD',
            ter=0.20,
            aum=65000000000,
            exchange='Euronext Amsterdam',
            description='Réplique l\'indice MSCI World, exposé aux marchés développés mondiaux',
            benchmark='MSCI World Index',
            inception_date='2009-09-25',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        'VWCE.DE': ETFInfo(
            isin='IE00BK5BQT80',
            symbol='VWCE.DE',
            name='Vanguard FTSE All-World UCITS ETF',
            sector='Global',
            region='World',
            currency='USD',
            ter=0.22,
            aum=15000000000,
            exchange='Xetra',
            description='Exposition aux marchés développés et émergents mondiaux',
            benchmark='FTSE All-World Index',
            inception_date='2019-07-23',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        # ETFs Europe
        'IEUS.AS': ETFInfo(
            isin='IE00B4K48X80',
            symbol='IEUS.AS',
            name='iShares Core MSCI Europe UCITS ETF',
            sector='Europe',
            region='Europe',
            currency='EUR',
            ter=0.12,
            aum=8000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux grandes et moyennes capitalisations européennes',
            benchmark='MSCI Europe Index',
            inception_date='2010-06-25',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        'VEUR.AS': ETFInfo(
            isin='IE00BK5BQV03',
            symbol='VEUR.AS',
            name='Vanguard FTSE Europe UCITS ETF',
            sector='Europe',
            region='Europe',
            currency='EUR',
            ter=0.10,
            aum=2500000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux marchés européens développés',
            benchmark='FTSE Europe Index',
            inception_date='2019-07-23',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        # ETFs USA
        'CSPX.AS': ETFInfo(
            isin='IE00B5BMR087',
            symbol='CSPX.AS',
            name='iShares Core S&P 500 UCITS ETF',
            sector='USA',
            region='North America',
            currency='USD',
            ter=0.07,
            aum=65000000000,
            exchange='Euronext Amsterdam',
            description='Réplique l\'indice S&P 500 des 500 plus grandes entreprises américaines',
            benchmark='S&P 500 Index',
            inception_date='2010-05-19',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        'VUAA.AS': ETFInfo(
            isin='IE00B3XXRP09',
            symbol='VUAA.AS',
            name='Vanguard S&P 500 UCITS ETF',
            sector='USA',
            region='North America',
            currency='USD',
            ter=0.07,
            aum=35000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux 500 plus grandes entreprises américaines',
            benchmark='S&P 500 Index',
            inception_date='2012-05-22',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        # ETFs Sectoriels Technologie
        'EQQQ.AS': ETFInfo(
            isin='IE0032077012',
            symbol='EQQQ.AS',
            name='Invesco EQQQ NASDAQ-100 UCITS ETF',
            sector='Technology',
            region='North America',
            currency='USD',
            ter=0.30,
            aum=8000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux 100 plus grandes sociétés non financières du NASDAQ',
            benchmark='NASDAQ-100 Index',
            inception_date='2007-04-16',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        'IUIT.AS': ETFInfo(
            isin='IE00B4K6B022',
            symbol='IUIT.AS',
            name='iShares Core MSCI World Information Technology Sector UCITS ETF',
            sector='Technology',
            region='World',
            currency='USD',
            ter=0.25,
            aum=3000000000,
            exchange='Euronext Amsterdam',
            description='Exposition mondiale au secteur des technologies de l\'information',
            benchmark='MSCI World Information Technology Index',
            inception_date='2015-09-18',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Sectoriels Healthcare
        'HEAL.AS': ETFInfo(
            isin='IE00BMW42900',
            symbol='HEAL.AS',
            name='iShares MSCI World Health Care Sector UCITS ETF',
            sector='Healthcare',
            region='World',
            currency='USD',
            ter=0.25,
            aum=1500000000,
            exchange='Euronext Amsterdam',
            description='Exposition mondiale au secteur de la santé',
            benchmark='MSCI World Health Care Index',
            inception_date='2018-05-11',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Sectoriels Energy
        'INRG.AS': ETFInfo(
            isin='IE00B1XNHC34',
            symbol='INRG.AS',
            name='iShares Global Clean Energy UCITS ETF',
            sector='Clean Energy',
            region='World',
            currency='USD',
            ter=0.65,
            aum=6000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux entreprises d\'énergie propre mondiales',
            benchmark='S&P Global Clean Energy Index',
            inception_date='2007-10-24',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Marchés Émergents
        'IEMG.AS': ETFInfo(
            isin='IE00B4L5YC18',
            symbol='IEMG.AS',
            name='iShares Core MSCI Emerging Markets IMI UCITS ETF',
            sector='Emerging Markets',
            region='Emerging',
            currency='USD',
            ter=0.18,
            aum=15000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux marchés émergents mondiaux',
            benchmark='MSCI Emerging Markets IMI Index',
            inception_date='2014-05-21',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Obligations
        'IEAG.AS': ETFInfo(
            isin='IE00B4WXJJ64',
            symbol='IEAG.AS',
            name='iShares Core Euro Aggregate Bond UCITS ETF',
            sector='Bonds',
            region='Europe',
            currency='EUR',
            ter=0.09,
            aum=3000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux obligations d\'entreprises et d\'État européennes',
            benchmark='Bloomberg Euro Aggregate Bond Index',
            inception_date='2015-06-25',
            dividend_frequency='Monthly',
            replication_method='Physical'
        ),
        
        'AGGG.AS': ETFInfo(
            isin='IE00B3DKXQ41',
            symbol='AGGG.AS',
            name='iShares Core Global Aggregate Bond UCITS ETF',
            sector='Bonds',
            region='World',
            currency='EUR',
            ter=0.10,
            aum=2000000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux obligations mondiales',
            benchmark='Bloomberg Global Aggregate Bond Index',
            inception_date='2015-06-25',
            dividend_frequency='Monthly',
            replication_method='Physical'
        ),
        
        # ETFs Immobilier
        'IPRP.AS': ETFInfo(
            isin='IE00B1FZS350',
            symbol='IPRP.AS',
            name='iShares European Property Yield UCITS ETF',
            sector='Real Estate',
            region='Europe',
            currency='EUR',
            ter=0.40,
            aum=800000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux REITs européens',
            benchmark='FTSE EPRA/NAREIT Europe Capped Index',
            inception_date='2006-10-20',
            dividend_frequency='Quarterly',
            replication_method='Physical'
        ),
        
        # ETFs Small Cap
        'IUSN.AS': ETFInfo(
            isin='IE00B3VWN518',
            symbol='IUSN.AS',
            name='iShares MSCI World Small Cap UCITS ETF',
            sector='Small Cap',
            region='World',
            currency='USD',
            ter=0.35,
            aum=2500000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux petites capitalisations mondiales',
            benchmark='MSCI World Small Cap Index',
            inception_date='2009-10-23',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Value/Growth
        'IWVL.AS': ETFInfo(
            isin='IE00BP3QZ825',
            symbol='IWVL.AS',
            name='iShares Edge MSCI World Value Factor UCITS ETF',
            sector='Value Factor',
            region='World',
            currency='USD',
            ter=0.30,
            aum=1200000000,
            exchange='Euronext Amsterdam',
            description='Exposition aux actions mondiales undervaluées',
            benchmark='MSCI World Enhanced Value Index',
            inception_date='2018-09-21',
            dividend_frequency='Semi-annual',
            replication_method='Physical'
        ),
        
        # ETFs Gold/Commodities
        'IGLN.AS': ETFInfo(
            isin='IE00B579F325',
            symbol='IGLN.AS',
            name='iShares Physical Gold ETC',
            sector='Commodities',
            region='Global',
            currency='USD',
            ter=0.25,
            aum=15000000000,
            exchange='Euronext Amsterdam',
            description='Exposition physique à l\'or',
            benchmark='Gold Spot Price',
            inception_date='2011-03-18',
            dividend_frequency='None',
            replication_method='Physical'
        )
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_all_etfs(self) -> List[ETFInfo]:
        """Retourne la liste complète des ETFs disponibles"""
        return list(self.ETF_CATALOG.values())
    
    def get_etfs_by_sector(self, sector: str) -> List[ETFInfo]:
        """Retourne les ETFs d'un secteur donné"""
        return [etf for etf in self.ETF_CATALOG.values() if etf.sector.lower() == sector.lower()]
    
    def get_etfs_by_region(self, region: str) -> List[ETFInfo]:
        """Retourne les ETFs d'une région donnée"""
        return [etf for etf in self.ETF_CATALOG.values() if etf.region.lower() == region.lower()]
    
    def search_etfs(self, query: str) -> List[ETFInfo]:
        """Recherche d'ETFs par nom, secteur ou symbole"""
        query = query.lower()
        results = []
        
        for etf in self.ETF_CATALOG.values():
            if (query in etf.name.lower() or 
                query in etf.sector.lower() or
                query in etf.symbol.lower() or
                query in etf.description.lower()):
                results.append(etf)
        
        return results
    
    def get_popular_etfs(self, limit: int = 10) -> List[ETFInfo]:
        """Retourne les ETFs les plus populaires (par AUM)"""
        sorted_etfs = sorted(self.ETF_CATALOG.values(), key=lambda x: x.aum, reverse=True)
        return sorted_etfs[:limit]
    
    def get_low_cost_etfs(self, max_ter: float = 0.20) -> List[ETFInfo]:
        """Retourne les ETFs avec des frais faibles"""
        return [etf for etf in self.ETF_CATALOG.values() if etf.ter <= max_ter]
    
    def get_etf_by_isin(self, isin: str) -> Optional[ETFInfo]:
        """Retourne un ETF par son ISIN"""
        for etf in self.ETF_CATALOG.values():
            if etf.isin == isin:
                return etf
        return None
    
    def get_etf_by_symbol(self, symbol: str) -> Optional[ETFInfo]:
        """Retourne un ETF par son symbole"""
        return self.ETF_CATALOG.get(symbol)
    
    def get_sectors(self) -> List[str]:
        """Retourne la liste unique des secteurs"""
        sectors = set(etf.sector for etf in self.ETF_CATALOG.values())
        return sorted(list(sectors))
    
    def get_regions(self) -> List[str]:
        """Retourne la liste unique des régions"""
        regions = set(etf.region for etf in self.ETF_CATALOG.values())
        return sorted(list(regions))
    
    def filter_etfs(self, 
                   sectors: Optional[List[str]] = None,
                   regions: Optional[List[str]] = None,
                   max_ter: Optional[float] = None,
                   min_aum: Optional[float] = None,
                   currencies: Optional[List[str]] = None) -> List[ETFInfo]:
        """Filtre les ETFs selon plusieurs critères"""
        filtered_etfs = list(self.ETF_CATALOG.values())
        
        if sectors:
            filtered_etfs = [etf for etf in filtered_etfs if etf.sector in sectors]
        
        if regions:
            filtered_etfs = [etf for etf in filtered_etfs if etf.region in regions]
        
        if max_ter is not None:
            filtered_etfs = [etf for etf in filtered_etfs if etf.ter <= max_ter]
        
        if min_aum is not None:
            filtered_etfs = [etf for etf in filtered_etfs if etf.aum >= min_aum]
        
        if currencies:
            filtered_etfs = [etf for etf in filtered_etfs if etf.currency in currencies]
        
        return filtered_etfs
    
    def populate_database(self, db: Session):
        """Peuple la base de données avec le catalogue d'ETFs"""
        try:
            for symbol, etf_info in self.ETF_CATALOG.items():
                # Vérifier si l'ETF existe déjà
                existing_etf = db.query(ETF).filter(ETF.isin == etf_info.isin).first()
                
                if not existing_etf:
                    new_etf = ETF(
                        isin=etf_info.isin,
                        symbol=symbol,  # Ajouter le symbole
                        name=etf_info.name,
                        sector=etf_info.sector,
                        currency=etf_info.currency,
                        ter=etf_info.ter,
                        aum=etf_info.aum,
                        exchange=etf_info.exchange
                    )
                    db.add(new_etf)
                else:
                    # Mettre à jour les informations
                    existing_etf.symbol = symbol
                    existing_etf.name = etf_info.name
                    existing_etf.sector = etf_info.sector
                    existing_etf.ter = etf_info.ter
                    existing_etf.aum = etf_info.aum
            
            db.commit()
            self.logger.info(f"Base de données peuplée avec {len(self.ETF_CATALOG)} ETFs")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du peuplement de la base de données: {e}")
            db.rollback()
            raise

def get_etf_catalog_service() -> ETFCatalogService:
    """Factory function pour le service de catalogue ETF"""
    return ETFCatalogService()