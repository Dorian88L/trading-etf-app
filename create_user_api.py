#!/usr/bin/env python3

"""
Script pour créer un utilisateur via l'API
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test@trading.com",
    "password": "test123",
    "full_name": "Utilisateur Test"
}

def create_test_user():
    print("🔐 Création de l'utilisateur via l'API...")
    
    try:
        # Tenter de créer l'utilisateur
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/register",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ Utilisateur créé avec succès!")
            print(f"📧 Email: {TEST_USER['email']}")
            print(f"🔑 Mot de passe: {TEST_USER['password']}")
            return True
        elif response.status_code == 400:
            print(f"ℹ️ L'utilisateur existe peut-être déjà")
            print(f"📧 Essayez de vous connecter avec: {TEST_USER['email']}")
            print(f"🔑 Mot de passe: {TEST_USER['password']}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à l'API sur {API_BASE_URL}")
        print("🔧 Vérifiez que le backend est démarré")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_login():
    print("\n🔐 Test de connexion...")
    
    try:
        # Tester la connexion
        login_data = {
            "username": TEST_USER["email"],  # FastAPI OAuth2 utilise 'username'
            "password": TEST_USER["password"]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            data=login_data,  # OAuth2 utilise form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connexion réussie!")
            print(f"🎫 Token reçu: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Échec de connexion {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur lors du test de connexion: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Configuration utilisateur pour l'application Trading ETF")
    print("=" * 60)
    
    # Créer l'utilisateur
    user_created = create_test_user()
    
    if user_created:
        # Tester la connexion
        login_success = test_login()
        
        print("\n" + "=" * 60)
        print("🎉 Informations de connexion:")
        print(f"   📧 Email: {TEST_USER['email']}")
        print(f"   🔑 Mot de passe: {TEST_USER['password']}")
        print(f"   🌐 Application: http://localhost:3000")
        print(f"   📚 API Docs: http://localhost:8000/docs")
        
        if login_success:
            print("\n✅ Tout est prêt ! Vous pouvez vous connecter.")
        else:
            print("\n⚠️ Utilisateur créé mais problème de connexion - vérifiez l'API")