#!/usr/bin/env python3

"""
Script pour créer un utilisateur de test
"""

import os
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Configuration
DATABASE_URL = "postgresql+asyncpg://trading_user:trading_password@localhost:5433/trading_etf"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Données de l'utilisateur test
TEST_USER = {
    "email": "test@trading.com",
    "password": "test123",
    "full_name": "Utilisateur Test"
}

async def create_test_user():
    print("🔐 Création de l'utilisateur de test...")
    
    # Créer l'engine async
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Créer la session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Vérifier si l'utilisateur existe déjà
            result = await session.execute(
                "SELECT id FROM users WHERE email = :email",
                {"email": TEST_USER["email"]}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"✅ L'utilisateur {TEST_USER['email']} existe déjà")
                return
            
            # Hasher le mot de passe
            hashed_password = pwd_context.hash(TEST_USER["password"])
            
            # Insérer le nouvel utilisateur
            await session.execute(
                """
                INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
                VALUES (:email, :hashed_password, :full_name, true, true)
                """,
                {
                    "email": TEST_USER["email"],
                    "hashed_password": hashed_password,
                    "full_name": TEST_USER["full_name"]
                }
            )
            
            await session.commit()
            print(f"✅ Utilisateur créé avec succès!")
            print(f"📧 Email: {TEST_USER['email']}")
            print(f"🔑 Mot de passe: {TEST_USER['password']}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🚀 Création d'un utilisateur de test pour l'application Trading ETF")
    print("=" * 60)
    
    try:
        asyncio.run(create_test_user())
        print("\n🎉 Vous pouvez maintenant vous connecter avec:")
        print(f"   Email: {TEST_USER['email']}")
        print(f"   Mot de passe: {TEST_USER['password']}")
        print("\n🌐 Accédez à l'application sur: http://localhost:3000")
    except KeyboardInterrupt:
        print("\n❌ Opération annulée")
        sys.exit(1)