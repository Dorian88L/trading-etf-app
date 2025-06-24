#!/usr/bin/env python3
"""
Test rapide du scraping depuis le conteneur Docker
"""

import asyncio
import sys
import os
sys.path.append('/home/app')

from app.services.etf_scraping_service import ETFScrapingService
from app.services.historical_data_service import HistoricalDataService

async def test_scraping():
    """Test du scraping en temps réel"""
    print("=== TEST SCRAPING TEMPS RÉEL ===")
    
    scraping_service = ETFScrapingService()
    
    # Test avec les principaux ETFs européens
    test_isins = [
        "IE00B5BMR087",  # iShares Core S&P 500 (CSPX)
        "IE00B4L5Y983",  # iShares Core MSCI World (IWDA)
        "IE00BK5BQT80",  # Vanguard FTSE All-World (VWRL)
    ]
    
    for isin in test_isins:
        print(f"\n--- Test {isin} ---")
        try:
            data = await scraping_service.scrape_etf_data(isin)
            if data:
                print(f"✅ {data.name}")
                print(f"   Prix: {data.current_price} {data.currency}")
                print(f"   Variation: {data.change} ({data.change_percent}%)")
                print(f"   Source: {data.source}")
                print(f"   Confiance: {data.confidence_score:.2f}")
            else:
                print(f"❌ Aucune donnée obtenue")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    await scraping_service.close()

async def test_historical():
    """Test des données historiques"""
    print("\n=== TEST DONNÉES HISTORIQUES ===")
    
    historical_service = HistoricalDataService()
    
    # Test avec un seul ETF
    test_isin = "IE00B5BMR087"  # CSPX
    
    print(f"\n--- Test historique {test_isin} ---")
    try:
        data = await historical_service.get_historical_data(test_isin, "1mo")
        if data:
            print(f"✅ {len(data)} points de données historiques")
            print(f"   Premier point: {data[0].date} - {data[0].close_price}")
            print(f"   Dernier point: {data[-1].date} - {data[-1].close_price}")
        else:
            print(f"❌ Aucune donnée historique obtenue")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    await historical_service.close()

if __name__ == "__main__":
    print("🔍 Test du scraping ETF depuis Docker")
    
    # Test scraping temps réel
    asyncio.run(test_scraping())
    
    # Test données historiques
    asyncio.run(test_historical())
    
    print("\n✅ Tests terminés")