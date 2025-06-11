#!/usr/bin/env python3
"""
Script pour peupler la base de données avec des ETFs européens réels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def populate_etfs():
    """Ajoute des ETFs européens populaires directement en SQL"""
    
    # Connexion directe à la base
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier si des ETFs existent déjà
        result = session.execute(text("SELECT COUNT(*) FROM etfs"))
        count = result.scalar()
        
        if count > 0:
            print(f"✅ {count} ETFs déjà présents en base")
            return
        
        print("🚀 Ajout d'ETFs européens populaires...")
        
        # ETFs européens avec données réelles
        etfs_sql = """
        INSERT INTO etfs (isin, name, sector, currency, ter, aum, exchange, created_at, updated_at) 
        VALUES 
        ('IE00B4L5Y983', 'iShares Core MSCI World UCITS ETF USD (Acc)', 'Global Equity', 'USD', 0.20, 20000000000, 'XETRA', NOW(), NOW()),
        ('IE00BK5BQT80', 'Vanguard FTSE All-World UCITS ETF USD Acc', 'Global Equity', 'USD', 0.22, 15000000000, 'XETRA', NOW(), NOW()),
        ('IE00B5BMR087', 'iShares Core S&P 500 UCITS ETF USD Acc', 'US Large Cap', 'USD', 0.07, 30000000000, 'London', NOW(), NOW()),
        ('IE00B3XXRP09', 'Vanguard S&P 500 UCITS ETF', 'US Large Cap', 'USD', 0.07, 25000000000, 'XETRA', NOW(), NOW()),
        ('LU0274208692', 'Xtrackers MSCI World UCITS ETF 1C', 'Global Equity', 'USD', 0.19, 8000000000, 'XETRA', NOW(), NOW()),
        ('FR0010315770', 'Amundi CAC 40 UCITS ETF DR', 'French Large Cap', 'EUR', 0.25, 1500000000, 'Euronext Paris', NOW(), NOW()),
        ('DE0005933931', 'iShares Core DAX UCITS ETF', 'German Large Cap', 'EUR', 0.16, 6000000000, 'XETRA', NOW(), NOW()),
        ('IE00BKM4GZ66', 'iShares Core MSCI EM IMI UCITS ETF', 'Emerging Markets', 'USD', 0.18, 12000000000, 'London', NOW(), NOW()),
        ('IE00B52VJ196', 'iShares Core EURO STOXX 50 UCITS ETF', 'European Large Cap', 'EUR', 0.10, 8500000000, 'XETRA', NOW(), NOW()),
        ('LU1681043599', 'Amundi Prime Global UCITS ETF DR', 'Global Equity', 'USD', 0.05, 3000000000, 'XETRA', NOW(), NOW()),
        ('IE00BJ0KDQ92', 'Xtrackers MSCI World UCITS ETF 1C', 'Global Equity', 'USD', 0.19, 12000000000, 'XETRA', NOW(), NOW()),
        ('LU1681043672', 'Amundi Prime Europe UCITS ETF DR', 'European Equity', 'EUR', 0.05, 2000000000, 'XETRA', NOW(), NOW()),
        ('IE00B4L5YV64', 'iShares Core FTSE 100 UCITS ETF', 'UK Large Cap', 'GBP', 0.07, 15000000000, 'London', NOW(), NOW()),
        ('FR0010429068', 'Lyxor CAC 40 (DR) UCITS ETF', 'French Large Cap', 'EUR', 0.25, 2500000000, 'Euronext Paris', NOW(), NOW()),
        ('LU0908500753', 'Lyxor Core STOXX Europe 600 UCITS ETF', 'European Equity', 'EUR', 0.07, 8000000000, 'XETRA', NOW(), NOW()),
        ('IE00BKX55Q28', 'Vanguard ESG Developed World All Cap Equity Index Fund', 'ESG Global Equity', 'USD', 0.12, 5000000000, 'London', NOW(), NOW()),
        ('IE00BYYR0935', 'Vanguard ESG Emerging Markets All Cap UCITS ETF', 'ESG Emerging Markets', 'USD', 0.24, 1500000000, 'London', NOW(), NOW()),
        ('LU0496786574', 'Lyxor MSCI Eastern Europe ex Russia UCITS ETF', 'Eastern Europe', 'EUR', 0.50, 800000000, 'XETRA', NOW(), NOW()),
        ('IE00BFMXXD54', 'iShares MSCI Europe SRI UCITS ETF', 'ESG European Equity', 'EUR', 0.20, 3000000000, 'XETRA', NOW(), NOW()),
        ('LU2115027975', 'Amundi CAC 40 ESG UCITS ETF DR', 'ESG French Large Cap', 'EUR', 0.25, 500000000, 'Euronext Paris', NOW(), NOW())
        """
        
        session.execute(text(etfs_sql))
        session.commit()
        
        # Vérifier le résultat
        result = session.execute(text("SELECT COUNT(*) FROM etfs"))
        new_count = result.scalar()
        
        print(f"✅ {new_count} ETFs ajoutés avec succès à la base de données")
        
        # Afficher quelques exemples
        examples = session.execute(text("SELECT name, currency, sector FROM etfs LIMIT 5")).fetchall()
        print("\n📊 Exemples d'ETFs ajoutés:")
        for etf in examples:
            print(f"   • {etf[0]} ({etf[1]}) - {etf[2]}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    populate_etfs()