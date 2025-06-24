#!/usr/bin/env python3
"""
Analyse statique du problème de prix CSPX.L
"""

import re
import os

def analyze_multi_source_service():
    """Analyse le service multi-source pour comprendre le problème"""
    
    print("=== ANALYSE DU PROBLÈME CSPX PRICE ===")
    print()
    
    service_file = '/home/dorian/trading-etf-app/backend/app/services/multi_source_etf_data.py'
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    print("1. Configuration CSPX dans european_etfs:")
    print("-" * 50)
    
    # Rechercher la configuration CSPX
    cspx_pattern = r'"CSPX\.[^"]*":\s*{[^}]+}'
    cspx_matches = re.findall(cspx_pattern, content, re.DOTALL)
    
    for match in cspx_matches:
        print(match)
        print()
    
    print("2. Méthode _get_yahoo_finance_data:")
    print("-" * 40)
    
    # Extraire la méthode Yahoo Finance
    yahoo_method_pattern = r'async def _get_yahoo_finance_data\(self, symbol: str\)[^:]*:(.*?)(?=async def|\Z)'
    yahoo_match = re.search(yahoo_method_pattern, content, re.DOTALL)
    
    if yahoo_match:
        method_content = yahoo_match.group(1)
        
        # Chercher les conversions de prix
        price_lines = []
        for line in method_content.split('\n'):
            if 'price' in line.lower() and ('=' in line or 'float' in line):
                price_lines.append(line.strip())
        
        print("Lignes relatives au prix:")
        for line in price_lines:
            print(f"  {line}")
        print()
        
        # Chercher les conversions de devise
        currency_lines = []
        for line in method_content.split('\n'):
            if 'currency' in line.lower():
                currency_lines.append(line.strip())
        
        print("Lignes relatives à la devise:")
        for line in currency_lines:
            print(f"  {line}")
        print()
    
    print("3. Analyse du problème potentiel:")
    print("-" * 40)
    
    print("CSPX.L (London Stock Exchange) est coté en:")
    print("- Pence (GBX) sur le LSE")
    print("- Problème: 638€ au lieu de ~553€")
    print()
    
    # Calculs
    incorrect_price = 638.0
    expected_price = 553.0
    ratio = incorrect_price / expected_price
    
    print(f"Ratio: {ratio:.4f}")
    print()
    
    # Vérifier si c'est un problème de pence
    gbp_eur_rate = 1.15  # Approximation
    if abs(ratio - gbp_eur_rate) < 0.1:
        print("🔍 DIAGNOSTIC: Probable conversion pence->euros sans passage par livres")
        print("   Exemple: 553 pence = 5.53 GBP = 6.36 EUR (attendu)")
        print("   Mais si: 553 pence × 1.15 = 636 EUR (incorrect)")
    else:
        print("🔍 DIAGNOSTIC: Autre problème de conversion")
    
    print()
    print("4. Solutions proposées:")
    print("-" * 30)
    print("A. Vérifier si Yahoo Finance retourne les prix en pence pour .L")
    print("B. Ajouter une conversion pence->livres pour les symboles .L")
    print("C. Utiliser les symboles .AS (Amsterdam) qui sont en euros")
    print("D. Implémenter une détection automatique de la devise")

if __name__ == "__main__":
    analyze_multi_source_service()