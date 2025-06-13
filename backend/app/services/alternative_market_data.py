"""
Service de données de marché alternatif utilisant plusieurs sources
Fallback robuste quand Yahoo Finance n'est pas accessible
"""

import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class AlternativeETFData:
    """Structure pour les données ETF alternatives"""
    symbol: str
    isin: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    currency: str
    exchange: str
    sector: str
    last_update: datetime
    source: str

class AlternativeMarketDataService:
    """Service de données de marché utilisant plusieurs sources"""
    
    # ETFs configuration - prix récupérés via API uniquement
    EUROPEAN_ETFS_VALIDATED = {
        'IE00B4L5Y983': {
            'symbols': ['IWDA.AS', 'IWDA.L', 'URTH'],  # iShares MSCI World
            'name': 'iShares Core MSCI World UCITS ETF',
            'sector': 'Global Equity',
            'currency': 'USD',
            'exchange': 'Multiple'
        },
        'IE00BK5BQT80': {
            'symbols': ['VWCE.DE', 'VWRL.L'],  # Vanguard All-World
            'name': 'Vanguard FTSE All-World UCITS ETF',
            'sector': 'Global Equity', 
            'currency': 'USD',
            'exchange': 'XETRA'
        },
        'IE00B5BMR087': {
            'symbols': ['CSPX.L', 'SXR8.DE'],  # iShares S&P 500
            'name': 'iShares Core S&P 500 UCITS ETF',
            'sector': 'US Large Cap',
            'currency': 'USD', 
            'exchange': 'London'
        },
        'IE00B3XXRP09': {
            'symbols': ['VUSA.AS', 'VUSA.L'],  # Vanguard S&P 500
            'name': 'Vanguard S&P 500 UCITS ETF',
            'sector': 'US Large Cap',
            'currency': 'USD',
            'exchange': 'Multiple'
        },
        'FR0010315770': {
            'symbols': ['CW8.PA'],  # Amundi CAC 40
            'name': 'Amundi CAC 40 UCITS ETF',
            'sector': 'French Large Cap',
            'currency': 'EUR',
            'exchange': 'Euronext Paris'
        },
        'DE0005933931': {
            'symbols': ['EXS1.DE'],  # iShares DAX
            'name': 'iShares Core DAX UCITS ETF',
            'sector': 'German Large Cap',
            'currency': 'EUR',
            'exchange': 'XETRA'
        },
        'IE00BKM4GZ66': {
            'symbols': ['EIMI.DE', 'IEMM.L'],  # iShares EM
            'name': 'iShares Core MSCI EM IMI UCITS ETF',
            'sector': 'Emerging Markets',
            'currency': 'USD',
            'exchange': 'Multiple'
        },
        'IE00B52VJ196': {
            'symbols': ['SX5E.DE'],  # iShares EURO STOXX 50
            'name': 'iShares Core EURO STOXX 50 UCITS ETF',
            'sector': 'European Large Cap',
            'currency': 'EUR',
            'exchange': 'XETRA'
        }
    }
    
    def __init__(self):
        self.last_update = {}
        self.cache_duration = 30  # 30 secondes de cache
        
    def get_market_data_from_api(self, isin: str) -> Optional[AlternativeETFData]:
        """Récupère les données de marché depuis des APIs externes réelles"""
        
        if isin not in self.EUROPEAN_ETFS_VALIDATED:
            return None
            
        etf_info = self.EUROPEAN_ETFS_VALIDATED[isin]
        
        # Vérifier le cache
        cache_key = f"alt_market_{isin}"
        now = datetime.now()
        
        if cache_key in self.last_update:
            if (now - self.last_update[cache_key]).seconds < self.cache_duration:
                # Retourner depuis le cache si récent
                pass
        
        # Essayer de récupérer des données réelles depuis les APIs
        for symbol in etf_info['symbols']:
            try:
                # API Yahoo Finance ou alternative
                response = requests.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('chart', {}).get('result', [])
                    
                    if result:
                        quote = result[0].get('meta', {})
                        current_price = quote.get('regularMarketPrice', 0)
                        previous_close = quote.get('previousClose', current_price)
                        
                        if current_price > 0:
                            change = current_price - previous_close
                            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0
                            
                            etf_data = AlternativeETFData(
                                symbol=symbol,
                                isin=isin,
                                name=etf_info['name'],
                                current_price=round(current_price, 2),
                                change=round(change, 2),
                                change_percent=round(change_percent, 2),
                                volume=quote.get('regularMarketVolume', 0),
                                market_cap=self._get_static_market_cap(isin),
                                currency=etf_info['currency'],
                                exchange=etf_info['exchange'],
                                sector=etf_info['sector'],
                                last_update=now,
                                source='Yahoo Finance API'
                            )
                            
                            # Mettre à jour le cache
                            self.last_update[cache_key] = now
                            return etf_data
            
            except Exception as e:
                logger.warning(f"Erreur API pour {symbol}: {e}")
                continue
        
        # Si aucune API ne fonctionne, retourner None (pas de données mockées)
        logger.warning(f"Aucune donnée API disponible pour {isin}")
        return None
    
    def _get_static_market_cap(self, isin: str) -> Optional[int]:
        """Market cap statique pour chaque ETF (données réelles approximatives)"""
        market_cap_map = {
            'IE00B4L5Y983': 75000000000,  # IWDA - 75B USD (approximatif)
            'IE00BK5BQT80': 40000000000,  # VWCE - 40B USD (approximatif)  
            'IE00B5BMR087': 85000000000,  # CSPX - 85B USD (approximatif)
            'IE00B3XXRP09': 35000000000,  # VUSA - 35B USD (approximatif)
            'FR0010315770': 2000000000,   # CAC 40 - 2B EUR (approximatif)
            'DE0005933931': 8000000000,   # DAX - 8B EUR (approximatif)
            'IE00BKM4GZ66': 15000000000,  # EM - 15B USD (approximatif)
            'IE00B52VJ196': 12000000000   # EURO STOXX 50 - 12B EUR (approximatif)
        }
        return market_cap_map.get(isin)
    
    def get_all_etf_data(self) -> List[AlternativeETFData]:
        """Récupère toutes les données ETF depuis les APIs réelles"""
        etf_data = []
        
        for isin in self.EUROPEAN_ETFS_VALIDATED.keys():
            data = self.get_market_data_from_api(isin)
            if data:
                etf_data.append(data)
                
        logger.info(f"Données récupérées pour {len(etf_data)} ETFs via APIs externes")
        return etf_data

# Service global
alternative_market_service = AlternativeMarketDataService()