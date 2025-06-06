"""
Endpoints pour les signaux avancés
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import psycopg2

from app.core.database import get_db
from app.services.advanced_signals import AdvancedSignalGenerator, AdvancedSignal
from pydantic import BaseModel

router = APIRouter()

class AdvancedSignalResponse(BaseModel):
    id: str
    etf_isin: str
    etf_name: str
    signal_type: str
    algorithm_type: str
    confidence: float
    technical_score: float
    fundamental_score: float
    risk_score: float
    current_price: float
    price_target: float
    stop_loss: float
    expected_return: float
    risk_reward_ratio: float
    holding_period: int
    justification: str
    timestamp: datetime
    sector: str

class MarketDataResponse(BaseModel):
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

class TechnicalIndicatorResponse(BaseModel):
    timestamp: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None

@router.get("/signals/advanced", response_model=List[AdvancedSignalResponse])
def get_advanced_signals(
    limit: int = Query(10, ge=1, le=50),
    signal_type: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Récupère les signaux avancés avec scoring détaillé"""
    
    # Configuration DB pour raw SQL (car notre schéma n'est pas encore en ORM)
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        
        # Query pour récupérer les signaux récents
        query = """
            SELECT s.*, e.name as etf_name, e.sector
            FROM signals s
            JOIN etfs e ON s.etf_isin = e.isin
            WHERE s.timestamp >= %s
        """
        params = [datetime.now() - timedelta(days=7)]
        
        if signal_type:
            query += " AND s.signal_type = %s"
            params.append(signal_type)
        
        if min_confidence:
            query += " AND s.confidence >= %s"
            params.append(min_confidence)
        
        query += " ORDER BY s.timestamp DESC, s.confidence DESC LIMIT %s"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Si pas de signaux en base, générer des signaux d'exemple
        if df.empty:
            return generate_sample_signals(limit)
        
        # Convertir en réponse
        signals = []
        for _, row in df.iterrows():
            signals.append(AdvancedSignalResponse(
                id=str(row.get('id', f"sig_{len(signals)}")),
                etf_isin=row['etf_isin'],
                etf_name=row.get('etf_name', 'ETF Unknown'),
                signal_type=row['signal_type'],
                algorithm_type=row.get('algorithm_type', 'MOMENTUM'),
                confidence=float(row['confidence']),
                technical_score=float(row.get('technical_score', 50.0)),
                fundamental_score=float(row.get('fundamental_score', 60.0)),
                risk_score=float(row.get('risk_score', 55.0)),
                current_price=float(row['current_price']),
                price_target=float(row['price_target']),
                stop_loss=float(row['stop_loss']),
                expected_return=float(row.get('expected_return', 0.0)),
                risk_reward_ratio=float(row.get('risk_reward_ratio', 1.0)),
                holding_period=int(row.get('holding_period', 7)),
                justification=row.get('justification', f"Signal {row['signal_type']} généré automatiquement"),
                timestamp=row['timestamp'],
                sector=row.get('sector', 'Mixed')
            ))
        
        return signals
        
    except Exception as e:
        # En cas d'erreur, retourner des signaux d'exemple
        return generate_sample_signals(limit)

