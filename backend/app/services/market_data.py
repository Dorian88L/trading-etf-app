import httpx
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import yfinance as yf
from app.core.config import settings


class MarketDataProvider:
    """Market data provider using Yahoo Finance and Alpha Vantage"""
    
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_etf_data(self, symbol: str, period: str = "1d") -> Optional[Dict]:
        """Get ETF market data from Yahoo Finance"""
        try:
            # Yahoo Finance API call
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow(),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "close": float(latest["Close"]),
                "volume": int(latest["Volume"]),
                "nav": None  # Would need separate API for NAV
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def get_multiple_etf_data(self, symbols: List[str]) -> List[Dict]:
        """Get market data for multiple ETFs"""
        results = []
        for symbol in symbols:
            data = await self.get_etf_data(symbol)
            if data:
                results.append(data)
        return results
    
    async def get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Alpha Vantage API"""
        if not self.alpha_vantage_key:
            return None
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": "5min",
                "apikey": self.alpha_vantage_key
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if "Time Series (5min)" not in data:
                return None
            
            time_series = data["Time Series (5min)"]
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            
            return {
                "symbol": symbol,
                "timestamp": datetime.fromisoformat(latest_time),
                "open": float(latest_data["1. open"]),
                "high": float(latest_data["2. high"]),
                "low": float(latest_data["3. low"]),
                "close": float(latest_data["4. close"]),
                "volume": int(latest_data["5. volume"])
            }
        except Exception as e:
            print(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    async def get_sector_performance(self) -> Dict:
        """Get sector performance data (mock for now)"""
        return {
            "Technology": {"performance": 2.3, "trend": "up"},
            "Healthcare": {"performance": 1.1, "trend": "up"},
            "Financial": {"performance": -0.8, "trend": "down"},
            "Energy": {"performance": 3.2, "trend": "up"},
            "Consumer": {"performance": 0.5, "trend": "neutral"}
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# ETF symbol mapping (ISIN to Yahoo Finance symbol)
ISIN_TO_SYMBOL = {
    "FR0010296061": "CAC.PA",      # Lyxor CAC 40
    "IE00B4L5Y983": "IWDA.AS",     # iShares Core MSCI World
    "LU0274211217": "XWRD.DE",     # Xtrackers MSCI World
    "IE00B4L5YC18": "CSPX.AS",     # iShares Core S&P 500
    "IE00B5BMR087": "CSPX.L",      # iShares Core S&P 500 UCITS ETF USD Acc
    "FR0010315770": "PAEEM.PA",    # Lyxor MSCI Emerging Markets
    "IE00BKM4GZ66": "IMEU.AS",     # iShares Core MSCI Europe
    "LU0290358497": "XESX.DE",     # Xtrackers EURO STOXX 50
    "IE00B52MJD48": "CNDX.AS",     # iShares NASDAQ 100
    "LU0488316133": "XJPN.DE",     # Xtrackers MSCI Japan
    "IE00B6R52259": "ISAC.AS",     # iShares MSCI ACWI
    "IE00BK5BQT80": "VWCE.AS",     # Vanguard FTSE All-World UCITS ETF
    "DE0005933931": "DAX.DE",      # iShares Core DAX UCITS ETF
    "IE00B52VJ196": "SX5E.DE",     # iShares Core EURO STOXX 50 UCITS ETF
}


def get_symbol_from_isin(isin: str) -> Optional[str]:
    """Convert ISIN to trading symbol"""
    return ISIN_TO_SYMBOL.get(isin)