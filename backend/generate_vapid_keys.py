#!/usr/bin/env python3
"""
Script pour générer les clés VAPID nécessaires aux notifications push
"""

import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_vapid_keys():
    """Génère une paire de clés VAPID (publique/privée)"""
    
    # Générer une clé privée ECDSA
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # Extraire la clé publique
    public_key = private_key.public_key()
    
    # Sérialiser la clé privée en format PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Sérialiser la clé publique en format PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Convertir en base64 pour utilisation dans les variables d'environnement
    private_key_b64 = base64.b64encode(private_pem).decode('utf-8')
    public_key_b64 = base64.b64encode(public_pem).decode('utf-8')
    
    return private_key_b64, public_key_b64

def update_env_file(private_key, public_key):
    """Met à jour le fichier .env avec les clés VAPID"""
    
    env_path = '.env'
    
    # Lire le fichier .env existant
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Supprimer les anciennes clés VAPID s'elles existent
    env_lines = [line for line in env_lines if not line.startswith('VAPID_')]
    
    # Ajouter les nouvelles clés
    env_lines.append(f'\n# Push Notifications VAPID Keys\n')
    env_lines.append(f'VAPID_PRIVATE_KEY={private_key}\n')
    env_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')
    env_lines.append(f'VAPID_EMAIL=admin@trading-etf.com\n')
    
    # Écrire le fichier .env mis à jour
    with open(env_path, 'w') as f:
        f.writelines(env_lines)
    
    print(f"✅ Fichier .env mis à jour avec les clés VAPID")

def update_frontend_config(public_key):
    """Met à jour la configuration frontend avec la clé publique"""
    
    frontend_env_path = '../frontend/.env'
    
    # Créer le fichier .env frontend s'il n'existe pas
    env_lines = []
    if os.path.exists(frontend_env_path):
        with open(frontend_env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Supprimer l'ancienne clé publique VAPID si elle existe
    env_lines = [line for line in env_lines if not line.startswith('REACT_APP_VAPID_PUBLIC_KEY')]
    
    # Ajouter la nouvelle clé publique
    env_lines.append(f'\n# Push Notifications\n')
    env_lines.append(f'REACT_APP_VAPID_PUBLIC_KEY={public_key}\n')
    
    # Écrire le fichier .env frontend
    os.makedirs('../frontend', exist_ok=True)
    with open(frontend_env_path, 'w') as f:
        f.writelines(env_lines)
    
    print(f"✅ Fichier frontend/.env mis à jour avec la clé publique VAPID")

def main():
    """Fonction principale"""
    print("🔑 Génération des clés VAPID pour les notifications push...")
    
    try:
        # Générer les clés
        private_key, public_key = generate_vapid_keys()
        
        print("✅ Clés VAPID générées avec succès")
        
        # Mettre à jour les fichiers de configuration
        update_env_file(private_key, public_key)
        update_frontend_config(public_key)
        
        print("\n📋 Configuration terminée:")
        print(f"   • Clé privée VAPID ajoutée au backend (.env)")
        print(f"   • Clé publique VAPID ajoutée au frontend (frontend/.env)")
        print(f"   • Email VAPID configuré: admin@trading-etf.com")
        
        print("\n🚀 Les notifications push sont maintenant configurées!")
        print("   Redémarrez l'application pour appliquer les changements.")
        
        # Afficher les clés pour debug (attention en production)
        print(f"\n🔍 Debug - Clé publique (à garder secrète):")
        print(f"   {public_key[:50]}...")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des clés: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())