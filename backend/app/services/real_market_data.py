"""
Service de collecte de données de marché réelles pour les ETFs européens
Utilise plusieurs sources de données : Yahoo Finance, Twelve Data (optionnel)
"""

import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.core.cache import cache, CacheManager, cache_response

logger = logging.getLogger(__name__)

@dataclass
class RealETFData:
    """Structure pour les données ETF réelles"""
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

@dataclass
class RealMarketDataPoint:
    """Point de données de marché réel"""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adj_close: float

class RealMarketDataService:
    """Service de collecte de données de marché réelles"""
    
    # ETFs européens populaires avec leurs symboles Yahoo Finance (corrigés et vérifiés)
    EUROPEAN_ETFS = {
        # iShares ETFs
        'IWDA.L': {
            'isin': 'IE00B4L5Y983',
            'name': 'iShares Core MSCI World UCITS ETF',
            'sector': 'Global Developed',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        'VWRL.L': {
            'isin': 'IE00BK5BQT80',
            'name': 'Vanguard FTSE All-World UCITS ETF',
            'sector': 'Global All Cap',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        'CSPX.L': {
            'isin': 'IE00B5BMR087',
            'name': 'iShares Core S&P 500 UCITS ETF',
            'sector': 'US Large Cap',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        'VUSA.L': {
            'isin': 'IE00B3XXRP09',
            'name': 'Vanguard S&P 500 UCITS ETF',
            'sector': 'US Large Cap',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        'IEMA.L': {
            'isin': 'IE00BKM4GZ66',
            'name': 'iShares Core MSCI EM IMI UCITS ETF',
            'sector': 'Emerging Markets',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        'IEUR.L': {
            'isin': 'IE00B4K48X80',
            'name': 'iShares Core MSCI Europe UCITS ETF',
            'sector': 'European Developed',
            'exchange': 'London Stock Exchange',
            'currency': 'EUR'
        },
        'ISF.L': {
            'isin': 'IE00B52VJ196',
            'name': 'iShares Core EURO STOXX 50 UCITS ETF',
            'sector': 'European Large Cap',
            'exchange': 'London Stock Exchange',
            'currency': 'EUR'
        },
        'INRG.L': {
            'isin': 'IE00B1XNHC34',
            'name': 'iShares Global Clean Energy UCITS ETF',
            'sector': 'Clean Energy',
            'exchange': 'London Stock Exchange',
            'currency': 'USD'
        },
        # ETFs avec symboles Xetra (Allemagne)
        'EUNL.DE': {
            'isin': 'IE00B4K48X80',
            'name': 'iShares Core MSCI Europe UCITS ETF EUR',
            'sector': 'European Developed',
            'exchange': 'XETRA',
            'currency': 'EUR'
        },
        'XMME.DE': {
            'isin': 'LU0274208692',
            'name': 'Xtrackers MSCI Emerging Markets UCITS ETF',
            'sector': 'Emerging Markets',
            'exchange': 'XETRA',
            'currency': 'USD'
        },
        # ETFs Paris
        'CW8.PA': {
            'isin': 'LU0274208692',
            'name': 'Amundi MSCI World UCITS ETF',
            'sector': 'Global Developed',
            'exchange': 'Euronext Paris',
            'currency': 'EUR'
        },
        'CAC.PA': {
            'isin': 'FR0010296061',
            'name': 'Lyxor CAC 40 UCITS ETF',
            'sector': 'French Large Cap',
            'exchange': 'Euronext Paris',
            'currency': 'EUR'
        },
        # ETFs US pour test de connectivité
        'SPY': {
            'isin': 'US78462F1030',
            'name': 'SPDR S&P 500 ETF Trust',
            'sector': 'US Large Cap',
            'exchange': 'NYSE',
            'currency': 'USD'
        },
        'VTI': {
            'isin': 'US9229087690',
            'name': 'Vanguard Total Stock Market ETF',
            'sector': 'US Total Market',
            'exchange': 'NYSE',
            'currency': 'USD'
        },
        'QQQ': {
            'isin': 'US46090E1038',
            'name': 'Invesco QQQ Trust',
            'sector': 'US Technology',
            'exchange': 'NASDAQ',
            'currency': 'USD'
        }
    }
    
    # Indices de marché européens
    EUROPEAN_INDICES = {
        '^FCHI': 'CAC 40',
        '^STOXX50E': 'EURO STOXX 50', 
        '^GDAXI': 'DAX',
        '^FTSE': 'FTSE 100',
        '^AEX': 'AEX',
        '^IBEX': 'IBEX 35'
    }
    
    def __init__(self, twelve_data_api_key: Optional[str] = None):
        self.twelve_data_api_key = twelve_data_api_key
    
    def get_real_etf_data(self, symbol: str) -> Optional[RealETFData]:
        """Récupère les données réelles d'un ETF via Yahoo Finance avec retry"""
        # Vérifier le cache d'abord
        cache_key = f"etf_data:{symbol}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit pour ETF {symbol}")
            return cached_data
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                
                # Récupérer les données intraday pour avoir des données plus récentes
                hist = ticker.history(period="5d", interval="1d")
                
                if hist.empty:
                    logger.warning(f"Aucune donnée disponible pour {symbol}")
                    return None
                
                # Prendre les données les plus récentes
                latest = hist.iloc[-1]
                previous = hist.iloc[-2] if len(hist) > 1 else latest
                
                current_price = float(latest['Close'])
                previous_close = float(previous['Close']) if len(hist) > 1 else current_price
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                
                etf_info = self.EUROPEAN_ETFS.get(symbol, {})
                
                # Récupérer des informations supplémentaires
                info = ticker.info
                market_cap = info.get('totalAssets') or info.get('marketCap')
                
                etf_data = RealETFData(
                    symbol=symbol,
                    isin=etf_info.get('isin', 'N/A'),
                    name=etf_info.get('name', info.get('longName', info.get('shortName', 'ETF Inconnu'))),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(latest.get('Volume', 0)),
                    market_cap=market_cap,
                    currency=etf_info.get('currency', info.get('currency', 'EUR')),
                    exchange=etf_info.get('exchange', info.get('exchange', 'Unknown')),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=latest.name if hasattr(latest, 'name') else datetime.now()
                )
                
                # Mettre en cache pour 30 secondes
                cache.set(cache_key, etf_data, 30)
                logger.debug(f"Données ETF {symbol} mises en cache")
                
                return etf_data
                
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée pour {symbol}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Échec définitif pour {symbol} après {max_retries} tentatives")
                    return None
                
        return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> List[RealMarketDataPoint]:
        """Récupère les données historiques d'un ETF"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            data_points = []
            for index, row in hist.iterrows():
                point = RealMarketDataPoint(
                    timestamp=index.to_pydatetime(),
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    volume=int(row['Volume']),
                    adj_close=float(row['Adj Close'])
                )
                data_points.append(point)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique pour {symbol}: {e}")
            return []
    
    def get_market_indices(self) -> Dict[str, Dict]:
        """Récupère les données des indices de marché européens"""
        indices_data = {}
        
        for symbol, name in self.EUROPEAN_INDICES.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                info = ticker.info
                
                if len(hist) >= 1:
                    latest = hist.iloc[-1]
                    previous = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    current_value = float(latest['Close'])
                    previous_close = float(previous['Close'])
                    change = current_value - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                    
                    indices_data[symbol] = {
                        'name': name,
                        'value': current_value,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': int(latest.get('Volume', 0)),
                        'currency': info.get('currency', 'EUR'),
                        'last_update': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de l'indice {symbol}: {e}")
                continue
        
        return indices_data
    
    def collect_all_etf_data(self) -> List[RealETFData]:
        """Collecte les données de tous les ETFs configurés"""
        etf_data = []
        
        for symbol in self.EUROPEAN_ETFS.keys():
            data = self.get_real_etf_data(symbol)
            if data:
                etf_data.append(data)
                logger.info(f"Données collectées pour {symbol}: {data.current_price} {data.currency}")
            else:
                logger.warning(f"Impossible de récupérer les données pour {symbol}")
        
        logger.info(f"Collecte terminée: {len(etf_data)}/{len(self.EUROPEAN_ETFS)} ETFs récupérés")
        return etf_data
    
    def get_single_etf_data(self, symbol: str) -> Optional[RealETFData]:
        """Récupère les données d'un seul ETF (pour tests)"""
        return self.get_real_etf_data(symbol)
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> List[Dict]:
        """Récupère les données historiques d'un ETF"""
        try:
            import yfinance as yf
            
            # Créer l'objet ticker
            ticker = yf.Ticker(symbol)
            
            # Récupérer les données historiques
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"Aucune donnée historique trouvée pour {symbol}")
                return []
            
            # Convertir en format dict avec les noms de colonnes corrects
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    'timestamp': date,
                    'open_price': float(row['Open']),
                    'high_price': float(row['High']),
                    'low_price': float(row['Low']),
                    'close_price': float(row['Close']),
                    'volume': int(row['Volume']),
                    'adj_close': float(row['Close'])  # Assuming adjusted close same as close
                })
            
            logger.info(f"Données historiques récupérées pour {symbol}: {len(historical_data)} points")
            return historical_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données historiques pour {symbol}: {e}")
            return []
    

# Service global
real_market_service = RealMarketDataService()

def get_real_market_data_service() -> RealMarketDataService:
    """Dependency injection pour le service de données réelles"""
    return real_market_service