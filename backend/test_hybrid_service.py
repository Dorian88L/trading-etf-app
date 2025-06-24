#!/usr/bin/env python3
"""
Test du nouveau service hybride
"""
import sys
sys.path.append('/app')
import requests
import json

print("🧪 Test du service hybride de données de marché")
print("=" * 60)

try:
    # Test de l'endpoint directement
    response = requests.get(
        "http://localhost:8000/api/v1/real-market/real-etfs",
        headers={
            "Accept": "application/json",
            "User-Agent": "TradingETFApp/1.0"
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Statut: {data.get('status', 'N/A')}")
        print(f"📊 Nombre d'ETFs: {data.get('count', 0)}")
        print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
        
        if 'data' in data and len(data['data']) > 0:
            print("\n🎯 Premiers ETFs:")
            for i, etf in enumerate(data['data'][:3]):
                print(f"\n{i+1}. {etf.get('name', 'N/A')[:50]}...")
                print(f"   ISIN: {etf.get('isin', 'N/A')}")
                print(f"   Prix: {etf.get('current_price', 'N/A')} {etf.get('currency', 'N/A')}")
                print(f"   Variation: {etf.get('change', 'N/A')} ({etf.get('change_percent', 'N/A')}%)")
                print(f"   Volume: {etf.get('volume', 'N/A'):,}")
                print(f"   Source: {etf.get('source', 'N/A')}")
                
        else:
            print("❌ Aucune donnée ETF retournée")
            
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")

print("\n" + "=" * 60)