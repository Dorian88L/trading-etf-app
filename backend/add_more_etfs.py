#!/usr/bin/env python3

"""
Script pour ajouter beaucoup plus d'ETFs européens réels
"""

import psycopg2
from datetime import datetime, timedelta
import random

# Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "database": "trading_etf",
    "user": "trading_user",
    "password": "trading_password"
}

# Plus d'ETFs européens réels
EUROPEAN_ETFS = [
    # ETFs iShares
    {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World UCITS ETF", "sector": "Global Developed", "currency": "USD", "ter": 0.0020, "aum": 50000000000, "exchange": "Xetra"},
    {"isin": "IE00B4L5YC18", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Large Cap", "currency": "USD", "ter": 0.0007, "aum": 75000000000, "exchange": "LSE"},
    {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Large Cap", "currency": "USD", "ter": 0.0007, "aum": 75000000000, "exchange": "LSE"},
    {"isin": "IE00BKM4GZ66", "name": "iShares Core MSCI EM IMI UCITS ETF", "sector": "Emerging Markets", "currency": "USD", "ter": 0.0018, "aum": 12000000000, "exchange": "Xetra"},
    {"isin": "IE00B53SZB19", "name": "iShares NASDAQ 100 UCITS ETF", "sector": "US Technology", "currency": "USD", "ter": 0.0033, "aum": 8500000000, "exchange": "Xetra"},
    {"isin": "IE00B52MJY50", "name": "iShares Core FTSE 100 UCITS ETF", "sector": "UK Large Cap", "currency": "GBP", "ter": 0.0007, "aum": 15000000000, "exchange": "LSE"},
    {"isin": "IE00B1YZSC51", "name": "iShares Core EURO STOXX 50 UCITS ETF", "sector": "European Large Cap", "currency": "EUR", "ter": 0.0010, "aum": 8000000000, "exchange": "Xetra"},
    {"isin": "IE00B4ND3602", "name": "iShares MSCI Japan UCITS ETF", "sector": "Japan", "currency": "USD", "ter": 0.0048, "aum": 6000000000, "exchange": "LSE"},
    {"isin": "IE00B14X4M10", "name": "iShares MSCI Europe UCITS ETF", "sector": "European Developed", "currency": "EUR", "ter": 0.0012, "aum": 4500000000, "exchange": "Xetra"},
    {"isin": "IE00B02KXL92", "name": "iShares Core DAX UCITS ETF", "sector": "Germany Large Cap", "currency": "EUR", "ter": 0.0016, "aum": 7500000000, "exchange": "Xetra"},
    
    # ETFs Vanguard
    {"isin": "IE00BK5BQT80", "name": "Vanguard FTSE All-World UCITS ETF", "sector": "Global All Cap", "currency": "USD", "ter": 0.0022, "aum": 25000000000, "exchange": "Euronext Amsterdam"},
    {"isin": "IE00B3XXRP09", "name": "Vanguard S&P 500 UCITS ETF", "sector": "US Large Cap", "currency": "USD", "ter": 0.0007, "aum": 35000000000, "exchange": "Euronext Amsterdam"},
    {"isin": "IE00BKX55T58", "name": "Vanguard FTSE Developed World UCITS ETF", "sector": "Global Developed", "currency": "USD", "ter": 0.0012, "aum": 18000000000, "exchange": "Euronext Amsterdam"},
    {"isin": "IE00BFMXXD54", "name": "Vanguard FTSE Emerging Markets UCITS ETF", "sector": "Emerging Markets", "currency": "USD", "ter": 0.0022, "aum": 8500000000, "exchange": "Euronext Amsterdam"},
    {"isin": "IE00B945VV12", "name": "Vanguard FTSE Developed Europe UCITS ETF", "sector": "European Developed", "currency": "EUR", "ter": 0.0010, "aum": 12000000000, "exchange": "Euronext Amsterdam"},
    {"isin": "IE00BZ163L38", "name": "Vanguard EUR Eurozone Government Bond UCITS ETF", "sector": "European Government Bonds", "currency": "EUR", "ter": 0.0007, "aum": 4500000000, "exchange": "Euronext Amsterdam"},
    
    # ETFs Xtrackers (DWS)
    {"isin": "LU0290358497", "name": "Xtrackers EURO STOXX 50 UCITS ETF", "sector": "European Large Cap", "currency": "EUR", "ter": 0.0009, "aum": 8500000000, "exchange": "Xetra"},
    {"isin": "LU0274208692", "name": "Xtrackers MSCI Emerging Markets UCITS ETF", "sector": "Emerging Markets", "currency": "USD", "ter": 0.0018, "aum": 12000000000, "exchange": "Xetra"},
    {"isin": "IE00BJ0KDQ92", "name": "Xtrackers MSCI World UCITS ETF", "sector": "Global Developed", "currency": "USD", "ter": 0.0019, "aum": 15000000000, "exchange": "Xetra"},
    {"isin": "LU0274211480", "name": "Xtrackers DAX UCITS ETF", "sector": "Germany Large Cap", "currency": "EUR", "ter": 0.0009, "aum": 6000000000, "exchange": "Xetra"},
    {"isin": "LU0274210672", "name": "Xtrackers STOXX Europe 600 UCITS ETF", "sector": "European All Cap", "currency": "EUR", "ter": 0.0020, "aum": 4500000000, "exchange": "Xetra"},
    {"isin": "IE00BL25JM42", "name": "Xtrackers MSCI USA UCITS ETF", "sector": "US All Cap", "currency": "USD", "ter": 0.0007, "aum": 8000000000, "exchange": "Xetra"},
    
    # ETFs SPDR
    {"isin": "IE00B6YX5C33", "name": "SPDR MSCI ACWI UCITS ETF", "sector": "Global All Cap", "currency": "USD", "ter": 0.0040, "aum": 6000000000, "exchange": "LSE"},
    {"isin": "IE00B44Z5B48", "name": "SPDR FTSE EPRA Europe Real Estate UCITS ETF", "sector": "European Real Estate", "currency": "EUR", "ter": 0.0035, "aum": 2500000000, "exchange": "LSE"},
    {"isin": "IE00B4WXJG34", "name": "SPDR S&P 500 UCITS ETF", "sector": "US Large Cap", "currency": "USD", "ter": 0.0030, "aum": 45000000000, "exchange": "LSE"},
    
    # ETFs Lyxor (Amundi)
    {"isin": "FR0010296061", "name": "Lyxor CAC 40 UCITS ETF", "sector": "France Large Cap", "currency": "EUR", "ter": 0.0025, "aum": 2500000000, "exchange": "Euronext Paris"},
    {"isin": "LU1781541179", "name": "Lyxor Core STOXX Europe 600 UCITS ETF", "sector": "European All Cap", "currency": "EUR", "ter": 0.0007, "aum": 3500000000, "exchange": "Euronext Paris"},
    {"isin": "LU0252633754", "name": "Lyxor EURO STOXX 50 UCITS ETF", "sector": "European Large Cap", "currency": "EUR", "ter": 0.0020, "aum": 5000000000, "exchange": "Euronext Paris"},
    
    # ETFs sectoriels et thématiques
    {"isin": "IE00BYZK4552", "name": "iShares Global Clean Energy UCITS ETF", "sector": "Clean Energy", "currency": "USD", "ter": 0.0065, "aum": 4500000000, "exchange": "Xetra"},
    {"isin": "IE00B3WJKG14", "name": "iShares S&P 500 Information Technology Sector UCITS ETF", "sector": "US Technology", "currency": "USD", "ter": 0.0015, "aum": 6500000000, "exchange": "Xetra"},
    {"isin": "IE00BMYDM794", "name": "iShares Healthcare Innovation UCITS ETF", "sector": "Healthcare Innovation", "currency": "USD", "ter": 0.0040, "aum": 3000000000, "exchange": "Xetra"},
    {"isin": "IE00BZ114W33", "name": "iShares Electric Vehicles and Driving Technology UCITS ETF", "sector": "Electric Vehicles", "currency": "USD", "ter": 0.0040, "aum": 2500000000, "exchange": "Xetra"},
    {"isin": "IE00BYMS5208", "name": "iShares Digitalisation UCITS ETF", "sector": "Digitalisation", "currency": "USD", "ter": 0.0040, "aum": 2000000000, "exchange": "Xetra"},
    
    # ETFs obligataires
    {"isin": "IE00B4WXJH41", "name": "iShares Core Global Aggregate Bond UCITS ETF", "sector": "Global Bonds", "currency": "EUR", "ter": 0.0010, "aum": 8000000000, "exchange": "Xetra"},
    {"isin": "IE00B1FZS467", "name": "iShares Core EUR Govt Bond UCITS ETF", "sector": "European Government Bonds", "currency": "EUR", "ter": 0.0009, "aum": 12000000000, "exchange": "Xetra"},
    {"isin": "IE00B3VWN518", "name": "iShares EUR Corp Bond UCITS ETF", "sector": "European Corporate Bonds", "currency": "EUR", "ter": 0.0020, "aum": 6500000000, "exchange": "Xetra"},
    
    # ETFs matières premières
    {"isin": "IE00B4ND3616", "name": "iShares Physical Gold ETC", "sector": "Gold", "currency": "USD", "ter": 0.0025, "aum": 15000000000, "exchange": "LSE"},
    {"isin": "IE00B6R52259", "name": "iShares STOXX Europe 600 Oil & Gas UCITS ETF", "sector": "European Energy", "currency": "EUR", "ter": 0.0046, "aum": 1500000000, "exchange": "Xetra"},
    
    # ETFs dividendes
    {"isin": "IE00B0M62Q58", "name": "iShares EURO STOXX Select Dividend 30 UCITS ETF", "sector": "European High Dividend", "currency": "EUR", "ter": 0.0031, "aum": 3500000000, "exchange": "Xetra"},
    {"isin": "IE00B5M1WJ87", "name": "iShares STOXX Global Select Dividend 100 UCITS ETF", "sector": "Global High Dividend", "currency": "EUR", "ter": 0.0046, "aum": 2800000000, "exchange": "Xetra"},
    
    # ETFs small cap
    {"isin": "IE00B3BXQK04", "name": "iShares MSCI Europe Small Cap UCITS ETF", "sector": "European Small Cap", "currency": "EUR", "ter": 0.0058, "aum": 2000000000, "exchange": "Xetra"},
    {"isin": "IE00B3GDKV13", "name": "iShares MSCI USA Small Cap UCITS ETF", "sector": "US Small Cap", "currency": "USD", "ter": 0.0043, "aum": 4500000000, "exchange": "Xetra"},
    
    # ETFs pays spécifiques
    {"isin": "IE00BKM4GZ66", "name": "iShares Core MSCI EM IMI UCITS ETF", "sector": "Emerging Markets", "currency": "USD", "ter": 0.0018, "aum": 12000000000, "exchange": "Xetra"},
    {"isin": "IE00B4ND3602", "name": "iShares MSCI Japan UCITS ETF", "sector": "Japan", "currency": "USD", "ter": 0.0048, "aum": 6000000000, "exchange": "LSE"},
    {"isin": "IE00B4QJF196", "name": "iShares MSCI China UCITS ETF", "sector": "China", "currency": "USD", "ter": 0.0040, "aum": 3500000000, "exchange": "LSE"},
    {"isin": "IE00B0M63177", "name": "iShares MSCI India UCITS ETF", "sector": "India", "currency": "USD", "ter": 0.0065, "aum": 2800000000, "exchange": "LSE"},
]

def add_european_etfs():
    print(f"📊 Ajout de {len(EUROPEAN_ETFS)} ETFs européens réels...")
    
    added_count = 0
    existing_count = 0
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        for etf in EUROPEAN_ETFS:
            # Vérifier si l'ETF existe déjà
            cursor.execute("SELECT isin FROM etfs WHERE isin = %s", (etf["isin"],))
            existing = cursor.fetchone()
            
            if existing:
                existing_count += 1
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
            added_count += 1
            print(f"  ✅ {etf['name'][:50]}{'...' if len(etf['name']) > 50 else ''}")
        
        conn.commit()
        print(f"\n✅ {added_count} nouveaux ETFs ajoutés!")
        print(f"⚠️  {existing_count} ETFs existaient déjà")
        print(f"📊 Total ETFs en base: {added_count + existing_count}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

def add_market_data_for_new_etfs():
    print("📈 Ajout des données de marché pour les nouveaux ETFs...")
    
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Récupérer tous les ETFs qui n'ont pas de données de marché
        cursor.execute("""
            SELECT e.isin, e.name 
            FROM etfs e 
            LEFT JOIN market_data m ON e.isin = m.etf_isin 
            WHERE m.etf_isin IS NULL
        """)
        
        etfs_without_data = cursor.fetchall()
        
        if not etfs_without_data:
            print("  ℹ️  Tous les ETFs ont déjà des données de marché")
            return True
        
        print(f"  📊 Génération de données pour {len(etfs_without_data)} ETFs...")
        
        # Générer 30 jours de données pour chaque ETF
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for isin, name in etfs_without_data:
            base_price = random.uniform(20, 500)  # Prix de base aléatoire plus réaliste
            
            current_date = start_date
            current_price = base_price
            
            while current_date <= end_date:
                # Variation journalière aléatoire (-2% à +2%)
                daily_change = random.uniform(-0.02, 0.02)
                current_price *= (1 + daily_change)
                
                # Calcul des prix OHLC
                open_price = current_price * random.uniform(0.998, 1.002)
                high_price = max(open_price, current_price) * random.uniform(1.0, 1.015)
                low_price = min(open_price, current_price) * random.uniform(0.985, 1.0)
                close_price = current_price
                volume = random.randint(50000, 2000000)
                nav = close_price * random.uniform(0.9995, 1.0005)
                
                cursor.execute(
                    """
                    INSERT INTO market_data (time, etf_isin, open_price, high_price, low_price, close_price, volume, nav)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (current_date, isin, round(open_price, 4), round(high_price, 4), 
                     round(low_price, 4), round(close_price, 4), volume, round(nav, 4))
                )
                
                current_date += timedelta(days=1)
            
            print(f"  ✅ Données ajoutées pour {name[:50]}{'...' if len(name) > 50 else ''}")
        
        conn.commit()
        print(f"✅ Données de marché ajoutées pour {len(etfs_without_data)} ETFs!")
        
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
    print("🌍 Ajout d'ETFs européens réels pour l'application Trading ETF")
    print("=" * 70)
    
    try:
        success1 = add_european_etfs()
        success2 = add_market_data_for_new_etfs()
        
        if success1 and success2:
            print("\n🎉 ETFs européens ajoutés avec succès!")
            print(f"📊 L'application dispose maintenant de {len(EUROPEAN_ETFS)} ETFs européens réels")
            print("🌐 Redémarrez l'application pour voir tous les nouveaux ETFs")
    except KeyboardInterrupt:
        print("\n❌ Opération annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")