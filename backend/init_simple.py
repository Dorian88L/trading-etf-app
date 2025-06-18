#!/usr/bin/env python3
"""
Script d'initialisation simple de la base de données
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer tous les modèles pour éviter les erreurs de relations
from app.core.database import Base
from app.models import *  # Import de tous les modèles

# Configuration
DATABASE_URL = "postgresql://trading_user:trading_password@postgres:5432/trading_etf_dev"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation simple de la base de données")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Créer toutes les tables
        print("🔧 Création des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées")
        
        # Créer une session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Vérifier si l'admin existe
        from app.models.user import User
        existing_admin = db.query(User).filter(User.email == "admin@investeclaire.fr").first()
        
        if not existing_admin:
            # Créer l'admin via SQL direct
            hashed_password = pwd_context.hash("Admin123#")
            admin_id = str(uuid.uuid4())
            
            db.execute(text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified, created_at, updated_at)
                VALUES (:id, :email, :password, :name, :active, :verified, :created, :updated)
            """), {
                'id': admin_id,
                'email': 'admin@investeclaire.fr',
                'password': hashed_password,
                'name': 'Administrateur',
                'active': True,
                'verified': True,
                'created': datetime.utcnow(),
                'updated': datetime.utcnow()
            })
            
            db.commit()
            print("✅ Utilisateur admin créé:")
            print("   📧 Email: admin@investeclaire.fr")
            print("   🔑 Mot de passe: Admin123#")
        else:
            print("⚠️  L'utilisateur admin existe déjà")
        
        db.close()
        print("🎉 Initialisation terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()