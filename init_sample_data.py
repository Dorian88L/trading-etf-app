#!/usr/bin/env python3

"""
Script pour initialiser des données d'exemple
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Récupère un token d'authentification"""
    login_data = {
        "username": "test@trading.com",
        "password": "test123"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erreur de connexion: {response.text}")
        return None

def test_endpoints():
    """Teste les différents endpoints"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🧪 Test des endpoints API...")
    
    # Test des ETFs
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/market/etfs", headers=headers)
        print(f"📊 ETFs endpoint: {response.status_code}")
        if response.status_code == 200:
            etfs = response.json()
            print(f"   Found {len(etfs)} ETFs")
    except Exception as e:
        print(f"❌ Erreur ETFs: {e}")
    
    # Test des signaux
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/signals/advanced?limit=5", headers=headers)
        print(f"📈 Signaux endpoint: {response.status_code}")
        if response.status_code == 200:
            signals = response.json()
            print(f"   Found {len(signals)} signals")
            if signals:
                print(f"   Premier signal: {signals[0].get('etf_name', 'N/A')} - {signals[0].get('signal_type', 'N/A')}")
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur Signaux: {e}")
    
    # Test des données de marché
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/market-data/FR0010296061?days=5", headers=headers)
        print(f"📉 Market Data endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} data points")
    except Exception as e:
        print(f"❌ Erreur Market Data: {e}")
    
    # Test des indicateurs techniques
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/technical-indicators/FR0010296061?days=30", headers=headers)
        print(f"📊 Technical Indicators endpoint: {response.status_code}")
        if response.status_code == 200:
            indicators = response.json()
            print(f"   Found {len(indicators)} indicator points")
    except Exception as e:
        print(f"❌ Erreur Technical Indicators: {e}")
    
    return True

def check_application_health():
    """Vérifie la santé de l'application"""
    print("🏥 Vérification de la santé de l'application...")
    
    # Test du backend
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Backend API: OK")
        else:
            print(f"❌ Backend API: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend API: {e}")
    
    # Test du frontend
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("✅ Frontend React: OK")
        else:
            print(f"❌ Frontend React: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend React: {e}")

if __name__ == "__main__":
    print("🚀 Vérification de l'application Trading ETF")
    print("=" * 60)
    
    check_application_health()
    print()
    test_endpoints()
    
    print("\n" + "=" * 60)
    print("💡 Instructions de connexion:")
    print("   📧 Email: test@trading.com")
    print("   🔑 Mot de passe: test123")
    print("   🌐 Application: http://localhost:3000")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("\n🎯 L'application devrait maintenant fonctionner correctement !")