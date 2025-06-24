#!/usr/bin/env python3
"""
Script de debug pour analyser le problème de prix avec CSPX.L
"""

import sys
import os
sys.path.append('/home/dorian/trading-etf-app/backend')

import asyncio
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_cspx_price():
    """Analyse le prix de CSPX depuis différentes sources"""
    
    print("=== DEBUG CSPX PRICE ANALYSIS ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Import des services
    try:
        from app.services.multi_source_etf_data import MultiSourceETFDataService
        from app.services.etf_scraping_service import ETFScrapingService
    except ImportError as e:
        print(f"Erreur d'import: {e}")
        return
    
    # Initialisation des services
    api_service = MultiSourceETFDataService()
    scraping_service = ETFScrapingService()
    
    # ISIN pour CSPX
    cspx_isin = "IE00B5BMR087"
    
    print("1. Analyse de la configuration CSPX dans multi_source_etf_data.py")
    print("-" * 60)
    
    cspx_configs = {}
    for symbol, config in api_service.european_etfs.items():
        if config.get('isin') == cspx_isin:
            cspx_configs[symbol] = config
            print(f"Symbole: {symbol}")
            print(f"  - Nom: {config.get('name')}")
            print(f"  - Bourse: {config.get('exchange')}")
            print(f"  - Secteur: {config.get('sector')}")
            print()
    
    print("2. Test du meilleur symbole mappé")
    print("-" * 40)
    best_symbol = api_service.isin_to_best_symbol.get(cspx_isin)
    print(f"Meilleur symbole pour {cspx_isin}: {best_symbol}")
    print()
    
    print("3. Test de récupération des données via API")
    print("-" * 50)
    
    # Test avec différents symboles
    symbols_to_test = ["CSPX.L", "CSPX.AS", "CSPX.PA"]
    
    for symbol in symbols_to_test:
        print(f"\n--- Test de {symbol} ---")
        try:
            # Test Yahoo Finance direct
            data = await api_service._get_yahoo_finance_data(symbol)
            if data:
                print(f"Yahoo Finance: {data.current_price} {data.currency}")
                print(f"  - Changement: {data.change}")
                print(f"  - % Changement: {data.change_percent}")
                print(f"  - Volume: {data.volume}")
                print(f"  - Confiance: {data.confidence_score}")
            else:
                print("Yahoo Finance: Pas de données")
        except Exception as e:
            print(f"Yahoo Finance: Erreur - {e}")
    
    print("\n4. Test de scraping")
    print("-" * 30)
    
    try:
        scraped_data = await scraping_service.scrape_etf_data(cspx_isin)
        if scraped_data:
            print(f"Scraping: {scraped_data.current_price} {scraped_data.currency}")
            print(f"  - Source: {scraped_data.source}")
            print(f"  - Changement: {scraped_data.change}")
            print(f"  - % Changement: {scraped_data.change_percent}")
            print(f"  - Confiance: {scraped_data.confidence_score}")
        else:
            print("Scraping: Pas de données")
    except Exception as e:
        print(f"Scraping: Erreur - {e}")
    
    print("\n5. Test de la méthode get_etf_data complète")
    print("-" * 50)
    
    try:
        final_data = await api_service.get_etf_data("CSPX.L")
        if final_data:
            print(f"Final: {final_data.current_price} {final_data.currency}")
            print(f"  - Source: {final_data.source}")
            print(f"  - Bourse: {final_data.exchange}")
            print(f"  - Confiance: {final_data.confidence_score}")
            print(f"  - Qualité: {final_data.data_quality}")
        else:
            print("Final: Pas de données")
    except Exception as e:
        print(f"Final: Erreur - {e}")
    
    print("\n6. Test de la méthode par ISIN")
    print("-" * 40)
    
    try:
        isin_data = await api_service.get_etf_data_by_isin(cspx_isin)
        if isin_data:
            print(f"Par ISIN: {isin_data.current_price} {isin_data.currency}")
            print(f"  - Symbole utilisé: {isin_data.symbol}")
            print(f"  - Source: {isin_data.source}")
        else:
            print("Par ISIN: Pas de données")
    except Exception as e:
        print(f"Par ISIN: Erreur - {e}")
    
    # Analyse des conversions possibles
    print("\n7. Analyse des conversions possibles")
    print("-" * 45)
    
    # Supposons qu'on ait un prix de 638€ au lieu de 553€
    incorrect_price = 638.0
    expected_price = 553.0
    
    # Ratio de conversion
    ratio = incorrect_price / expected_price
    print(f"Ratio prix incorrect/attendu: {ratio:.4f}")
    
    # Conversions possibles
    gbp_to_eur_rate = 1.15  # Approximation
    pence_to_pounds = 100.0
    
    # Conversion pence -> livres -> euros
    if abs(ratio - (pence_to_eur_rate := gbp_to_eur_rate * pence_to_pounds)) < 0.1:
        print(f"🔍 Possibilité: Prix en pence convertis incorrectement")
        print(f"   638 pence = 6.38 GBP ≈ {6.38 * gbp_to_eur_rate:.2f} EUR")
    
    # Cleanup
    await api_service.close()
    await scraping_service.close()
    
    print("\n=== FIN DU DEBUG ===")

if __name__ == "__main__":
    asyncio.run(debug_cspx_price())