#!/usr/bin/env python3
"""
Test du mapping ISIN -> symbole pour CSPX
"""

# Configuration CSPX extraite du code
european_etfs = {
    "CSPX.L": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF USD (Acc)", "sector": "US Equity", "exchange": "LSE"},
    "CSPX.AS": {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 UCITS ETF", "sector": "US Large Cap", "exchange": "Euronext Amsterdam"},
}

# Simulation de la logique de mapping
isin_to_best_symbol = {}
target_isin = "IE00B5BMR087"

print("=== TEST DU MAPPING ISIN -> SYMBOLE ===")
print(f"ISIN cible: {target_isin}")
print()

print("Étapes du mapping:")
for symbol, info in european_etfs.items():
    isin = info['isin']
    print(f"Traitement de {symbol} (ISIN: {isin})")
    
    if isin == target_isin:
        if isin not in isin_to_best_symbol:
            isin_to_best_symbol[isin] = symbol
            print(f"  -> Premier symbole: {symbol} assigné")
        else:
            print(f"  -> Symbole existant: {isin_to_best_symbol[isin]}")
            # Préférer les symboles avec EUR pour les prix européens
            if '.AS' in symbol or '.DE' in symbol or '.PA' in symbol:
                print(f"  -> Symbole européen trouvé: {symbol}, remplacement")
                isin_to_best_symbol[isin] = symbol
            else:
                print(f"  -> Garder le symbole existant: {isin_to_best_symbol[isin]}")

print()
print(f"Résultat final: {target_isin} -> {isin_to_best_symbol.get(target_isin)}")
print()

# Analyse du problème
best_symbol = isin_to_best_symbol.get(target_isin)
if best_symbol:
    exchange = european_etfs[best_symbol]["exchange"]
    print(f"Bourse sélectionnée: {exchange}")
    
    if "LSE" in exchange or ".L" in best_symbol:
        print("⚠️  PROBLÈME IDENTIFIÉ:")
        print("   - CSPX.L est coté en pence (GBX) sur le LSE")
        print("   - Prix retourné: ~63800 pence = 638 GBP ≈ 734 EUR")
        print("   - Prix attendu: ~553 EUR")
        print("   - Solution: Préférer CSPX.AS (coté en EUR)")
    elif "Amsterdam" in exchange or ".AS" in best_symbol:
        print("✅ SOLUTION CORRECTE:")
        print("   - CSPX.AS est coté en EUR sur Euronext Amsterdam")
        print("   - Prix retourné directement en EUR")

print()
print("=== RECOMMANDATIONS ===")
print("1. Modifier la logique de priorité pour éviter .L quand .AS existe")
print("2. Ajouter une conversion pence->EUR pour les symboles .L")
print("3. Détecter automatiquement la devise depuis Yahoo Finance")