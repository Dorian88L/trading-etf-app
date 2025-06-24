#!/usr/bin/env python3
"""
Script d'initialisation de la base de données avec utilisateur admin
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.etf import ETF
from app.models.notification import PushSubscription, UserNotificationPreferences

# Configuration
DATABASE_URL = "postgresql://trading_user:trading_password@postgres:5432/trading_etf_dev"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_database_tables():
    """Crée toutes les tables de la base de données"""
    engine = create_engine(DATABASE_URL)
    
    print("🔧 Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès")
    
    return engine

def create_admin_user(engine):
    """Crée l'utilisateur admin"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Vérifier si l'admin existe déjà
        existing_admin = db.query(User).filter(User.email == "admin@investeclaire.fr").first()
        if existing_admin:
            print("⚠️  L'utilisateur admin existe déjà")
            return existing_admin
        
        # Hasher le mot de passe
        hashed_password = pwd_context.hash("Admin123#")
        
        # Créer l'utilisateur admin
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@investeclaire.fr",
            hashed_password=hashed_password,
            full_name="Administrateur",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Créer les préférences par défaut
        preferences = UserPreferences(
            user_id=admin_user.id,
            risk_tolerance="moderate",
            preferred_sectors=["Technology", "Healthcare", "Finance"],
            preferred_regions=["Europe", "North America"],
            max_position_size=0.10,  # 10% max par position pour admin
            max_ter=0.75,
            min_aum=50000000,  # 50M€ minimum
            email_notifications=True,
            push_notifications=True,
            min_signal_confidence=50.0,
            theme="dark",
            language="fr",
            timezone="Europe/Paris"
        )
        
        db.add(preferences)
        db.commit()
        
        print(f"✅ Utilisateur admin créé:")
        print(f"   📧 Email: {admin_user.email}")
        print(f"   🔑 Mot de passe: Admin123#")
        print(f"   🆔 ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la création de l'admin: {e}")
        raise
    finally:
        db.close()

def add_sample_etfs(engine):
    """Ajoute quelques ETFs de test"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # ETFs de test
        sample_etfs = [
            {
                "isin": "IE00B4L5Y983",
                "symbol": "IWDA.AS",
                "name": "iShares Core MSCI World UCITS ETF",
                "sector": "Global Equity",
                "ter": 0.20,
                "aum": 75000000000,  # 75B
                "inception_date": "2009-09-25",
                "currency": "USD",
                "exchange": "Euronext Amsterdam"
            },
            {
                "isin": "IE00BK5BQT80",
                "symbol": "VWCE.DE",
                "name": "Vanguard FTSE All-World UCITS ETF",
                "sector": "Global Equity",
                "ter": 0.22,
                "aum": 15000000000,  # 15B
                "inception_date": "2019-07-23",
                "currency": "USD",
                "exchange": "XETRA"
            },
            {
                "isin": "IE00B5BMR087",
                "symbol": "CSPX.L",
                "name": "iShares Core S&P 500 UCITS ETF",
                "sector": "US Equity",
                "ter": 0.07,
                "aum": 65000000000,  # 65B
                "inception_date": "2010-05-19",
                "currency": "USD",
                "exchange": "London Stock Exchange"
            }
        ]
        
        for etf_data in sample_etfs:
            existing_etf = db.query(ETF).filter(ETF.isin == etf_data["isin"]).first()
            if not existing_etf:
                etf = ETF(**etf_data)
                db.add(etf)
        
        db.commit()
        print("✅ ETFs de test ajoutés")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de l'ajout des ETFs: {e}")
    finally:
        db.close()

def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation de la base de données Trading ETF")
    print("=" * 50)
    
    try:
        # Créer les tables
        engine = create_database_tables()
        
        # Créer l'utilisateur admin
        admin_user = create_admin_user(engine)
        
        # Ajouter des ETFs de test
        add_sample_etfs(engine)
        
        print("\n" + "=" * 50)
        print("🎉 Initialisation terminée avec succès!")
        print("\n📝 Informations de connexion:")
        print("   URL: http://localhost")
        print("   Email: admin@investeclaire.fr")
        print("   Mot de passe: Admin123#")
        print("\n📚 Documentation API:")
        print("   Swagger: http://localhost/docs")
        print("   ReDoc: http://localhost/redoc")
        
    except Exception as e:
        print(f"\n❌ Erreur d'initialisation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()