#!/usr/bin/env python3
"""
Script pour initialiser complètement la base de données
Crée les tables et l'utilisateur test
"""
import asyncio
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Import de nos modèles
from app.core.config import settings
from app.models.user import User, Base
from app.models.etf import ETF
from app.models.signal import Signal
from app.models.portfolio import Portfolio
from app.models.alert import Alert
from app.models.watchlist import Watchlist
from app.models.notification import PushSubscription
from app.models.user_preferences import UserPreferences

# Configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5434/trading_etf"

def init_database():
    """Initialise la base de données avec les tables et données"""
    print("🗄️ Initialisation de la base de données...")
    
    # Créer l'engine
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Créer toutes les tables
    print("📋 Création des tables...")
    Base.metadata.create_all(bind=engine)
    
    # Créer une session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Créer l'utilisateur test
        print("👤 Création de l'utilisateur test...")
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.email == "test@trading.com").first()
        if existing_user:
            print("✅ Utilisateur test@trading.com existe déjà")
            return existing_user
        
        # Hasher le mot de passe
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("test123")
        
        # Créer l'utilisateur
        test_user = User(
            id=uuid.uuid4(),
            email="test@trading.com",
            hashed_password=hashed_password,
            full_name="Test User Trading",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Utilisateur créé: {test_user.email} (ID: {test_user.id})")
        
        # Créer les préférences utilisateur
        user_prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=test_user.id,
            notification_email=True,
            notification_push=True,
            notification_signals=True,
            default_currency="EUR",
            risk_tolerance="medium",
            investment_horizon="short_term",
            preferred_sectors=["technology", "healthcare", "finance"],
            watchlist_etfs=["IWDA.AS", "VWCE.DE", "CSPX.L"],
            signal_subscriptions=["BUY", "SELL"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user_prefs)
        db.commit()
        
        print("✅ Préférences utilisateur créées")
        
        # Créer quelques ETFs de test
        print("📊 Création d'ETFs de test...")
        
        etfs_test = [
            {
                "isin": "IE00B4L5Y983", 
                "symbol": "IWDA.AS",
                "name": "iShares Core MSCI World UCITS ETF",
                "currency": "USD",
                "exchange": "Euronext Amsterdam"
            },
            {
                "isin": "IE00BK5BQT80",
                "symbol": "VWCE.DE", 
                "name": "Vanguard FTSE All-World UCITS ETF",
                "currency": "USD",
                "exchange": "XETRA"
            },
            {
                "isin": "IE00B5BMR087",
                "symbol": "CSPX.L",
                "name": "iShares Core S&P 500 UCITS ETF",
                "currency": "USD", 
                "exchange": "London Stock Exchange"
            }
        ]
        
        for etf_data in etfs_test:
            existing_etf = db.query(ETF).filter(ETF.isin == etf_data["isin"]).first()
            if not existing_etf:
                etf = ETF(
                    id=uuid.uuid4(),
                    isin=etf_data["isin"],
                    symbol=etf_data["symbol"],
                    name=etf_data["name"],
                    currency=etf_data["currency"],
                    exchange=etf_data["exchange"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(etf)
        
        db.commit()
        print("✅ ETFs de test créés")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        user = init_database()
        print("\n🎉 Base de données initialisée avec succès!")
        print(f"👤 Utilisateur: test@trading.com")
        print(f"🔑 Mot de passe: test123")
        print(f"🆔 User ID: {user.id}")
        print("\n🚀 Vous pouvez maintenant vous connecter à l'application!")
        
    except Exception as e:
        print(f"\n❌ Échec de l'initialisation: {e}")
        sys.exit(1)