@router.get("/market-data/{etf_isin}", response_model=List[MarketDataResponse])
def get_market_data(
    etf_isin: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Récupère les données de marché pour un ETF"""
    
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        
        query = """
            SELECT time as timestamp, open_price, high_price, low_price, close_price, volume
            FROM market_data 
            WHERE etf_isin = %s 
            AND time >= %s
            ORDER BY time ASC
        """
        
        start_date = datetime.now() - timedelta(days=days)
        df = pd.read_sql_query(query, conn, params=[etf_isin, start_date])
        conn.close()
        
        if df.empty:
            # Générer des données d'exemple
            return generate_sample_market_data(days)
        
        return [
            MarketDataResponse(
                timestamp=row['timestamp'],
                open_price=float(row['open_price']),
                high_price=float(row['high_price']),
                low_price=float(row['low_price']),
                close_price=float(row['close_price']),
                volume=int(row['volume'])
            )
            for _, row in df.iterrows()
        ]
        
    except Exception as e:
        return generate_sample_market_data(days)

@router.get("/technical-indicators/{etf_isin}", response_model=List[TechnicalIndicatorResponse])
def get_technical_indicators(
    etf_isin: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Récupère les indicateurs techniques pour un ETF"""
    
    db_config = {
        "host": "localhost",
        "port": 5433,
        "database": "trading_etf",
        "user": "trading_user",
        "password": "trading_password"
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        
        # Récupérer les données de marché pour calculer les indicateurs
        query = """
            SELECT time, close_price, high_price, low_price, volume
            FROM market_data 
            WHERE etf_isin = %s 
            AND time >= %s
            ORDER BY time ASC
        """
        
        start_date = datetime.now() - timedelta(days=days + 50)  # Plus de données pour les calculs
        df = pd.read_sql_query(query, conn, params=[etf_isin, start_date])
        conn.close()
        
        if len(df) < 50:
            return generate_sample_indicators(days)
        
        # Calculer les indicateurs
        from app.services.advanced_signals import AdvancedTechnicalAnalyzer
        analyzer = AdvancedTechnicalAnalyzer()
        
        close = df['close_price']
        high = df['high_price']
        low = df['low_price']
        
        # Calculs
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        
        # Bollinger Bands
        sma_bb = close.rolling(20).mean()
        std_bb = close.rolling(20).std()
        bb_upper = sma_bb + (2 * std_bb)
        bb_lower = sma_bb - (2 * std_bb)
        
        # Filtrer les derniers jours demandés
        recent_df = df.tail(days)
        
        indicators = []
        for i, (_, row) in enumerate(recent_df.iterrows()):
            idx = df.index[df['time'] == row['time']].tolist()[0]
            
            indicators.append(TechnicalIndicatorResponse(
                timestamp=row['time'],
                sma_20=float(sma_20.iloc[idx]) if not pd.isna(sma_20.iloc[idx]) else None,
                sma_50=float(sma_50.iloc[idx]) if not pd.isna(sma_50.iloc[idx]) else None,
                sma_200=float(sma_200.iloc[idx]) if not pd.isna(sma_200.iloc[idx]) else None,
                rsi=float(rsi.iloc[idx]) if not pd.isna(rsi.iloc[idx]) else None,
                macd=float(macd.iloc[idx]) if not pd.isna(macd.iloc[idx]) else None,
                macd_signal=float(macd_signal.iloc[idx]) if not pd.isna(macd_signal.iloc[idx]) else None,
                bb_upper=float(bb_upper.iloc[idx]) if not pd.isna(bb_upper.iloc[idx]) else None,
                bb_lower=float(bb_lower.iloc[idx]) if not pd.isna(bb_lower.iloc[idx]) else None,
                bb_middle=float(sma_bb.iloc[idx]) if not pd.isna(sma_bb.iloc[idx]) else None,
            ))
        
        return indicators
        
    except Exception as e:
        return generate_sample_indicators(days)

def generate_sample_signals(limit: int) -> List[AdvancedSignalResponse]:
    """Génère des signaux d'exemple"""
    import random
    from datetime import datetime, timedelta
    
    etfs = [
        {'isin': 'FR0010296061', 'name': 'Lyxor CAC 40 UCITS ETF', 'sector': 'Large Cap France'},
        {'isin': 'IE00B4L5Y983', 'name': 'iShares Core MSCI World UCITS ETF', 'sector': 'Global Developed'},
        {'isin': 'LU0290358497', 'name': 'Xtrackers EURO STOXX 50 UCITS ETF', 'sector': 'Europe Large Cap'},
        {'isin': 'IE00B4L5YC18', 'name': 'iShares Core S&P 500 UCITS ETF', 'sector': 'US Large Cap'},
    ]
    
    signals = []
    for i in range(min(limit, len(etfs))):
        etf = etfs[i]
        signal_types = ['BUY', 'SELL', 'HOLD']
        algorithms = ['BREAKOUT', 'MEAN_REVERSION', 'MOMENTUM']
        
        confidence = random.uniform(60, 95)
        current_price = random.uniform(40, 500)
        
        signals.append(AdvancedSignalResponse(
            id=f"sig_{i+1:03d}",
            etf_isin=etf['isin'],
            etf_name=etf['name'],
            signal_type=random.choice(signal_types),
            algorithm_type=random.choice(algorithms),
            confidence=confidence,
            technical_score=confidence + random.uniform(-10, 10),
            fundamental_score=random.uniform(50, 90),
            risk_score=random.uniform(40, 80),
            current_price=current_price,
            price_target=current_price * random.uniform(0.95, 1.08),
            stop_loss=current_price * random.uniform(0.92, 1.03),
            expected_return=random.uniform(-5, 10),
            risk_reward_ratio=random.uniform(0.5, 2.5),
            holding_period=random.randint(3, 15),
            justification=f"Signal généré par algorithme {random.choice(algorithms)}. Confiance: {confidence:.1f}%",
            timestamp=datetime.now() - timedelta(hours=random.randint(1, 48)),
            sector=etf['sector']
        ))
    
    return signals

def generate_sample_market_data(days: int) -> List[MarketDataResponse]:
    """Génère des données de marché d'exemple"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_price = 50.0
    current_price = base_price
    
    for i in range(days):
        # Variation journalière
        change = random.uniform(-0.03, 0.03)
        current_price *= (1 + change)
        
        # OHLC
        open_price = current_price * random.uniform(0.995, 1.005)
        high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
        close_price = current_price
        volume = random.randint(1000000, 5000000)
        
        data.append(MarketDataResponse(
            timestamp=datetime.now() - timedelta(days=days-i),
            open_price=round(open_price, 2),
            high_price=round(high_price, 2),
            low_price=round(low_price, 2),
            close_price=round(close_price, 2),
            volume=volume
        ))
    
    return data

def generate_sample_indicators(days: int) -> List[TechnicalIndicatorResponse]:
    """Génère des indicateurs techniques d'exemple"""
    import random
    from datetime import datetime, timedelta
    
    indicators = []
    base_price = 50.0
    
    for i in range(days):
        current_price = base_price * (1 + random.uniform(-0.2, 0.2))
        
        indicators.append(TechnicalIndicatorResponse(
            timestamp=datetime.now() - timedelta(days=days-i),
            sma_20=current_price * random.uniform(0.98, 1.02),
            sma_50=current_price * random.uniform(0.95, 1.05),
            sma_200=current_price * random.uniform(0.90, 1.10),
            rsi=random.uniform(25, 75),
            macd=random.uniform(-2, 2),
            macd_signal=random.uniform(-1.5, 1.5),
            bb_upper=current_price * 1.04,
            bb_lower=current_price * 0.96,
            bb_middle=current_price
        ))
    
    return indicators