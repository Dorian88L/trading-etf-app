#!/usr/bin/env python3
"""
Script de correction rapide pour les erreurs de production
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_issues():
    """Corrige les problèmes de base de données."""
    db = SessionLocal()
    
    try:
        logger.info("🔧 Correction des problèmes de base de données...")
        
        # 1. Nettoyer les données en double dans market_data
        logger.info("🧹 Nettoyage des doublons dans market_data...")
        
        # Supprimer les doublons en gardant le plus récent
        cleanup_sql = """
        DELETE FROM market_data 
        WHERE ctid NOT IN (
            SELECT MAX(ctid) 
            FROM market_data 
            GROUP BY time, etf_isin
        );
        """
        
        result = db.execute(text(cleanup_sql))
        deleted_rows = result.rowcount
        logger.info(f"✅ {deleted_rows} doublons supprimés")
        
        # 2. Mettre à jour les données NULL qui causent les erreurs de calcul
        logger.info("🔧 Correction des valeurs NULL...")
        
        # Corriger les change_absolute et change_percent NULL
        update_sql = """
        UPDATE market_data 
        SET 
            change_absolute = 0.0, 
            change_percent = 0.0 
        WHERE change_absolute IS NULL OR change_percent IS NULL;
        """
        
        db.execute(text(update_sql))
        logger.info("✅ Valeurs NULL corrigées")
        
        # 3. Nettoyer les market_data trop anciens (garde 7 jours)
        cleanup_old_sql = """
        DELETE FROM market_data 
        WHERE time < NOW() - INTERVAL '7 days';
        """
        
        result = db.execute(text(cleanup_old_sql))
        deleted_old = result.rowcount
        logger.info(f"✅ {deleted_old} anciennes données supprimées")
        
        # 4. Reindexer pour optimiser les performances
        logger.info("📊 Réindexation...")
        
        db.execute(text("REINDEX INDEX market_data_pkey;"))
        db.execute(text("ANALYZE market_data;"))
        
        db.commit()
        logger.info("✅ Base de données nettoyée et optimisée")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction de la base: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def check_database_health():
    """Vérifie la santé de la base de données."""
    db = SessionLocal()
    
    try:
        logger.info("🔍 Vérification de la santé de la base...")
        
        # Vérifier les doublons
        duplicate_check = """
        SELECT COUNT(*) as duplicates
        FROM (
            SELECT time, etf_isin, COUNT(*) 
            FROM market_data 
            GROUP BY time, etf_isin 
            HAVING COUNT(*) > 1
        ) as dups;
        """
        
        result = db.execute(text(duplicate_check)).fetchone()
        duplicates = result[0]
        
        if duplicates > 0:
            logger.warning(f"⚠️ {duplicates} doublons détectés")
        else:
            logger.info("✅ Aucun doublon trouvé")
        
        # Vérifier les valeurs NULL problématiques
        null_check = """
        SELECT COUNT(*) as nulls
        FROM market_data 
        WHERE change_absolute IS NULL OR change_percent IS NULL;
        """
        
        result = db.execute(text(null_check)).fetchone()
        nulls = result[0]
        
        if nulls > 0:
            logger.warning(f"⚠️ {nulls} valeurs NULL trouvées")
        else:
            logger.info("✅ Aucune valeur NULL problématique")
        
        # Statistiques générales
        stats_sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT etf_isin) as unique_etfs,
            MAX(time) as latest_data
        FROM market_data;
        """
        
        result = db.execute(text(stats_sql)).fetchone()
        total, unique_etfs, latest = result
        
        logger.info(f"📊 Statistiques: {total} enregistrements, {unique_etfs} ETFs uniques")
        logger.info(f"📅 Dernières données: {latest}")
        
        return duplicates == 0 and nulls == 0
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False
        
    finally:
        db.close()

def main():
    """Point d'entrée principal."""
    logger.info("🚀 Démarrage des corrections de production...")
    
    # Vérifier l'état initial
    logger.info("🔍 Vérification de l'état initial...")
    initial_health = check_database_health()
    
    if not initial_health:
        logger.info("🔧 Correction des problèmes détectés...")
        if fix_database_issues():
            logger.info("✅ Corrections appliquées avec succès")
        else:
            logger.error("❌ Échec des corrections")
            return 1
    
    # Vérifier l'état final
    logger.info("🔍 Vérification finale...")
    final_health = check_database_health()
    
    if final_health:
        logger.info("🎉 Base de données en bon état!")
        logger.info("")
        logger.info("📋 Actions recommandées:")
        logger.info("1. Redémarrer le backend pour appliquer les correctifs du code")
        logger.info("2. Surveiller les logs pour vérifier l'absence d'erreurs")
        logger.info("3. Tester les endpoints qui échouaient")
        logger.info("")
        logger.info("🔄 Pour redémarrer le backend:")
        logger.info("   docker restart backend-prod")
        return 0
    else:
        logger.error("❌ Problèmes persistants détectés")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)