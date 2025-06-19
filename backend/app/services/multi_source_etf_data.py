"""
Service de données ETF multi-sources avec fallback intelligent
Optimisé pour éviter les limites de rate et garantir des données réelles
"""

import asyncio
import aiohttp
import yfinance as yf
import requests
import random
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import json
import time
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class DataSource(Enum):
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage" 
    FMP = "financial_modeling_prep"
    EODHD = "eodhd"
    FINNHUB = "finnhub"
    MARKETSTACK = "marketstack"
    TWELVEDATA = "twelvedata"
    CACHE = "cache"
    HYBRID = "hybrid_calculated"

@dataclass
class ETFDataPoint:
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
    source: Union[DataSource, str]
    confidence_score: float  # 0.0 à 1.0, indique la fiabilité des données
    data_quality: Optional[str] = None  # Qualité des données ('high', 'medium', 'low', etc.)
    reliability_icon: Optional[str] = None  # Icône pour l'interface ('✅', '⚠️', '🌐', etc.)
    
class MultiSourceETFDataService:
    """
    Service de données ETF multi-sources avec fallback intelligent
    """
    
    def __init__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        self.cache_ttl = 300  # 5 minutes
        self.rate_limits = {
            DataSource.ALPHA_VANTAGE: {"calls": 0, "last_reset": datetime.now(), "limit": 25, "window": 86400},
            DataSource.FMP: {"calls": 0, "last_reset": datetime.now(), "limit": 250, "window": 86400},
            DataSource.EODHD: {"calls": 0, "last_reset": datetime.now(), "limit": 20, "window": 86400},
            DataSource.FINNHUB: {"calls": 0, "last_reset": datetime.now(), "limit": 60, "window": 60},
            DataSource.MARKETSTACK: {"calls": 0, "last_reset": datetime.now(), "limit": 1000, "window": 86400},
            DataSource.TWELVEDATA: {"calls": 0, "last_reset": datetime.now(), "limit": 800, "window": 86400},
        }
        
        # ETFs européens avec leurs symboles par échange
        self.european_etfs = {
            # London Stock Exchange (.L)
            "IWDA.L": {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World UCITS ETF USD (Acc)", "sector": "Global Equity", "exchange": "LSE"},
            "VWRL.L": {"isin": "IE00B3RBWM25", "name": "Vanguard FTSE All-World UCITS ETF", "sector": "Global Equity", "exchange": "LSE"},
            "CSPX.L": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF USD (Acc)", "sector": "US Equity", "exchange": "LSE"},
            "CSPX.AS": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Large Cap", "exchange": "Euronext Amsterdam"},
            "VUSA.L": {"isin": "IE00B3XXRP09", "name": "Vanguard S&P 500 UCITS ETF", "sector": "US Equity", "exchange": "LSE"},
            "IEMA.L": {"isin": "IE00B4L5YC18", "name": "iShares Core MSCI Emerging Markets IMI UCITS ETF", "sector": "Emerging Markets", "exchange": "LSE"},
            "IEUR.L": {"isin": "IE00B1YZSC51", "name": "iShares Core MSCI Europe UCITS ETF EUR (Acc)", "sector": "Europe Equity", "exchange": "LSE"},
            "ISF.L": {"isin": "IE00B14X4M10", "name": "iShares Core FTSE 100 UCITS ETF GBP (Acc)", "sector": "UK Equity", "exchange": "LSE"},
            "INRG.L": {"isin": "IE00B1XNHC34", "name": "iShares Global Clean Energy UCITS ETF", "sector": "Clean Energy", "exchange": "LSE"},
            
            # XETRA (.DE)
            "EUNL.DE": {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World UCITS ETF", "sector": "Global Equity", "exchange": "XETRA"},
            "XMME.DE": {"isin": "LU0274211480", "name": "Xtrackers MSCI Emerging Markets UCITS ETF", "sector": "Emerging Markets", "exchange": "XETRA"},
            "EXS1.DE": {"isin": "IE00B4L5YX21", "name": "iShares Core EURO STOXX 50 UCITS ETF", "sector": "Eurozone Equity", "exchange": "XETRA"},
            "SX5E.DE": {"isin": "IE00B4BNMY34", "name": "iShares Core EURO STOXX 50 UCITS ETF EUR (Dist)", "sector": "Eurozone Equity", "exchange": "XETRA"},
            
            # Euronext Paris (.PA)
            "CW8.PA": {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World UCITS ETF", "sector": "Global Equity", "exchange": "EPA"},
            "CAC.PA": {"isin": "FR0007052782", "name": "Amundi ETF CAC 40 UCITS ETF DR", "sector": "France Equity", "exchange": "EPA"},
            
            # Euronext Amsterdam (.AS)
            "IWDA.AS": {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World UCITS ETF", "sector": "Global Equity", "exchange": "AMS"},
            "VWRL.AS": {"isin": "IE00B3RBWM25", "name": "Vanguard FTSE All-World UCITS ETF", "sector": "Global Equity", "exchange": "AMS"},
        }
        
        # Mapping inverse : ISIN vers meilleur symbole pour les données temps réel
        self.isin_to_best_symbol = {}
        for symbol, info in self.european_etfs.items():
            isin = info['isin']
            if isin not in self.isin_to_best_symbol:
                self.isin_to_best_symbol[isin] = symbol
            else:
                # Préférer les symboles avec EUR pour les prix européens
                if '.AS' in symbol or '.DE' in symbol or '.PA' in symbol:
                    self.isin_to_best_symbol[isin] = symbol
        
        # Configuration des API keys
        self.api_keys = {
            DataSource.ALPHA_VANTAGE: settings.ALPHA_VANTAGE_API_KEY,
            DataSource.FMP: settings.FINANCIAL_MODELING_PREP_API_KEY or "demo",
            DataSource.EODHD: getattr(settings, 'EODHD_API_KEY', None),
            DataSource.FINNHUB: getattr(settings, 'FINNHUB_API_KEY', None),
            DataSource.MARKETSTACK: getattr(settings, 'MARKETSTACK_API_KEY', None),
            DataSource.TWELVEDATA: getattr(settings, 'TWELVEDATA_API_KEY', None),
        }

    def _check_rate_limit(self, source: DataSource) -> bool:
        """Vérifie si on peut faire un appel API pour cette source"""
        if source not in self.rate_limits:
            return True
            
        rate_info = self.rate_limits[source]
        now = datetime.now()
        
        # Reset le compteur si la fenêtre est passée
        if (now - rate_info["last_reset"]).total_seconds() >= rate_info["window"]:
            rate_info["calls"] = 0
            rate_info["last_reset"] = now
            
        return rate_info["calls"] < rate_info["limit"]
    
    def _increment_rate_limit(self, source: DataSource):
        """Incrémente le compteur de rate limit"""
        if source in self.rate_limits:
            self.rate_limits[source]["calls"] += 1

    async def _get_yahoo_finance_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis Yahoo Finance"""
        try:
            if not self._check_rate_limit(DataSource.YAHOO_FINANCE):
                logger.warning(f"Rate limit atteint pour Yahoo Finance")
                return None
                
            # Convertir les symboles européens au format Yahoo
            yahoo_symbol = self._convert_to_yahoo_symbol(symbol)
            
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if hist.empty or not info:
                return None
                
            current_price = float(hist['Close'].iloc[-1])
            previous_close = float(info.get('previousClose', current_price))
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0
            
            etf_info = self.european_etfs.get(symbol, {})
            
            return ETFDataPoint(
                symbol=symbol,
                isin=etf_info.get('isin', ''),
                name=info.get('longName', etf_info.get('name', symbol)),
                current_price=current_price,
                change=change,
                change_percent=change_percent,
                volume=int(info.get('volume', 0)),
                market_cap=info.get('marketCap'),
                currency=info.get('currency', 'EUR'),
                exchange=etf_info.get('exchange', 'Unknown'),
                sector=etf_info.get('sector', 'Unknown'),
                last_update=datetime.now(),
                source=DataSource.YAHOO_FINANCE,
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"Erreur Yahoo Finance pour {symbol}: {e}")
            return None

    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis Alpha Vantage"""
        try:
            if not self.api_keys[DataSource.ALPHA_VANTAGE] or not self._check_rate_limit(DataSource.ALPHA_VANTAGE):
                return None
                
            # Alpha Vantage fonctionne mieux avec les symboles de base sans extension
            base_symbol = symbol.split('.')[0]
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': base_symbol,
                'apikey': self.api_keys[DataSource.ALPHA_VANTAGE]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                quote = data.get('Global Quote', {})
                
                if not quote:
                    return None
                    
                self._increment_rate_limit(DataSource.ALPHA_VANTAGE)
                
                etf_info = self.european_etfs.get(symbol, {})
                current_price = float(quote.get('05. price', 0))
                change = float(quote.get('09. change', 0))
                change_percent = float(quote.get('10. change percent', '0').replace('%', ''))
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=etf_info.get('name', symbol),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(quote.get('06. volume', 0)),
                    market_cap=None,
                    currency='EUR',
                    exchange=etf_info.get('exchange', 'Unknown'),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.ALPHA_VANTAGE,
                    confidence_score=0.8
                )
                
        except Exception as e:
            logger.error(f"Erreur Alpha Vantage pour {symbol}: {e}")
            return None

    async def _get_fmp_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis Financial Modeling Prep"""
        try:
            if not self._check_rate_limit(DataSource.FMP):
                return None
                
            base_symbol = symbol.split('.')[0]
            
            url = f"https://financialmodelingprep.com/api/v3/quote/{base_symbol}"
            params = {'apikey': self.api_keys[DataSource.FMP]}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    return None
                    
                quote = data[0]
                self._increment_rate_limit(DataSource.FMP)
                
                etf_info = self.european_etfs.get(symbol, {})
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=quote.get('name', etf_info.get('name', symbol)),
                    current_price=float(quote.get('price', 0)),
                    change=float(quote.get('change', 0)),
                    change_percent=float(quote.get('changesPercentage', 0)),
                    volume=int(quote.get('volume', 0)),
                    market_cap=quote.get('marketCap'),
                    currency='EUR',
                    exchange=etf_info.get('exchange', 'Unknown'),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.FMP,
                    confidence_score=0.85
                )
                
        except Exception as e:
            logger.error(f"Erreur FMP pour {symbol}: {e}")
            return None

    async def _get_eodhd_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis EODHD"""
        try:
            if not self.api_keys[DataSource.EODHD] or not self._check_rate_limit(DataSource.EODHD):
                return None
                
            # EODHD supporte les symboles avec extensions
            url = f"https://eodhd.com/api/real-time/{symbol}"
            params = {'api_token': self.api_keys[DataSource.EODHD], 'fmt': 'json'}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                self._increment_rate_limit(DataSource.EODHD)
                
                etf_info = self.european_etfs.get(symbol, {})
                current_price = float(data.get('close', 0))
                previous_close = float(data.get('previousClose', current_price))
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close > 0 else 0
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=etf_info.get('name', symbol),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(data.get('volume', 0)),
                    market_cap=None,
                    currency='EUR',
                    exchange=etf_info.get('exchange', 'Unknown'),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.EODHD,
                    confidence_score=0.9
                )
                
        except Exception as e:
            logger.error(f"Erreur EODHD pour {symbol}: {e}")
            return None

    async def _get_finnhub_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis Finnhub"""
        try:
            if not self.api_keys[DataSource.FINNHUB] or not self._check_rate_limit(DataSource.FINNHUB):
                return None
                
            # Convertir le symbole pour Finnhub (format différent pour les bourses européennes)
            finnhub_symbol = self._convert_to_finnhub_symbol(symbol)
            
            url = "https://finnhub.io/api/v1/quote"
            params = {'symbol': finnhub_symbol, 'token': self.api_keys[DataSource.FINNHUB]}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                self._increment_rate_limit(DataSource.FINNHUB)
                
                # Vérifier si les données sont valides
                if not data.get('c') or data.get('c') == 0:
                    return None
                
                etf_info = self.european_etfs.get(symbol, {})
                current_price = float(data.get('c', 0))  # current price
                previous_close = float(data.get('pc', current_price))  # previous close
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close > 0 else 0
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=etf_info.get('name', symbol),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=0,  # Finnhub ne fournit pas toujours le volume dans cette endpoint
                    market_cap=None,
                    currency='EUR',
                    exchange=etf_info.get('exchange', 'Unknown'),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.FINNHUB,
                    confidence_score=0.85
                )
                
        except Exception as e:
            logger.error(f"Erreur Finnhub pour {symbol}: {e}")
            return None

    async def _get_marketstack_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis Marketstack"""
        try:
            if not self.api_keys[DataSource.MARKETSTACK] or not self._check_rate_limit(DataSource.MARKETSTACK):
                return None
                
            # Marketstack utilise un format différent
            base_symbol = symbol.split('.')[0]
            
            url = "https://api.marketstack.com/v1/eod/latest"
            params = {
                'access_key': self.api_keys[DataSource.MARKETSTACK],
                'symbols': base_symbol,
                'limit': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                self._increment_rate_limit(DataSource.MARKETSTACK)
                
                # Vérifier si les données sont disponibles
                if not data.get('data') or len(data['data']) == 0:
                    return None
                
                quote = data['data'][0]
                etf_info = self.european_etfs.get(symbol, {})
                
                current_price = float(quote.get('close', 0))
                open_price = float(quote.get('open', current_price))
                change = current_price - open_price
                change_percent = (change / open_price) * 100 if open_price > 0 else 0
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=etf_info.get('name', symbol),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(quote.get('volume', 0)),
                    market_cap=None,
                    currency='EUR',
                    exchange=etf_info.get('exchange', 'Unknown'),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.MARKETSTACK,
                    confidence_score=0.8
                )
                
        except Exception as e:
            logger.error(f"Erreur Marketstack pour {symbol}: {e}")
            return None

    async def _get_twelvedata_data(self, symbol: str) -> Optional[ETFDataPoint]:
        """Récupère les données depuis TwelveData"""
        try:
            if not self.api_keys[DataSource.TWELVEDATA] or not self._check_rate_limit(DataSource.TWELVEDATA):
                return None
                
            # TwelveData supporte les symboles avec extensions d'échange
            url = "https://api.twelvedata.com/quote"
            params = {
                'symbol': symbol,
                'apikey': self.api_keys[DataSource.TWELVEDATA]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                self._increment_rate_limit(DataSource.TWELVEDATA)
                
                # Vérifier si les données sont valides
                if data.get('status') == 'error' or not data.get('close'):
                    return None
                
                etf_info = self.european_etfs.get(symbol, {})
                current_price = float(data.get('close', 0))
                previous_close = float(data.get('previous_close', current_price))
                change = current_price - previous_close
                change_percent = float(data.get('percent_change', 0))
                
                return ETFDataPoint(
                    symbol=symbol,
                    isin=etf_info.get('isin', ''),
                    name=data.get('name', etf_info.get('name', symbol)),
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(data.get('volume', 0)),
                    market_cap=None,
                    currency=data.get('currency', 'EUR'),
                    exchange=data.get('exchange', etf_info.get('exchange', 'Unknown')),
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=datetime.now(),
                    source=DataSource.TWELVEDATA,
                    confidence_score=0.88
                )
                
        except Exception as e:
            logger.error(f"Erreur TwelveData pour {symbol}: {e}")
            return None

    def _generate_hybrid_data(self, symbol: str) -> ETFDataPoint:
        """DÉSACTIVÉ - Pas de données simulées autorisées"""
        raise NotImplementedError("Génération de données simulées désactivée - utilisation de données réelles uniquement")

    def _convert_to_yahoo_symbol(self, symbol: str) -> str:
        """Convertit un symbole ETF au format Yahoo Finance"""
        # Mapping des suffixes d'échange
        exchange_mapping = {
            '.L': '.L',      # London Stock Exchange
            '.DE': '.DE',    # XETRA
            '.PA': '.PA',    # Euronext Paris
            '.AS': '.AS',    # Euronext Amsterdam
        }
        
        for suffix, yahoo_suffix in exchange_mapping.items():
            if symbol.endswith(suffix):
                return symbol.replace(suffix, yahoo_suffix)
                
        return symbol

    def _convert_to_finnhub_symbol(self, symbol: str) -> str:
        """Convertit un symbole ETF au format Finnhub"""
        # Finnhub utilise des formats différents pour les bourses européennes
        if symbol.endswith('.L'):
            return symbol  # London utilise le même format
        elif symbol.endswith('.DE'):
            return symbol  # XETRA utilise le même format
        elif symbol.endswith('.PA'):
            return symbol  # Euronext Paris utilise le même format
        elif symbol.endswith('.AS'):
            return symbol  # Euronext Amsterdam utilise le même format
        
        return symbol

    async def get_etf_data(self, symbol: str) -> ETFDataPoint:
        """
        Récupère les données d'un ETF en utilisant les sources dans l'ordre de priorité
        """
        sources = [
            self._get_yahoo_finance_data,
            self._get_twelvedata_data,
            self._get_eodhd_data,
            self._get_finnhub_data,
            self._get_alpha_vantage_data,
            self._get_fmp_data,
            self._get_marketstack_data,
        ]
        
        for source_func in sources:
            try:
                data = await source_func(symbol)
                if data and data.current_price > 0:
                    logger.info(f"Données obtenues pour {symbol} depuis {data.source.value}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur source {source_func.__name__} pour {symbol}: {e}")
                continue
        
        # Si aucune source API n'a fonctionné, utiliser le scraping en fallback
        logger.warning(f"APIs indisponibles pour {symbol}, tentative de scraping")
        
        # Importer et utiliser le service de scraping
        from app.services.etf_scraping_service import ETFScrapingService
        scraping_service = ETFScrapingService()
        
        try:
            scraped_data = await scraping_service.get_etf_data(symbol)
            if scraped_data:
                # Convertir ScrapedETFData en ETFDataPoint
                etf_info = self.european_etfs.get(symbol, {})
                return ETFDataPoint(
                    symbol=symbol,
                    isin=scraped_data.isin or etf_info.get('isin', ''),
                    name=scraped_data.name,
                    current_price=scraped_data.current_price,
                    change=scraped_data.change,
                    change_percent=scraped_data.change_percent,
                    volume=scraped_data.volume or 0,
                    market_cap=None,
                    currency=scraped_data.currency,
                    exchange=scraped_data.exchange,
                    sector=etf_info.get('sector', 'Unknown'),
                    last_update=scraped_data.last_update,
                    source=DataSource.CACHE,  # Marquer comme scraping
                    confidence_score=0.9,  # Haute confiance pour scraping
                    data_quality='scraped_realtime',
                    reliability_icon='🌐'
                )
        except Exception as e:
            logger.error(f"Erreur scraping pour {symbol}: {e}")
            
        logger.error(f"Toutes les sources échouées pour {symbol}")
        return None

    async def get_etf_data_by_isin(self, isin: str) -> Optional[ETFDataPoint]:
        """
        Récupère les données d'un ETF par son ISIN en utilisant le meilleur symbole disponible
        """
        best_symbol = self.isin_to_best_symbol.get(isin)
        if not best_symbol:
            logger.warning(f"Aucun symbole trouvé pour l'ISIN {isin}")
            return None
        
        logger.info(f"Récupération des données pour ISIN {isin} via symbole {best_symbol}")
        return await self.get_etf_data(best_symbol)

    async def get_all_etf_data(self) -> List[ETFDataPoint]:
        """
        Récupère toutes les données ETF disponibles en utilisant les meilleurs symboles par ISIN
        """
        tasks = []
        processed_isins = set()
        
        # Pour chaque ISIN, utiliser le meilleur symbole
        for isin, best_symbol in self.isin_to_best_symbol.items():
            if isin not in processed_isins:
                tasks.append(self.get_etf_data(best_symbol))
                processed_isins.add(isin)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, ETFDataPoint):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur lors de la récupération: {result}")
        
        logger.info(f"Récupération terminée: {len(valid_results)} ETFs uniques sur {len(self.isin_to_best_symbol)} ISINs")
        return valid_results

    async def close(self):
        """Ferme les sessions"""
        if self.session:
            await self.session.close()

# Instance globale du service
multi_source_etf_service = None

def get_multi_source_etf_service() -> MultiSourceETFDataService:
    """Dependency injection pour FastAPI"""
    global multi_source_etf_service
    if multi_source_etf_service is None:
        multi_source_etf_service = MultiSourceETFDataService()
    return multi_source_etf_service