#!/usr/bin/env python3
"""
Script pour tester et afficher les détails des ETFs par ISIN
"""

import sys
import os
import asyncio
from typing import Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.etf_catalog import get_etf_catalog_service, ETFInfo

def format_currency(amount: float) -> str:
    """Formate un montant en milliards ou millions"""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f}B €"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M €"
    else:
        return f"{amount:,.0f} €"

def display_etf_details(etf: ETFInfo):
    """Affiche les détails d'un ETF de manière formatée"""
    print("=" * 80)
    print(f"📊 {etf.name}")
    print("=" * 80)
    print(f"ISIN:           {etf.isin}")
    print(f"Symbole:        {etf.symbol}")
    print(f"Secteur:        {etf.sector}")
    print(f"Région:         {etf.region}")
    print(f"Devise:         {etf.currency}")
    print(f"TER:            {etf.ter}%")
    print(f"AUM:            {format_currency(etf.aum)}")
    print(f"Bourse:         {etf.exchange}")
    print(f"Benchmark:      {etf.benchmark}")
    print(f"Date création:  {etf.inception_date}")
    print(f"Dividendes:     {etf.dividend_frequency}")
    print(f"Réplication:    {etf.replication_method}")
    print(f"Description:    {etf.description}")
    print()

def main():
    """Fonction principale"""
    print("🔍 Test des détails ETFs par ISIN")
    print()
    
    # ISINs à tester (ceux mentionnés par l'utilisateur)
    test_isins = [
        "IE0032077012",  # Invesco NASDAQ-100
        "IE00BK5BQT80",  # Vanguard All-World
        "IE00BK5BQV03"   # Vanguard Europe
    ]
    
    catalog_service = get_etf_catalog_service()
    
    for isin in test_isins:
        print(f"🔎 Recherche ISIN: {isin}")
        etf_info = catalog_service.get_etf_by_isin(isin)
        
        if etf_info:
            display_etf_details(etf_info)
        else:
            print(f"❌ ETF avec ISIN {isin} non trouvé dans le catalogue")
            print()
    
    # Afficher quelques statistiques du catalogue
    print("📈 Statistiques du catalogue:")
    all_etfs = catalog_service.get_all_etfs()
    print(f"Total ETFs: {len(all_etfs)}")
    
    sectors = set(etf.sector for etf in all_etfs)
    print(f"Secteurs disponibles: {', '.join(sorted(sectors))}")
    
    regions = set(etf.region for etf in all_etfs)
    print(f"Régions disponibles: {', '.join(sorted(regions))}")

if __name__ == "__main__":
    main()