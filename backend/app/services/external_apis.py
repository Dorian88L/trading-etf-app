"""
Service pour l'intégration des APIs externes (Alpha Vantage, Yahoo Finance)
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import yfinance as yf
from app.core.config import settings
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service principal pour les appels API externes"""
    
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.yahoo_finance_key = settings.YAHOO_FINANCE_API_KEY
        self.fmp_key = settings.FINANCIAL_MODELING_PREP_API_KEY
        
        # URLs de base
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        self.fmp_base = "https://financialmodelingprep.com/api/v3"
        
    async def get_etf_data(self, symbol: str, period: str = "1d") -> Optional[Dict]:
        """
        Récupère les données ETF depuis Yahoo Finance (priorité) ou Alpha Vantage (fallback)
        """
        cache_key = f"etf_data:{symbol}:{period}"
        
        # Vérifier le cache
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Essayer Yahoo Finance d'abord
        data = await self._get_yahoo_finance_data(symbol, period)
        
        # Fallback sur Alpha Vantage si Yahoo Finance échoue
        if not data and self.alpha_vantage_key:
            data = await self._get_alpha_vantage_data(symbol)
            
        # Fallback sur Financial Modeling Prep
        if not data:
            data = await self._get_fmp_data(symbol)
        
        if data:
            # Mettre en cache pour 5 minutes
            await cache_manager.set(
                cache_key, 
                json.dumps(data), 
                ttl=settings.CACHE_TTL_MARKET_DATA
            )
            
        return data
    
    async def _get_yahoo_finance_data(self, symbol: str, period: str = "1d") -> Optional[Dict]:
        """Récupère les données depuis Yahoo Finance"""
        try:
            # Utiliser yfinance pour récupérer les données
            ticker = yf.Ticker(symbol)
            
            # Récupérer les données historiques
            hist = ticker.history(period=period)
            if hist.empty:
                logger.warning(f"Aucune donnée historique trouvée pour {symbol}")
                return None
            
            # Récupérer les informations du ticker
            info = ticker.info
            
            # Formater les données
            latest_data = hist.iloc[-1]
            
            result = {
                "symbol": symbol,
                "price": float(latest_data['Close']),
                "change": float(latest_data['Close'] - hist.iloc[-2]['Close']) if len(hist) > 1 else 0,
                "change_percent": float((latest_data['Close'] - hist.iloc[-2]['Close']) / hist.iloc[-2]['Close'] * 100) if len(hist) > 1 else 0,
                "volume": int(latest_data['Volume']),
                "high": float(latest_data['High']),
                "low": float(latest_data['Low']),
                "open": float(latest_data['Open']),
                "previous_close": float(hist.iloc[-2]['Close']) if len(hist) > 1 else float(latest_data['Close']),
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "dividend_yield": info.get('dividendYield'),
                "expense_ratio": info.get('annualReportExpenseRatio'),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange'),
                "sector": info.get('category'),
                "description": info.get('longBusinessSummary'),
                "historical_data": [
                    {
                        "date": idx.strftime('%Y-%m-%d'),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume'])
                    }
                    for idx, row in hist.iterrows()
                ],
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_finance"
            }
            
            logger.info(f"Données récupérées avec succès depuis Yahoo Finance pour {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données Yahoo Finance pour {symbol}: {e}")
            return None
    
    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Récupère les données depuis Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                # Récupérer les données de base
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key
                }
                
                async with session.get(self.alpha_vantage_base, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Erreur HTTP {response.status} depuis Alpha Vantage")
                        return None
                    
                    data = await response.json()
                    
                    if 'Global Quote' not in data:
                        logger.error(f"Format de réponse inattendu depuis Alpha Vantage: {data}")
                        return None
                    
                    quote = data['Global Quote']
                    
                    result = {
                        "symbol": quote.get('01. symbol'),
                        "price": float(quote.get('05. price', 0)),
                        "change": float(quote.get('09. change', 0)),
                        "change_percent": float(quote.get('10. change percent', '0%').replace('%', '')),
                        "volume": int(quote.get('06. volume', 0)),
                        "high": float(quote.get('03. high', 0)),
                        "low": float(quote.get('04. low', 0)),
                        "open": float(quote.get('02. open', 0)),
                        "previous_close": float(quote.get('08. previous close', 0)),
                        "timestamp": datetime.now().isoformat(),
                        "source": "alpha_vantage"
                    }
                    
                    logger.info(f"Données récupérées avec succès depuis Alpha Vantage pour {symbol}")
                    return result
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données Alpha Vantage pour {symbol}: {e}")
            return None
    
    async def _get_fmp_data(self, symbol: str) -> Optional[Dict]:
        """Récupère les données depuis Financial Modeling Prep"""
        try:
            async with aiohttp.ClientSession() as session:
                # Récupérer le prix en temps réel
                url = f"{self.fmp_base}/quote/{symbol}"
                params = {'apikey': self.fmp_key}
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Erreur HTTP {response.status} depuis FMP")
                        return None
                    
                    data = await response.json()
                    
                    if not data or not isinstance(data, list) or len(data) == 0:
                        logger.error(f"Aucune donnée trouvée depuis FMP pour {symbol}")
                        return None
                    
                    quote = data[0]
                    
                    result = {
                        "symbol": quote.get('symbol'),
                        "price": float(quote.get('price', 0)),
                        "change": float(quote.get('change', 0)),
                        "change_percent": float(quote.get('changesPercentage', 0)),
                        "volume": int(quote.get('volume', 0)),
                        "high": float(quote.get('dayHigh', 0)),
                        "low": float(quote.get('dayLow', 0)),
                        "open": float(quote.get('open', 0)),
                        "previous_close": float(quote.get('previousClose', 0)),
                        "market_cap": quote.get('marketCap'),
                        "pe_ratio": quote.get('pe'),
                        "timestamp": datetime.now().isoformat(),
                        "source": "financial_modeling_prep"
                    }
                    
                    logger.info(f"Données récupérées avec succès depuis FMP pour {symbol}")
                    return result
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données FMP pour {symbol}: {e}")
            return None
    
    async def get_multiple_etfs(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Récupère les données de plusieurs ETFs en parallèle
        """
        tasks = [self.get_etf_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Erreur pour {symbol}: {result}")
                data[symbol] = None
            else:
                data[symbol] = result
        
        return data
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """
        Récupère les données des principaux indices européens
        """
        indices = {
            "CAC40": "^FCHI",
            "DAX": "^GDAXI", 
            "FTSE100": "^FTSE",
            "EUROSTOXX50": "^STOXX50E",
            "SP500": "^GSPC",
            "NASDAQ": "^IXIC"
        }
        
        cache_key = "market_indices"
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        results = await self.get_multiple_etfs(list(indices.values()))
        
        formatted_results = {}
        for name, symbol in indices.items():
            if results.get(symbol):
                formatted_results[name] = results[symbol]
        
        # Cache pour 5 minutes
        await cache_manager.set(
            cache_key,
            json.dumps(formatted_results),
            ttl=settings.CACHE_TTL_MARKET_DATA
        )
        
        return formatted_results
    
    async def search_etfs(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Recherche d'ETFs par nom ou symbole
        """
        # Pour l'instant, une liste statique des ETFs populaires européens
        # Dans une version avancée, on utiliserait une API de recherche
        popular_etfs = [
            {"symbol": "IWDA.AS", "name": "iShares Core MSCI World UCITS ETF", "sector": "Global Equity"},
            {"symbol": "VWCE.DE", "name": "Vanguard FTSE All-World UCITS ETF", "sector": "Global Equity"},
            {"symbol": "CSPX.PA", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Equity"},
            {"symbol": "EUNL.DE", "name": "iShares Core MSCI Europe UCITS ETF", "sector": "European Equity"},
            {"symbol": "IEMM.AS", "name": "iShares Core MSCI Emerging Markets IMI UCITS ETF", "sector": "Emerging Markets"},
            {"symbol": "LTPB.PA", "name": "Lyxor PEA Euro Government Bond UCITS ETF", "sector": "Government Bonds"},
            {"symbol": "PANX.PA", "name": "Lyxor PEA Nasdaq-100 UCITS ETF", "sector": "US Tech"},
            {"symbol": "PCEU.PA", "name": "Lyxor PEA EURO STOXX 50 UCITS ETF", "sector": "European Equity"},
        ]
        
        # Filtrer selon la requête
        query_lower = query.lower()
        filtered_etfs = [
            etf for etf in popular_etfs
            if query_lower in etf["symbol"].lower() or query_lower in etf["name"].lower()
        ]
        
        return filtered_etfs[:limit]

# Instance globale du service
external_api_service = ExternalAPIService()