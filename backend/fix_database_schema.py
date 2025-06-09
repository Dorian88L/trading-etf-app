#!/usr/bin/env python3
"""
Script pour mettre à jour le schéma de base de données
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ajouter le chemin du backend pour les imports
sys.path.append(os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.user_preferences import UserPreferences, UserWatchlist, UserAlert, UserSignalSubscription
from app.models.notification import PushSubscription, NotificationHistory, UserNotificationPreferences

def update_database_schema():
    """Met à jour le schéma de base de données"""
    
    print("🔧 Mise à jour du schéma de base de données...")
    
    # Créer la connexion
    engine = create_engine(settings.DATABASE_URL)
    
    # Créer toutes les tables
    print("📊 Création/mise à jour des tables...")
    Base.metadata.create_all(bind=engine)
    
    # Ajouter les colonnes manquantes à user_preferences si nécessaire
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier et ajouter les colonnes manquantes
        columns_to_add = [
            ("preferred_sectors", "JSONB"),
            ("preferred_regions", "JSONB"),
            ("dashboard_layout", "JSONB"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                session.execute(text(f"""
                    ALTER TABLE user_preferences 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """))
                print(f"✅ Colonne {column_name} ajoutée/vérifiée")
            except Exception as e:
                print(f"⚠️  Colonne {column_name}: {e}")
        
        # Créer les tables de notifications si elles n'existent pas
        notification_tables = [
            """
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id),
                endpoint TEXT NOT NULL UNIQUE,
                p256dh_key TEXT NOT NULL,
                auth_key TEXT NOT NULL,
                user_agent VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_used_at TIMESTAMP WITH TIME ZONE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notification_history (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id),
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                is_clicked BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                clicked_at TIMESTAMP WITH TIME ZONE,
                etf_isin VARCHAR(12),
                signal_id INTEGER,
                metadata JSONB
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id) UNIQUE,
                signal_notifications BOOLEAN DEFAULT TRUE,
                price_alert_notifications BOOLEAN DEFAULT TRUE,
                market_alert_notifications BOOLEAN DEFAULT TRUE,
                portfolio_notifications BOOLEAN DEFAULT TRUE,
                system_notifications BOOLEAN DEFAULT TRUE,
                min_signal_confidence FLOAT DEFAULT 60.0,
                min_price_change_percent FLOAT DEFAULT 5.0,
                min_volume_spike_percent FLOAT DEFAULT 50.0,
                quiet_hours_start VARCHAR(5) DEFAULT '22:00',
                quiet_hours_end VARCHAR(5) DEFAULT '08:00',
                weekend_notifications BOOLEAN DEFAULT FALSE,
                max_notifications_per_hour INTEGER DEFAULT 10,
                max_notifications_per_day INTEGER DEFAULT 50,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        ]
        
        for table_sql in notification_tables:
            try:
                session.execute(text(table_sql))
                print("✅ Table de notifications créée/vérifiée")
            except Exception as e:
                print(f"⚠️  Erreur table notifications: {e}")
        
        session.commit()
        print("✅ Schéma de base de données mis à jour avec succès!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False
    finally:
        session.close()
    
    return True

def create_default_preferences():
    """Crée les préférences par défaut pour les utilisateurs existants"""
    
    print("👤 Création des préférences par défaut...")
    
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Récupérer tous les utilisateurs sans préférences
        users_without_prefs = session.execute(text("""
            SELECT u.id FROM users u 
            LEFT JOIN user_preferences up ON u.id = up.user_id 
            WHERE up.user_id IS NULL
        """)).fetchall()
        
        for user_row in users_without_prefs:
            user_id = user_row[0]
            
            # Créer les préférences par défaut
            session.execute(text("""
                INSERT INTO user_preferences (
                    user_id, risk_tolerance, max_position_size, max_ter, 
                    min_aum, email_notifications, push_notifications, 
                    sms_notifications, min_signal_confidence, theme, 
                    language, timezone
                ) VALUES (
                    :user_id, 'moderate', 0.05, 0.50, 
                    100000000, true, true, 
                    false, 60.0, 'light', 
                    'fr', 'Europe/Paris'
                )
            """), {"user_id": user_id})
            
            print(f"✅ Préférences créées pour l'utilisateur {user_id}")
        
        session.commit()
        print("✅ Préférences par défaut créées!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur création préférences: {e}")
        return False
    finally:
        session.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Script de mise à jour de la base de données")
    print("=" * 50)
    
    success = update_database_schema()
    if success:
        create_default_preferences()
        print("\n🎉 Mise à jour terminée avec succès!")
    else:
        print("\n❌ Échec de la mise à jour")
        sys.exit(1)