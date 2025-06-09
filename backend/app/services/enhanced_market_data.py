"""
Service de données de marché amélioré avec plusieurs sources API
"""
import logging
import requests
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from app.core.config import settings
from app.core.cache import cache, CacheManager

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMarketData:
    """Données de marché enrichies avec métadonnées de source"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    currency: str
    source: str
    confidence: float  # Score de confiance 0-1
    last_update: datetime

class EnhancedMarketDataService:
    """Service de données de marché avec sources multiples"""
    
    def __init__(self):
        self.fmp_api_key = settings.FINANCIAL_MODELING_PREP_API_KEY
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        
        # Mapping des symboles européens
        self.european_indices = {
            'CAC40': {
                'yahoo': '^FCHI',
                'fmp': '%5EFCHI',
                'name': 'CAC 40'
            },
            'EUROSTOXX50': {
                'yahoo': '^STOXX50E', 
                'fmp': '%5ESTOXX50E',
                'name': 'EURO STOXX 50'
            },
            'DAX': {
                'yahoo': '^GDAXI',
                'fmp': '%5EGDAXI', 
                'name': 'DAX'
            },
            'FTSE100': {
                'yahoo': '^FTSE',
                'fmp': '%5EFTSE',
                'name': 'FTSE 100'
            }
        }
    
    def get_data_from_fmp(self, symbol: str) -> Optional[EnhancedMarketData]:
        """Récupère les données depuis Financial Modeling Prep"""
        try:
            url = f"{self.fmp_base_url}/quote/{symbol}"
            params = {'apikey': self.fmp_api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data or len(data) == 0:
                return None
                
            item = data[0]
            
            return EnhancedMarketData(
                symbol=symbol,
                price=float(item.get('price', 0)),
                change=float(item.get('change', 0)),
                change_percent=float(item.get('changesPercentage', 0)),
                volume=int(item.get('volume', 0)),
                currency=item.get('currency', 'USD'),
                source='Financial Modeling Prep',
                confidence=0.9,  # Haute confiance pour FMP
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Erreur FMP pour {symbol}: {e}")
            return None
    
    def get_data_from_yahoo(self, symbol: str) -> Optional[EnhancedMarketData]:
        """Récupère les données depuis Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if hist.empty:
                return None
                
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            current_price = float(latest['Close'])
            previous_close = float(previous['Close'])
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close != 0 else 0
            
            return EnhancedMarketData(
                symbol=symbol,
                price=current_price,
                change=change,
                change_percent=change_percent,
                volume=int(latest.get('Volume', 0)),
                currency=info.get('currency', 'USD'),
                source='Yahoo Finance',
                confidence=0.8,  # Confiance moyenne pour Yahoo
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Erreur Yahoo pour {symbol}: {e}")
            return None
    
    def get_enhanced_market_data(self, symbol: str, prefer_source: str = 'fmp') -> Optional[EnhancedMarketData]:
        """Récupère les données avec fallback automatique entre sources"""
        cache_key = f"enhanced_market:{symbol}"
        
        # Vérifier le cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit pour {symbol}")
            return cached_data
        
        sources = []
        if prefer_source == 'fmp':
            sources = [
                ('fmp', self.get_data_from_fmp),
                ('yahoo', self.get_data_from_yahoo)
            ]
        else:
            sources = [
                ('yahoo', self.get_data_from_yahoo),
                ('fmp', self.get_data_from_fmp)
            ]
        
        for source_name, source_func in sources:
            try:
                logger.info(f"Tentative {source_name} pour {symbol}")
                data = source_func(symbol)
                
                if data and data.price > 0:
                    # Validation des données
                    if abs(data.change_percent) > 50:  # Changement suspect
                        logger.warning(f"Changement suspect pour {symbol}: {data.change_percent}%")
                        data.confidence *= 0.5
                    
                    # Mettre en cache pour 60 secondes
                    cache.set(cache_key, data, 60)
                    logger.info(f"✅ Données récupérées via {source_name} pour {symbol}: {data.price}")
                    return data
                    
            except Exception as e:
                logger.error(f"Erreur {source_name} pour {symbol}: {e}")
                continue
        
        logger.error(f"❌ Impossible de récupérer des données pour {symbol}")
        return None
    
    def get_enhanced_indices(self) -> Dict[str, Any]:
        """Récupère tous les indices européens avec sources multiples"""
        indices_data = {}
        
        for index_key, config in self.european_indices.items():
            # Essayer d'abord FMP, puis Yahoo
            data = None
            
            # Essayer FMP
            if config.get('fmp'):
                data = self.get_enhanced_market_data(config['fmp'], 'fmp')
            
            # Fallback vers Yahoo si FMP échoue
            if not data and config.get('yahoo'):
                data = self.get_enhanced_market_data(config['yahoo'], 'yahoo')
            
            if data:
                indices_data[index_key] = {
                    'name': config['name'],
                    'value': data.price,
                    'change': data.change,
                    'change_percent': data.change_percent,
                    'volume': data.volume,
                    'currency': data.currency,
                    'source': data.source,
                    'confidence': data.confidence,
                    'last_update': data.last_update.isoformat()
                }
            else:
                logger.warning(f"Impossible de récupérer les données pour {config['name']}")
        
        return indices_data
    
    def validate_market_data(self, data: EnhancedMarketData) -> bool:
        """Valide la qualité des données de marché"""
        if not data:
            return False
            
        # Vérifications de base
        if data.price <= 0:
            return False
            
        if abs(data.change_percent) > 20:  # Changement > 20% suspect
            logger.warning(f"Changement suspect: {data.change_percent}%")
            return False
            
        return True

# Service global
enhanced_market_service = EnhancedMarketDataService()

def get_enhanced_market_service() -> EnhancedMarketDataService:
    """Dependency injection pour le service amélioré"""
    return enhanced_market_service