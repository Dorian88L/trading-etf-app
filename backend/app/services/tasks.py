from celery import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
from typing import List

from app.celery_app import celery_app
from app.core.config import settings
from app.models.etf import ETF, MarketData, TechnicalIndicators
from app.models.signal import Signal
from app.services.market_data import MarketDataProvider, get_symbol_from_isin
from app.services.technical_analysis import TechnicalAnalyzer, SignalGenerator

# Database setup for Celery tasks
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(bind=True)
def collect_market_data(self):
    """Collect market data for all ETFs"""
    try:
        db = get_db_session()
        provider = MarketDataProvider()
        
        # Get all ETFs
        etfs = db.query(ETF).all()
        
        for etf in etfs:
            try:
                symbol = get_symbol_from_isin(etf.isin)
                if not symbol:
                    continue
                
                # Get market data
                data = await provider.get_etf_data(symbol)
                if not data:
                    continue
                
                # Save to database
                market_data = MarketData(
                    time=data['timestamp'],
                    etf_isin=etf.isin,
                    open_price=data['open'],
                    high_price=data['high'],
                    low_price=data['low'],
                    close_price=data['close'],
                    volume=data['volume'],
                    nav=data.get('nav')
                )
                
                db.add(market_data)
                db.commit()
                
            except Exception as e:
                print(f"Error processing ETF {etf.isin}: {e}")
                continue
        
        await provider.close()
        db.close()
        
        return f"Collected market data for {len(etfs)} ETFs"
        
    except Exception as e:
        print(f"Error in collect_market_data: {e}")
        return f"Error: {e}"


@celery_app.task(bind=True)
def update_technical_indicators(self):
    """Update technical indicators for all ETFs"""
    try:
        db = get_db_session()
        analyzer = TechnicalAnalyzer()
        
        # Get all ETFs
        etfs = db.query(ETF).all()
        
        for etf in etfs:
            try:
                # Get recent market data (last 200 periods for proper calculation)
                market_data_query = (
                    db.query(MarketData)
                    .filter(MarketData.etf_isin == etf.isin)
                    .order_by(MarketData.time.desc())
                    .limit(200)
                )
                
                market_data = pd.read_sql(
                    market_data_query.statement,
                    con=engine,
                    index_col='time'
                ).sort_index()
                
                if market_data.empty:
                    continue
                
                # Calculate technical indicators
                tech_data = analyzer.analyze_etf(market_data)
                if not tech_data:
                    continue
                
                # Save technical indicators
                indicators = TechnicalIndicators(
                    time=tech_data['timestamp'],
                    etf_isin=etf.isin,
                    sma_20=tech_data.get('sma_20'),
                    sma_50=tech_data.get('sma_50'),
                    sma_200=tech_data.get('sma_200'),
                    ema_20=tech_data.get('ema_20'),
                    ema_50=tech_data.get('ema_50'),
                    rsi=tech_data.get('rsi'),
                    macd=tech_data.get('macd'),
                    macd_signal=tech_data.get('macd_signal'),
                    macd_histogram=tech_data.get('macd_histogram'),
                    bb_upper=tech_data.get('bb_upper'),
                    bb_middle=tech_data.get('bb_middle'),
                    bb_lower=tech_data.get('bb_lower'),
                    atr=tech_data.get('atr'),
                    obv=tech_data.get('obv'),
                    vwap=tech_data.get('vwap')
                )
                
                db.add(indicators)
                db.commit()
                
            except Exception as e:
                print(f"Error processing indicators for ETF {etf.isin}: {e}")
                continue
        
        db.close()
        return f"Updated technical indicators for {len(etfs)} ETFs"
        
    except Exception as e:
        print(f"Error in update_technical_indicators: {e}")
        return f"Error: {e}"


