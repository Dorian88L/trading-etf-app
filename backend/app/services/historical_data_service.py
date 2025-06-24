"""
Service pour la récupération et sauvegarde des données historiques ETF
Combine scraping et APIs pour garantir des données complètes
"""

import asyncio
import aiohttp
import requests
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.etf import ETF, MarketData
from app.services.etf_scraping_service import ETFScrapingService, get_etf_scraping_service

logger = logging.getLogger(__name__)

@dataclass
class HistoricalDataPoint:
    """Point de données historiques"""
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None
    
class HistoricalDataService:
    """Service complet pour données historiques avec sauvegarde automatique"""
    
    def __init__(self):
        self.session = None
        self.scraping_service = get_etf_scraping_service()
        
        # Mapping ISIN vers symboles pour données historiques
        self.isin_to_symbols = {
            "IE00B5BMR087": ["CSPX.AS", "CSPX.L", "CSPX.PA"],  # iShares Core S&P 500
            "IE00B4L5Y983": ["IWDA.AS", "IWDA.L", "IWDA.PA"],  # iShares Core MSCI World
            "IE00BK5BQT80": ["VWRL.AS", "VWRL.L"],             # Vanguard FTSE All-World
            "IE00B3RBWM25": ["VWRL.AS", "VWRL.L"],             # Vanguard FTSE All-World (ancien)
            "IE00B3XXRP09": ["VUSA.L", "VUSA.AS"],             # Vanguard S&P 500
            "IE00B4L5YC18": ["IEMA.L", "IEMA.AS"],             # iShares Core MSCI Emerging Markets
            "IE00B1YZSC51": ["IEUR.L", "IEUR.AS"],             # iShares Core MSCI Europe
            "IE00B14X4M10": ["ISF.L"],                         # iShares Core FTSE 100
            "IE00B1XNHC34": ["INRG.L"],                        # iShares Global Clean Energy
            "LU0274211480": ["XMME.DE"],                       # Xtrackers MSCI Emerging Markets
            "IE00B4L5YX21": ["EXS1.DE"],                       # iShares Core EURO STOXX 50
            "FR0007052782": ["CAC.PA"],                        # Amundi ETF CAC 40
        }
        
        # Sources de données historiques par priorité
        self.historical_sources = [
            self._get_yahoo_historical,
            self._get_alpha_vantage_historical,
            self._get_twelvedata_historical,
            self._get_eodhd_historical,
        ]
    
    async def get_session(self):
        """Session HTTP réutilisable"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _get_yahoo_historical(self, symbol: str, period: str = "1y") -> Optional[List[HistoricalDataPoint]]:
        """Récupère les données historiques via yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Mapper les périodes
            period_map = {
                "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo", 
                "6mo": "6mo", "1y": "1y", "2y": "2y", "5y": "5y", "10y": "10y"
            }
            
            yf_period = period_map.get(period, "1y")
            hist = ticker.history(period=yf_period)
            
            if hist.empty:
                logger.warning(f"Yahoo Finance: Pas de données historiques pour {symbol}")
                return None
            
            data_points = []
            for index, row in hist.iterrows():
                try:
                    data_point = HistoricalDataPoint(
                        date=index.to_pydatetime(),
                        open_price=float(row['Open']),
                        high_price=float(row['High']),
                        low_price=float(row['Low']),
                        close_price=float(row['Close']),
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        adjusted_close=float(row['Close'])  # Yahoo donne déjà le prix ajusté
                    )
                    data_points.append(data_point)
                except Exception as e:
                    logger.warning(f"Erreur parsing ligne pour {symbol}: {e}")
                    continue
            
            logger.info(f"Yahoo Finance: {len(data_points)} points historiques pour {symbol}")
            return data_points
            
        except Exception as e:
            logger.error(f"Erreur Yahoo Finance historique pour {symbol}: {e}")
            return None
    
    async def _get_alpha_vantage_historical(self, symbol: str, period: str = "1y") -> Optional[List[HistoricalDataPoint]]:
        """Récupère les données historiques via Alpha Vantage"""
        if not settings.ALPHA_VANTAGE_API_KEY or settings.ALPHA_VANTAGE_API_KEY == "demo":
            return None
        
        try:
            session = await self.get_session()
            
            # Alpha Vantage utilise des fonctions différentes
            function = "TIME_SERIES_DAILY_ADJUSTED"
            if period in ["1d", "5d"]:
                function = "TIME_SERIES_INTRADAY"
            
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
                "outputsize": "full" if period in ["1y", "2y", "5y", "10y"] else "compact"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Chercher la clé des données temporelles
                time_series_key = None
                for key in data.keys():
                    if "Time Series" in key:
                        time_series_key = key
                        break
                
                if not time_series_key or time_series_key not in data:
                    logger.warning(f"Alpha Vantage: Format inattendu pour {symbol}")
                    return None
                
                time_series = data[time_series_key]
                data_points = []
                
                for date_str, values in time_series.items():
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        data_point = HistoricalDataPoint(
                            date=date,
                            open_price=float(values.get("1. open", 0)),
                            high_price=float(values.get("2. high", 0)),
                            low_price=float(values.get("3. low", 0)),
                            close_price=float(values.get("4. close", 0)),
                            volume=int(values.get("6. volume", 0)),
                            adjusted_close=float(values.get("5. adjusted close", values.get("4. close", 0)))
                        )
                        data_points.append(data_point)
                        
                    except Exception as e:
                        logger.warning(f"Alpha Vantage: Erreur parsing date {date_str}: {e}")
                        continue
                
                # Filtrer par période si nécessaire
                if period != "max":
                    cutoff_date = datetime.now() - self._period_to_timedelta(period)
                    data_points = [dp for dp in data_points if dp.date >= cutoff_date]
                
                logger.info(f"Alpha Vantage: {len(data_points)} points historiques pour {symbol}")
                return data_points
                
        except Exception as e:
            logger.error(f"Erreur Alpha Vantage historique pour {symbol}: {e}")
            return None
    
    async def _get_twelvedata_historical(self, symbol: str, period: str = "1y") -> Optional[List[HistoricalDataPoint]]:
        """Récupère les données historiques via TwelveData"""
        if not hasattr(settings, 'TWELVEDATA_API_KEY') or settings.TWELVEDATA_API_KEY == "demo":
            return None
        
        try:
            session = await self.get_session()
            
            # Mapper les périodes TwelveData
            interval = "1day"
            outputsize = "5000"
            
            url = "https://api.twelvedata.com/time_series"
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": settings.TWELVEDATA_API_KEY
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if "values" not in data:
                    logger.warning(f"TwelveData: Pas de données pour {symbol}")
                    return None
                
                data_points = []
                for item in data["values"]:
                    try:
                        date = datetime.strptime(item["datetime"], "%Y-%m-%d")
                        
                        data_point = HistoricalDataPoint(
                            date=date,
                            open_price=float(item["open"]),
                            high_price=float(item["high"]),
                            low_price=float(item["low"]),
                            close_price=float(item["close"]),
                            volume=int(item.get("volume", 0))
                        )
                        data_points.append(data_point)
                        
                    except Exception as e:
                        logger.warning(f"TwelveData: Erreur parsing: {e}")
                        continue
                
                # Filtrer par période
                if period != "max":
                    cutoff_date = datetime.now() - self._period_to_timedelta(period)
                    data_points = [dp for dp in data_points if dp.date >= cutoff_date]
                
                logger.info(f"TwelveData: {len(data_points)} points historiques pour {symbol}")
                return data_points
                
        except Exception as e:
            logger.error(f"Erreur TwelveData historique pour {symbol}: {e}")
            return None
    
    async def _get_eodhd_historical(self, symbol: str, period: str = "1y") -> Optional[List[HistoricalDataPoint]]:
        """Récupère les données historiques via EODHD"""
        if not hasattr(settings, 'EODHD_API_KEY') or settings.EODHD_API_KEY == "demo":
            return None
        
        try:
            session = await self.get_session()
            
            # Calculer les dates de début et fin
            end_date = datetime.now()
            start_date = end_date - self._period_to_timedelta(period)
            
            url = f"https://eodhistoricaldata.com/api/eod/{symbol}"
            params = {
                "api_token": settings.EODHD_API_KEY,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "fmt": "json"
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if not isinstance(data, list):
                    logger.warning(f"EODHD: Format inattendu pour {symbol}")
                    return None
                
                data_points = []
                for item in data:
                    try:
                        date = datetime.strptime(item["date"], "%Y-%m-%d")
                        
                        data_point = HistoricalDataPoint(
                            date=date,
                            open_price=float(item["open"]),
                            high_price=float(item["high"]),
                            low_price=float(item["low"]),
                            close_price=float(item["close"]),
                            volume=int(item.get("volume", 0)),
                            adjusted_close=float(item.get("adjusted_close", item["close"]))
                        )
                        data_points.append(data_point)
                        
                    except Exception as e:
                        logger.warning(f"EODHD: Erreur parsing: {e}")
                        continue
                
                logger.info(f"EODHD: {len(data_points)} points historiques pour {symbol}")
                return data_points
                
        except Exception as e:
            logger.error(f"Erreur EODHD historique pour {symbol}: {e}")
            return None
    
    def _period_to_timedelta(self, period: str) -> timedelta:
        """Convertit une période en timedelta"""
        period_map = {
            "1d": timedelta(days=1),
            "5d": timedelta(days=5),
            "1mo": timedelta(days=30),
            "3mo": timedelta(days=90),
            "6mo": timedelta(days=180),
            "1y": timedelta(days=365),
            "2y": timedelta(days=730),
            "5y": timedelta(days=1825),
            "10y": timedelta(days=3650),
        }
        return period_map.get(period, timedelta(days=365))
    
    async def get_historical_data(self, isin: str, period: str = "1y") -> Optional[List[HistoricalDataPoint]]:
        """Récupère les données historiques pour un ISIN avec fallback"""
        symbols = self.isin_to_symbols.get(isin, [])
        if not symbols:
            logger.warning(f"Aucun symbole trouvé pour l'ISIN {isin}")
            return None
        
        # Essayer chaque symbole avec chaque source
        for symbol in symbols:
            logger.info(f"Tentative récupération historique pour {isin} via {symbol}")
            
            for source_func in self.historical_sources:
                try:
                    data = await source_func(symbol, period) if asyncio.iscoroutinefunction(source_func) else source_func(symbol, period)
                    if data and len(data) > 0:
                        logger.info(f"Données historiques obtenues pour {isin} via {source_func.__name__}: {len(data)} points")
                        
                        # Sauvegarder automatiquement en base
                        await self.save_historical_to_database(isin, data)
                        
                        return data
                except Exception as e:
                    logger.warning(f"Erreur {source_func.__name__} pour {symbol}: {e}")
                    continue
        
        logger.error(f"Aucune donnée historique trouvée pour {isin}")
        return None
    
    async def save_historical_to_database(self, isin: str, data_points: List[HistoricalDataPoint]):
        """Sauvegarde les données historiques en base"""
        db = SessionLocal()
        try:
            saved_count = 0
            
            for point in data_points:
                # Vérifier si on a déjà cette date
                existing = db.query(MarketData).filter(
                    and_(
                        MarketData.etf_isin == isin,
                        MarketData.time >= point.date,
                        MarketData.time < point.date + timedelta(days=1)
                    )
                ).first()
                
                if not existing:
                    market_data = MarketData(
                        time=point.date,
                        etf_isin=isin,
                        open_price=point.open_price,
                        high_price=point.high_price,
                        low_price=point.low_price,
                        close_price=point.close_price,
                        volume=point.volume,
                        nav=point.adjusted_close
                    )
                    
                    db.add(market_data)
                    saved_count += 1
            
            if saved_count > 0:
                db.commit()
                logger.info(f"Données historiques sauvegardées pour {isin}: {saved_count} nouveaux points")
            else:
                logger.info(f"Aucune nouvelle donnée historique pour {isin}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique pour {isin}: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def update_all_historical_data(self, period: str = "1y"):
        """Met à jour toutes les données historiques"""
        logger.info(f"Début mise à jour historique pour {len(self.isin_to_symbols)} ETFs")
        
        tasks = []
        for isin in self.isin_to_symbols.keys():
            tasks.append(self.get_historical_data(isin, period))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, list) and len(result) > 0:
                success_count += 1
            elif isinstance(result, Exception):
                logger.error(f"Erreur mise à jour historique: {result}")
        
        logger.info(f"Mise à jour historique terminée: {success_count}/{len(self.isin_to_symbols)} ETFs mis à jour")
        return success_count
    
    async def close(self):
        """Ferme les sessions"""
        if self.session:
            await self.session.close()
        if self.scraping_service:
            await self.scraping_service.close()

# Instance globale
historical_data_service = None

def get_historical_data_service() -> HistoricalDataService:
    """Dependency injection pour FastAPI"""
    global historical_data_service
    if historical_data_service is None:
        historical_data_service = HistoricalDataService()
    return historical_data_service