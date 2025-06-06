#!/usr/bin/env python3

"""
Script pour ajouter des données d'exemple d'ETFs
"""

import psycopg2
from datetime import datetime, timedelta
import random

# Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "trading_etf",
    "user": "trading_user",
    "password": "trading_password"
}

# ETFs d'exemple
SAMPLE_ETFS = [
    {
        "isin": "FR0010296061",
        "name": "Lyxor CAC 40 UCITS ETF",
        "sector": "Large Cap",
        "currency": "EUR",
        "ter": 0.0025,
        "aum": 2500000000,
        "exchange": "Euronext Paris"
    },
    {
        "isin": "IE00B4L5Y983", 
        "name": "iShares Core MSCI World UCITS ETF USD",
        "sector": "Global",
        "currency": "USD",
        "ter": 0.0020,
        "aum": 50000000000,
        "exchange": "Xetra"
    },
    {
        "isin": "LU0290358497",
        "name": "Xtrackers EURO STOXX 50 UCITS ETF",
        "sector": "Large Cap",
        "currency": "EUR", 
        "ter": 0.0009,
        "aum": 8500000000,
        "exchange": "Xetra"
    },
    {
        "isin": "IE00B4L5YC18",
        "name": "iShares Core S&P 500 UCITS ETF",
        "sector": "US Large Cap",
        "currency": "USD",
        "ter": 0.0007,
        "aum": 75000000000,
        "exchange": "London Stock Exchange"
    },
    {
        "isin": "LU0274208692",
        "name": "Xtrackers MSCI Emerging Markets UCITS ETF",
        "sector": "Emerging Markets",
        "currency": "USD",
        "ter": 0.0018,
        "aum": 12000000000,
        "exchange": "Xetra"
    }
]

def add_sample_etfs():
    print("📊 Ajout des ETFs d'exemple...")
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        for etf in SAMPLE_ETFS:
            # Vérifier si l'ETF existe déjà
            cursor.execute("SELECT isin FROM etfs WHERE isin = %s", (etf["isin"],))
            existing = cursor.fetchone()
            
            if existing:
                print(f"  ⚠️  ETF {etf['name']} existe déjà")
                continue
            
            # Insérer l'ETF
            cursor.execute(
                """
                INSERT INTO etfs (isin, name, sector, currency, ter, aum, exchange)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    etf["isin"],
                    etf["name"],
                    etf["sector"],
                    etf["currency"],
                    etf["ter"],
                    etf["aum"],
                    etf["exchange"]
                )
            )
            print(f"  ✅ {etf['name']} ajouté")
        
        conn.commit()
        print("✅ ETFs d'exemple ajoutés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

def add_sample_market_data():
    print("📈 Ajout des données de marché d'exemple...")
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Générer 30 jours de données pour chaque ETF
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for etf in SAMPLE_ETFS:
            isin = etf["isin"]
            base_price = random.uniform(50, 300)  # Prix de base aléatoire
            
            current_date = start_date
            current_price = base_price
            
            while current_date <= end_date:
                # Variation journalière aléatoire (-3% à +3%)
                daily_change = random.uniform(-0.03, 0.03)
                current_price *= (1 + daily_change)
                
                # Calcul des prix OHLC
                open_price = current_price * random.uniform(0.995, 1.005)
                high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
                low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
                close_price = current_price
                volume = random.randint(100000, 5000000)
                nav = close_price * random.uniform(0.999, 1.001)
                
                # Vérifier si les données existent déjà
                cursor.execute(
                    "SELECT time FROM market_data WHERE time = %s AND etf_isin = %s",
                    (current_date, isin)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO market_data (time, etf_isin, open_price, high_price, low_price, close_price, volume, nav)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (current_date, isin, round(open_price, 4), round(high_price, 4), 
                         round(low_price, 4), round(close_price, 4), volume, round(nav, 4))
                    )
                
                current_date += timedelta(days=1)
            
            print(f"  ✅ Données ajoutées pour {etf['name']}")
        
        conn.commit()
        print("✅ Données de marché ajoutées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("📦 Ajout de données d'exemple pour l'application Trading ETF")
    print("=" * 60)
    
    try:
        success1 = add_sample_etfs()
        success2 = add_sample_market_data()
        
        if success1 and success2:
            print("\n🎉 Données d'exemple ajoutées avec succès!")
            print("🌐 Accédez à l'application sur: http://localhost:3000")
            print("🔐 Connectez-vous avec: test@trading.com / test123")
    except KeyboardInterrupt:
        print("\n❌ Opération annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")