@celery_app.task(bind=True)
def generate_trading_signals(self):
    """Generate trading signals for all ETFs"""
    try:
        db = get_db_session()
        signal_generator = SignalGenerator()
        
        # Get all ETFs
        etfs = db.query(ETF).all()
        signals_created = 0
        
        for etf in etfs:
            try:
                # Get recent market data
                market_data_query = (
                    db.query(MarketData)
                    .filter(MarketData.etf_isin == etf.isin)
                    .order_by(MarketData.time.desc())
                    .limit(100)
                )
                
                market_data = pd.read_sql(
                    market_data_query.statement,
                    con=engine,
                    index_col='time'
                ).sort_index()
                
                if market_data.empty:
                    continue
                
                # Get latest technical indicators
                latest_tech = (
                    db.query(TechnicalIndicators)
                    .filter(TechnicalIndicators.etf_isin == etf.isin)
                    .order_by(TechnicalIndicators.time.desc())
                    .first()
                )
                
                if not latest_tech:
                    continue
                
                # Convert to dict for signal generation
                tech_data = {
                    'sma_20': float(latest_tech.sma_20) if latest_tech.sma_20 else None,
                    'sma_50': float(latest_tech.sma_50) if latest_tech.sma_50 else None,
                    'sma_200': float(latest_tech.sma_200) if latest_tech.sma_200 else None,
                    'ema_20': float(latest_tech.ema_20) if latest_tech.ema_20 else None,
                    'ema_50': float(latest_tech.ema_50) if latest_tech.ema_50 else None,
                    'rsi': float(latest_tech.rsi) if latest_tech.rsi else None,
                    'macd': float(latest_tech.macd) if latest_tech.macd else None,
                    'macd_signal': float(latest_tech.macd_signal) if latest_tech.macd_signal else None,
                    'macd_histogram': float(latest_tech.macd_histogram) if latest_tech.macd_histogram else None,
                    'bb_upper': float(latest_tech.bb_upper) if latest_tech.bb_upper else None,
                    'bb_middle': float(latest_tech.bb_middle) if latest_tech.bb_middle else None,
                    'bb_lower': float(latest_tech.bb_lower) if latest_tech.bb_lower else None,
                    'atr': float(latest_tech.atr) if latest_tech.atr else None,
                    'obv': int(latest_tech.obv) if latest_tech.obv else None,
                    'vwap': float(latest_tech.vwap) if latest_tech.vwap else None,
                }
                
                # Generate signal
                signal_data = signal_generator.generate_signal(etf.isin, market_data, tech_data)
                if not signal_data:
                    continue
                
                # Check if we should create a new signal
                # Only create if confidence is above minimum threshold
                if signal_data['confidence'] < settings.MIN_SIGNAL_CONFIDENCE:
                    continue
                
                # Deactivate old signals for this ETF
                db.query(Signal).filter(
                    Signal.etf_isin == etf.isin,
                    Signal.is_active == True
                ).update({"is_active": False})
                
                # Create new signal
                signal = Signal(
                    etf_isin=signal_data['etf_isin'],
                    signal_type=signal_data['signal_type'],
                    confidence=signal_data['confidence'],
                    technical_score=signal_data['technical_score'],
                    fundamental_score=signal_data['fundamental_score'],
                    risk_score=signal_data['risk_score'],
                    price_target=signal_data['price_target'],
                    stop_loss=signal_data['stop_loss'],
                    expires_at=datetime.utcnow() + timedelta(hours=24)  # 24h expiry
                )
                
                db.add(signal)
                db.commit()
                signals_created += 1
                
            except Exception as e:
                print(f"Error generating signal for ETF {etf.isin}: {e}")
                continue
        
        db.close()
        return f"Generated {signals_created} trading signals"
        
    except Exception as e:
        print(f"Error in generate_trading_signals: {e}")
        return f"Error: {e}"


@celery_app.task(bind=True)
def cleanup_expired_signals(self):
    """Clean up expired signals"""
    try:
        db = get_db_session()
        
        # Deactivate expired signals
        expired_count = (
            db.query(Signal)
            .filter(
                Signal.expires_at < datetime.utcnow(),
                Signal.is_active == True
            )
            .update({"is_active": False})
        )
        
        db.commit()
        db.close()
        
        return f"Deactivated {expired_count} expired signals"
        
    except Exception as e:
        print(f"Error in cleanup_expired_signals: {e}")
        return f"Error: {e}"


@celery_app.task(bind=True)
def send_signal_alerts(self, signal_id: str):
    """Send alerts for new trading signals"""
    try:
        db = get_db_session()
        
        # Get signal
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            return "Signal not found"
        
        # Get users who have this ETF in watchlist
        from app.models.watchlist import Watchlist
        from app.models.alert import Alert, AlertType
        
        watchlist_users = (
            db.query(Watchlist)
            .filter(Watchlist.etf_isin == signal.etf_isin)
            .all()
        )
        
        alerts_created = 0
        for watchlist_item in watchlist_users:
            # Create alert for user
            alert = Alert(
                user_id=watchlist_item.user_id,
                alert_type=AlertType.SIGNAL,
                title=f"New {signal.signal_type} Signal",
                message=f"ETF {signal.etf_isin}: {signal.signal_type} signal with {signal.confidence}% confidence",
                etf_isin=signal.etf_isin
            )
            db.add(alert)
            alerts_created += 1
        
        db.commit()
        db.close()
        
        return f"Created {alerts_created} alerts for signal {signal_id}"
        
    except Exception as e:
        print(f"Error in send_signal_alerts: {e}")
        return f"Error: {e}"