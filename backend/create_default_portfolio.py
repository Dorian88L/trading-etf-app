#!/usr/bin/env python3
"""
Créer un portfolio par défaut pour l'utilisateur admin
"""
import sys
sys.path.append('/app')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from datetime import datetime

def create_default_portfolio():
    """Créer un portfolio par défaut"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("📝 Création du portfolio par défaut...")
        
        # Récupérer l'utilisateur admin
        result = session.execute(text("""
            SELECT id FROM users WHERE email = 'admin@investeclaire.fr' LIMIT 1
        """))
        
        user_row = result.fetchone()
        if not user_row:
            print("❌ Utilisateur admin non trouvé")
            return False
            
        user_id = user_row[0]
        print(f"👤 Utilisateur admin trouvé: {user_id}")
        
        # Vérifier si le portfolio existe déjà
        existing = session.execute(text("""
            SELECT COUNT(*) FROM portfolios WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()[0]
        
        if existing == 0:
            # Créer un portfolio par défaut
            session.execute(text("""
                INSERT INTO portfolios (id, user_id, name, created_at, updated_at)
                VALUES (gen_random_uuid(), :user_id, 'Portfolio Principal', NOW(), NOW())
            """), {"user_id": user_id})
            print("✅ Portfolio créé")
        else:
            print("ℹ️ Portfolio déjà existant")
        
        # Vérifier la table portfolios existe
        session.execute(text("SELECT COUNT(*) FROM portfolios"))
        
        session.commit()
        print("✅ Portfolio par défaut créé avec succès")
        
        # Vérifier les portfolios
        result = session.execute(text("""
            SELECT p.name, u.email 
            FROM portfolios p 
            JOIN users u ON p.user_id = u.id
        """))
        
        portfolios = result.fetchall()
        print(f"\n📊 Portfolios existants: {len(portfolios)}")
        for portfolio in portfolios:
            print(f"  - {portfolio[0]} (Utilisateur: {portfolio[1]})")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du portfolio: {e}")
        return False

if __name__ == "__main__":
    success = create_default_portfolio()
    if success:
        print("🎉 Portfolio par défaut créé avec succès")
    else:
        print("💥 Échec de la création du portfolio")
        sys.exit(1)