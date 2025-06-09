#!/usr/bin/env python3
"""
Script pour réinitialiser complètement la base de données
"""

import os
import sys
from sqlalchemy import create_engine, text

# Ajouter le chemin du backend pour les imports
sys.path.append(os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import Base

def reset_database():
    """Réinitialise complètement la base de données"""
    
    print("🗑️  Réinitialisation complète de la base de données...")
    
    # Créer la connexion
    engine = create_engine(settings.DATABASE_URL)
    
    # Supprimer toutes les tables
    print("❌ Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Recréer toutes les tables
    print("📊 Création de toutes les tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Base de données réinitialisée avec succès!")
    return True

if __name__ == "__main__":
    print("🚀 Script de réinitialisation de la base de données")
    print("=" * 50)
    
    success = reset_database()
    if success:
        print("\n🎉 Réinitialisation terminée avec succès!")
        print("💡 Redémarrez l'application et ajoutez des données d'exemple.")
    else:
        print("\n❌ Échec de la réinitialisation")
        sys.exit(1)