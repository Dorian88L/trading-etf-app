#!/usr/bin/env python3
"""
Script simple pour initialiser les données de base
"""
import os
import sys
sys.path.append('.')

# Configuration de l'environnement
os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5434/trading_etf'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid
import random

def init_basic_data():
    """Initialiser les données de base sans les modèles complexes"""
    
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🗄️ Ajout des données de base...")
        
        # Créer un utilisateur de test simple
        user_id = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified)
            VALUES (:id, :email, :password, :name, true, true)
            ON CONFLICT (email) DO NOTHING
        """), {
            'id': user_id,
            'email': 'test@trading.com',
            'password': '$2b$12$1234567890abcdefghijklmnopqrstuvwxyz',  # test123
            'name': 'Test User Trading'
        })
        
        # Ajouter des ETFs réels européens
        etfs = [
            ('IE00B4L5Y983', 'iShares Core MSCI World UCITS ETF (IWDA)', 'Global Equity'),
            ('IE00BK5BQT80', 'Vanguard FTSE All-World UCITS ETF (VWCE)', 'Global Equity'),
            ('IE00B5BMR087', 'iShares Core S&P 500 UCITS ETF (CSPX)', 'US Equity'),
            ('IE00B3RBWM25', 'Vanguard FTSE Developed Europe UCITS ETF (VEUR)', 'European Equity'),
            ('IE00B42Z5J44', 'SPDR S&P 500 UCITS ETF (SPY5)', 'US Equity'),
            ('LU0274208692', 'Xtrackers MSCI World UCITS ETF (XMWO)', 'Global Equity'),
            ('IE00B0M62Q58', 'iShares MSCI Europe UCITS ETF (IMEU)', 'European Equity'),
            ('IE00B4WXJJ64', 'iShares Core MSCI Emerging Markets UCITS ETF (IEMG)', 'Emerging Markets')
        ]
        
        for isin, name, sector in etfs:
            session.execute(text("""
                INSERT INTO etfs (isin, name, sector, currency, ter, aum, exchange)
                VALUES (:isin, :name, :sector, 'EUR', 0.0025, 1000000000, 'XETRA')
                ON CONFLICT (isin) DO NOTHING
            """), {
                'isin': isin,
                'name': name,
                'sector': sector
            })
        
        # Ajouter quelques données de marché récentes
        base_price = 100.0
        now = datetime.utcnow()
        
        for isin, name, sector in etfs[:3]:  # Seulement pour les 3 premiers ETFs
            for i in range(30):  # 30 jours de données
                date = now - timedelta(days=i)
                price = base_price + random.uniform(-5, 5)
                
                session.execute(text("""
                    INSERT INTO market_data (time, etf_isin, open_price, high_price, low_price, close_price, volume)
                    VALUES (:time, :isin, :open, :high, :low, :close, :volume)
                    ON CONFLICT (time, etf_isin) DO NOTHING
                """), {
                    'time': date,
                    'isin': isin,
                    'open': price,
                    'high': price + random.uniform(0, 2),
                    'low': price - random.uniform(0, 2),
                    'close': price + random.uniform(-1, 1),
                    'volume': random.randint(100000, 1000000)
                })
        
        # Ajouter quelques signaux d'exemple
        for isin, name, sector in etfs[:3]:
            signal_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO signals (id, etf_isin, signal_type, confidence, price_target, technical_score, is_active)
                VALUES (:id, :isin, :type, :confidence, :target, :score, true)
                ON CONFLICT (id) DO NOTHING
            """), {
                'id': signal_id,
                'isin': isin,
                'type': random.choice(['BUY', 'SELL', 'HOLD']),
                'confidence': random.uniform(70, 95),
                'target': base_price + random.uniform(-10, 10),
                'score': random.uniform(60, 90)
            })
        
        session.commit()
        print("✅ Données de base ajoutées avec succès!")
        print(f"👤 Utilisateur: test@trading.com / test123")
        print(f"📊 {len(etfs)} ETFs ajoutés")
        print("📈 Données de marché et signaux générés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = init_basic_data()
    sys.exit(0 if success else 1)