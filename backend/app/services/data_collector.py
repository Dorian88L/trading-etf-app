"""
Collecteur de données en temps réel selon le cahier des charges
- Collecte toutes les 5 minutes (prix, volumes)
- Collecte journalière (données fondamentales, NAV)
- Sources multiples : Yahoo Finance, Alpha Vantage
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import redis
import json
from celery import Celery

logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Point de données de marché"""
    timestamp: datetime
    etf_isin: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    nav: Optional[float] = None

@dataclass
class ETFInfo:
    """Informations ETF"""
    isin: str
    ticker: str
    name: str
    sector: str
    currency: str
    ter: float
    aum: float
    exchange: str

class DataCollector:
    """Collecteur de données en temps réel"""
    
    def __init__(self, redis_client: redis.Redis, db_config: Dict):
        self.redis_client = redis_client
        self.db_config = db_config
        self.session = None
        
        # Mapping ISIN -> Ticker pour Yahoo Finance
        self.isin_ticker_mapping = {
            "FR0010296061": "CAC.PA",      # Lyxor CAC 40
            "IE00B4L5Y983": "SWDA.L",      # iShares MSCI World
            "LU0290358497": "SX5E.DE",     # Xtrackers EURO STOXX 50
            "IE00B4L5YC18": "CSPX.L",      # iShares S&P 500
            "LU0274208692": "XMME.DE"      # Xtrackers Emerging Markets
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def collect_realtime_data(self, isin_list: List[str]) -> List[MarketDataPoint]:
        """Collecte des données temps réel pour une liste d'ETFs"""
        logger.info(f"Collecte temps réel pour {len(isin_list)} ETFs")
        
        tasks = []
        for isin in isin_list:
            ticker = self.isin_ticker_mapping.get(isin)
            if ticker:
                task = self.fetch_yahoo_data(isin, ticker)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les erreurs
        valid_results = []
        for result in results:
            if isinstance(result, MarketDataPoint):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur collecte: {result}")
        
        return valid_results
    
    async def fetch_yahoo_data(self, isin: str, ticker: str) -> Optional[MarketDataPoint]:
        """Récupère les données depuis Yahoo Finance"""
        try:
            # Utilisation synchrone de yfinance (dans un thread pool en production)
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d", interval="5m")
            
            if hist.empty:
                logger.warning(f"Pas de données pour {ticker}")
                return None
            
            # Dernière ligne de données
            latest = hist.iloc[-1]
            
            return MarketDataPoint(
                timestamp=datetime.now(),
                etf_isin=isin,
                open_price=float(latest['Open']),
                high_price=float(latest['High']),
                low_price=float(latest['Low']),
                close_price=float(latest['Close']),
                volume=int(latest['Volume']),
                nav=None  # À calculer séparément
            )
            
        except Exception as e:
            logger.error(f"Erreur Yahoo Finance pour {ticker}: {e}")
            return None
    
    async def fetch_alpha_vantage_data(self, isin: str, symbol: str, api_key: str) -> Optional[MarketDataPoint]:
        """Récupère les données depuis Alpha Vantage"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': '5min',
                'apikey': api_key,
                'outputsize': 'compact'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                if 'Time Series (5min)' not in data:
                    logger.warning(f"Pas de données Alpha Vantage pour {symbol}")
                    return None
                
                time_series = data['Time Series (5min)']
                latest_time = max(time_series.keys())
                latest_data = time_series[latest_time]
                
                return MarketDataPoint(
                    timestamp=datetime.strptime(latest_time, "%Y-%m-%d %H:%M:%S"),
                    etf_isin=isin,
                    open_price=float(latest_data['1. open']),
                    high_price=float(latest_data['2. high']),
                    low_price=float(latest_data['3. low']),
                    close_price=float(latest_data['4. close']),
                    volume=int(latest_data['5. volume'])
                )
                
        except Exception as e:
            logger.error(f"Erreur Alpha Vantage pour {symbol}: {e}")
            return None
    
    def save_to_database(self, data_points: List[MarketDataPoint]) -> bool:
        """Sauvegarde les données en base"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            for point in data_points:
                cursor.execute("""
                    INSERT INTO market_data (time, etf_isin, open_price, high_price, low_price, close_price, volume, nav)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time, etf_isin) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        nav = EXCLUDED.nav
                """, (
                    point.timestamp,
                    point.etf_isin,
                    point.open_price,
                    point.high_price,
                    point.low_price,
                    point.close_price,
                    point.volume,
                    point.nav
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Sauvegardé {len(data_points)} points de données")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde base: {e}")
            return False
    
    def cache_latest_data(self, data_points: List[MarketDataPoint]) -> None:
        """Met en cache les dernières données dans Redis"""
        try:
            for point in data_points:
                cache_key = f"latest_data:{point.etf_isin}"
                cache_data = {
                    'timestamp': point.timestamp.isoformat(),
                    'close_price': point.close_price,
                    'volume': point.volume,
                    'high_price': point.high_price,
                    'low_price': point.low_price
                }
                
                # Cache avec expiration de 10 minutes
                self.redis_client.setex(
                    cache_key, 
                    600,  # 10 minutes
                    json.dumps(cache_data)
                )
            
            logger.info(f"Mis en cache {len(data_points)} points")
            
        except Exception as e:
            logger.error(f"Erreur cache Redis: {e}")
    
    async def collect_daily_fundamentals(self, isin_list: List[str]) -> Dict[str, Dict]:
        """Collecte quotidienne des données fondamentales"""
        logger.info("Collecte des données fondamentales")
        
        fundamentals = {}
        
        for isin in isin_list:
            ticker = self.isin_ticker_mapping.get(isin)
            if ticker:
                try:
                    ticker_obj = yf.Ticker(ticker)
                    info = ticker_obj.info
                    
                    fundamentals[isin] = {
                        'market_cap': info.get('marketCap', 0),
                        'total_assets': info.get('totalAssets', 0),
                        'expense_ratio': info.get('annualReportExpenseRatio', 0.01),
                        'yield': info.get('yield', 0),
                        'beta': info.get('beta', 1.0),
                        'pe_ratio': info.get('forwardPE', 0),
                        'dividend_yield': info.get('dividendYield', 0),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Erreur collecte fondamentaux {ticker}: {e}")
        
        return fundamentals

# Configuration Celery pour les tâches périodiques
celery_app = Celery('data_collector')
celery_app.conf.update(
    broker_url='redis://localhost:6380',
    result_backend='redis://localhost:6380',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
)

# Configuration des tâches périodiques
celery_app.conf.beat_schedule = {
    'collect-realtime-data': {
        'task': 'app.services.data_collector.collect_realtime_task',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'collect-daily-fundamentals': {
        'task': 'app.services.data_collector.collect_fundamentals_task',
        'schedule': 86400.0,  # Tous les jours
    },
    'generate-signals': {
        'task': 'app.services.data_collector.generate_signals_task',
        'schedule': 1800.0,  # Toutes les 30 minutes
    },
}

@celery_app.task
def collect_realtime_task():
    """Tâche Celery pour la collecte temps réel"""
    import redis
    
    # Configuration
    redis_client = redis.Redis(host='localhost', port=6380, db=0)
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    # Liste des ETFs à surveiller
    etf_list = [
        "FR0010296061",  # Lyxor CAC 40
        "IE00B4L5Y983",  # iShares MSCI World
        "LU0290358497",  # Xtrackers EURO STOXX 50
        "IE00B4L5YC18",  # iShares S&P 500
        "LU0274208692"   # Xtrackers Emerging Markets
    ]
    
    async def collect_data():
        async with DataCollector(redis_client, db_config) as collector:
            data_points = await collector.collect_realtime_data(etf_list)
            
            if data_points:
                # Sauvegarde en base
                collector.save_to_database(data_points)
                
                # Cache Redis
                collector.cache_latest_data(data_points)
                
                logger.info(f"Collecte réussie: {len(data_points)} ETFs")
            else:
                logger.warning("Aucune donnée collectée")
    
    # Exécution de la tâche async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(collect_data())
    finally:
        loop.close()
    
    return f"Collecte terminée à {datetime.now()}"

@celery_app.task
def collect_fundamentals_task():
    """Tâche Celery pour la collecte des fondamentaux"""
    import redis
    
    redis_client = redis.Redis(host='localhost', port=6380, db=0)
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    etf_list = [
        "FR0010296061", "IE00B4L5Y983", "LU0290358497", 
        "IE00B4L5YC18", "LU0274208692"
    ]
    
    async def collect_fundamentals():
        async with DataCollector(redis_client, db_config) as collector:
            fundamentals = await collector.collect_daily_fundamentals(etf_list)
            
            # Cache des fondamentaux
            for isin, data in fundamentals.items():
                cache_key = f"fundamentals:{isin}"
                redis_client.setex(
                    cache_key,
                    86400,  # 24 heures
                    json.dumps(data)
                )
            
            logger.info(f"Fondamentaux collectés: {len(fundamentals)} ETFs")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(collect_fundamentals())
    finally:
        loop.close()
    
    return f"Fondamentaux collectés à {datetime.now()}"

@celery_app.task
def generate_signals_task():
    """Tâche Celery pour la génération de signaux"""
    from app.services.advanced_signals import AdvancedSignalGenerator
    import psycopg2
    import pandas as pd
    
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    etf_list = [
        "FR0010296061", "IE00B4L5Y983", "LU0290358497", 
        "IE00B4L5YC18", "LU0274208692"
    ]
    
    try:
        conn = psycopg2.connect(**db_config)
        signal_generator = AdvancedSignalGenerator()
        
        for isin in etf_list:
            # Récupérer les données de marché des 50 derniers jours
            query = """
                SELECT time, open_price, high_price, low_price, close_price, volume
                FROM market_data 
                WHERE etf_isin = %s 
                ORDER BY time DESC 
                LIMIT 500
            """
            
            df = pd.read_sql_query(query, conn, params=(isin,))
            
            if len(df) >= 50:
                df = df.sort_values('time')
                
                # Informations ETF
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, sector, ter, aum FROM etfs WHERE isin = %s", 
                    (isin,)
                )
                etf_info_row = cursor.fetchone()
                cursor.close()
                
                if etf_info_row:
                    etf_info = {
                        'name': etf_info_row[0],
                        'sector': etf_info_row[1],
                        'ter': etf_info_row[2] or 0.01,
                        'aum': etf_info_row[3] or 1000000000
                    }
                    
                    # Génération du signal
                    signal = signal_generator.generate_advanced_signal(isin, df, etf_info)
                    
                    if signal and signal.confidence >= 60:
                        # Sauvegarde du signal
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO signals (etf_isin, signal_type, confidence, technical_score, 
                                               fundamental_score, risk_score, price_target, stop_loss, 
                                               current_price, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            signal.etf_isin,
                            signal.signal_type.value,
                            signal.confidence,
                            signal.technical_score.total_score,
                            signal.fundamental_score.total_score,
                            signal.risk_score.total_score,
                            signal.price_target,
                            signal.stop_loss,
                            signal.current_price,
                            signal.timestamp
                        ))
                        conn.commit()
                        cursor.close()
                        
                        logger.info(f"Signal généré pour {isin}: {signal.signal_type} (confidence: {signal.confidence:.1f})")
        
        conn.close()
        return f"Signaux générés à {datetime.now()}"
        
    except Exception as e:
        logger.error(f"Erreur génération signaux: {e}")
        return f"Erreur: {e}"

if __name__ == "__main__":
    # Test de collecte
    import redis
    
    redis_client = redis.Redis(host='localhost', port=6380, db=0)
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    etf_list = ["FR0010296061", "IE00B4L5Y983"]
    
    async def test_collection():
        async with DataCollector(redis_client, db_config) as collector:
            data_points = await collector.collect_realtime_data(etf_list)
            print(f"Collecté: {len(data_points)} points")
            
            for point in data_points:
                print(f"{point.etf_isin}: {point.close_price} EUR (Volume: {point.volume})")
    
    asyncio.run(test_collection())