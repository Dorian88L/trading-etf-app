#!/usr/bin/env python3

"""
Script pour créer un utilisateur de test (version simple avec psycopg2)
"""

import psycopg2
from passlib.context import CryptContext

# Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "trading_etf",
    "user": "trading_user",
    "password": "trading_password"
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Données de l'utilisateur test
TEST_USER = {
    "email": "test@trading.com",
    "password": "test123",
    "full_name": "Utilisateur Test"
}

def create_test_user():
    print("🔐 Création de l'utilisateur de test...")
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (TEST_USER["email"],)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"✅ L'utilisateur {TEST_USER['email']} existe déjà")
            return
        
        # Hasher le mot de passe
        hashed_password = pwd_context.hash(TEST_USER["password"])
        
        # Insérer le nouvel utilisateur
        cursor.execute(
            """
            INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                TEST_USER["email"],
                hashed_password,
                TEST_USER["full_name"],
                True,
                True
            )
        )
        
        conn.commit()
        print(f"✅ Utilisateur créé avec succès!")
        print(f"📧 Email: {TEST_USER['email']}")
        print(f"🔑 Mot de passe: {TEST_USER['password']}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Création d'un utilisateur de test pour l'application Trading ETF")
    print("=" * 60)
    
    try:
        success = create_test_user()
        if success:
            print("\n🎉 Vous pouvez maintenant vous connecter avec:")
            print(f"   Email: {TEST_USER['email']}")
            print(f"   Mot de passe: {TEST_USER['password']}")
            print("\n🌐 Accédez à l'application sur: http://localhost:3000")
    except KeyboardInterrupt:
        print("\n❌ Opération annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")