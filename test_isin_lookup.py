#!/usr/bin/env python3
"""
Test de la logique de récupération d'ISIN dans get_etf_data
"""

# Configuration CSPX extraite du code
european_etfs = {
    "CSPX.L": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF USD (Acc)", "sector": "US Equity", "exchange": "LSE"},
    "CSPX.AS": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Large Cap", "exchange": "Euronext Amsterdam"},
}

isin_to_best_symbol = {
    "IE00B5BMR087": "CSPX.AS"  # Résultat de la logique précédente
}

def test_isin_lookup(symbol):
    """Test de la récupération d'ISIN selon la logique du code"""
    
    print(f"=== TEST RÉCUPÉRATION ISIN POUR {symbol} ===")
    
    # Logique actuelle du code (lignes 534-545)
    isin = None
    
    # Étape 1: Chercher dans european_etfs par nom ou symbole exact
    print("Étape 1: Recherche dans european_etfs")
    for etf_symbol, etf_data in european_etfs.items():
        print(f"  Vérification de {etf_symbol}")
        print(f"    - symbol in name: {symbol in etf_data.get('name', '')}")
        print(f"    - symbol == etf_symbol: {symbol == etf_symbol}")
        
        if symbol in etf_data.get('name', '') or symbol == etf_symbol:
            isin = etf_data.get('isin', etf_symbol)
            print(f"    -> TROUVÉ: ISIN = {isin}")
            break
    
    if not isin:
        print("  Aucun ISIN trouvé par nom/symbole exact")
        
        # Étape 2: Chercher dans le mapping inverse
        print("Étape 2: Recherche dans isin_to_best_symbol")
        for mapped_isin, mapped_symbol in isin_to_best_symbol.items():
            print(f"  Vérification {mapped_isin} -> {mapped_symbol}")
            if mapped_symbol == symbol:
                isin = mapped_isin
                print(f"    -> TROUVÉ: ISIN = {isin}")
                break
        
        if not isin:
            print("  Aucun ISIN trouvé dans le mapping inverse")
    
    print(f"\nRésultat final: ISIN = {isin}")
    
    # Analyse du problème
    if isin:
        best_symbol = isin_to_best_symbol.get(isin)
        print(f"Meilleur symbole pour {isin}: {best_symbol}")
        
        if symbol != best_symbol:
            print(f"⚠️  PROBLÈME: Recherche pour {symbol} mais meilleur symbole est {best_symbol}")
            print("   Le scraping va utiliser le bon ISIN mais le retour sera associé au mauvais symbole")

# Tests
test_isin_lookup("CSPX.L")
print()
test_isin_lookup("CSPX.AS")