#!/usr/bin/env python3
"""
Script pour tester les APIs ETF
"""

import requests
import json
import sys
import os

# URL de base de l'API (ajustez selon votre configuration)
BASE_URL = "http://localhost:8000/api/v1"

def test_real_etfs():
    """Test de l'endpoint real-etfs"""
    print("🧪 Test de l'endpoint /real-market/real-etfs")
    
    try:
        response = requests.get(f"{BASE_URL}/real-market/real-etfs")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Succès ! {data['count']} ETFs récupérés")
            
            # Afficher quelques exemples
            if data.get('data'):
                print("\n📋 Premiers ETFs:")
                for etf in data['data'][:3]:
                    print(f"  - {etf['symbol']}: {etf['name']} ({etf['sector']})")
            
            return True
        else:
            print(f"❌ Échec: Status {response.status_code}")
            print(f"Erreur: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_etf_search():
    """Test de l'endpoint de recherche"""
    print("\n🔍 Test de la recherche d'ETFs")
    
    try:
        response = requests.get(f"{BASE_URL}/real-market/search-etfs?q=technology&limit=5")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recherche réussie ! {data['count']} résultats pour 'technology'")
            
            if data.get('data'):
                print("\n📋 Résultats de recherche:")
                for etf in data['data']:
                    print(f"  - {etf['symbol']}: {etf['name']}")
            
            return True
        else:
            print(f"❌ Échec: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_etf_catalog():
    """Test du catalogue ETF"""
    print("\n📚 Test du catalogue ETF")
    
    try:
        response = requests.get(f"{BASE_URL}/etfs/catalog?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Catalogue accessible ! {data['count']} ETFs")
            return True
        else:
            print(f"❌ Échec: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test des APIs ETF\n")
    
    results = []
    results.append(test_real_etfs())
    results.append(test_etf_search())
    results.append(test_etf_catalog())
    
    print(f"\n📊 Résumé des tests:")
    print(f"✅ Réussis: {sum(results)}/{len(results)}")
    print(f"❌ Échecs: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 Tous les tests sont passés !")
        sys.exit(0)
    else:
        print("\n⚠️ Certains tests ont échoué")
        sys.exit(1)

if __name__ == "__main__":
    main()