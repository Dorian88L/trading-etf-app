#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion frontend/backend en local
"""

import requests
import json
import time

def test_backend_health():
    """Test du health check backend"""
    try:
        response = requests.get("http://localhost:8443/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check OK")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend non accessible: {e}")
        return False

def test_backend_root():
    """Test de l'endpoint root"""
    try:
        response = requests.get("http://localhost:8443/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend root OK - Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Backend root failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend root error: {e}")
        return False

def test_frontend():
    """Test du frontend"""
    try:
        response = requests.get("http://localhost:80", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend non accessible: {e}")
        return False

def test_register_endpoint():
    """Test de l'endpoint register"""
    try:
        test_user = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = requests.post(
            "http://localhost:8443/api/v1/auth/register", 
            json=test_user,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Endpoint register accessible")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Endpoint register accessible (utilisateur existe déjà)")
            return True
        else:
            print(f"❌ Register endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Register endpoint error: {e}")
        return False

def main():
    print("🧪 Test de connexion frontend/backend local")
    print("=" * 50)
    
    # Test backend
    print("\n📡 Test Backend:")
    backend_health = test_backend_health()
    backend_root = test_backend_root()
    register_ok = test_register_endpoint()
    
    # Test frontend  
    print("\n🌐 Test Frontend:")
    frontend_ok = test_frontend()
    
    # Résumé
    print("\n📊 Résumé:")
    print("=" * 30)
    
    if backend_health and backend_root and register_ok:
        print("✅ Backend: FONCTIONNEL")
    else:
        print("❌ Backend: PROBLÈMES DÉTECTÉS")
        
    if frontend_ok:
        print("✅ Frontend: ACCESSIBLE")
    else:
        print("❌ Frontend: NON ACCESSIBLE")
        
    if backend_health and backend_root and register_ok and frontend_ok:
        print("\n🎉 SUCCÈS: L'application fonctionne en local!")
        print("📱 Frontend: http://localhost:80")
        print("🔧 Backend API: http://localhost:8443")
        print("📚 Documentation: http://localhost:8443/docs")
    else:
        print("\n⚠️  PROBLÈMES DÉTECTÉS - Vérifiez les logs")

if __name__ == "__main__":
    main()