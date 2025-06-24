#!/usr/bin/env python3
"""
Script pour tester la récupération de données réelles ETF
"""

import asyncio
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.multi_source_etf_data import MultiSourceETFDataService
from app.services.etf_catalog import get_etf_catalog_service

async def test_real_data():
    """Test de récupération de données réelles"""
    print("🧪 Test de récupération de données ETF réelles\n")
    
    # Initialiser les services
    catalog_service = get_etf_catalog_service()
    data_service = MultiSourceETFDataService()
    
    # Récupérer quelques ETFs du catalogue
    all_etfs = catalog_service.get_all_etfs()
    test_etfs = all_etfs[:5]  # Tester les 5 premiers
    
    print(f"📋 Test de {len(test_etfs)} ETFs du catalogue:")
    for etf in test_etfs:
        print(f"  - {etf.symbol}: {etf.name}")
    
    print("\n🔄 Récupération des données réelles...")
    
    successful = 0
    failed = 0
    
    for etf in test_etfs:
        try:
            print(f"\n🔍 Test de {etf.symbol}...")
            real_data = await data_service.get_etf_data(etf.symbol)
            
            if real_data:
                print(f"✅ Succès ! Prix: {real_data.current_price} {real_data.currency}")
                print(f"   Variation: {real_data.change_percent:.2f}%")
                print(f"   Source: {real_data.source.value}")
                print(f"   Confiance: {real_data.confidence_score:.2f}")
                successful += 1
            else:
                print(f"❌ Aucune donnée trouvée")
                failed += 1
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            failed += 1
    
    print(f"\n📊 Résumé:")
    print(f"✅ Succès: {successful}/{len(test_etfs)}")
    print(f"❌ Échecs: {failed}/{len(test_etfs)}")
    
    if successful > 0:
        print("\n🎉 Au moins certaines données réelles ont été récupérées !")
        return True
    else:
        print("\n⚠️ Aucune donnée réelle récupérée. Vérifiez les clés API ou la connectivité.")
        return False

async def main():
    """Fonction principale"""
    success = await test_real_data()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())