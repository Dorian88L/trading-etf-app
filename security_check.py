#!/usr/bin/env python3
"""
Script de validation de sécurité pour l'application Trading ETF
Vérifie que toutes les corrections de sécurité sont appliquées
"""
import os
import sys
import subprocess
from typing import List, Tuple

class SecurityValidator:
    def __init__(self):
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0
        
    def check(self, name: str, condition: bool, message: str, warning: bool = False) -> bool:
        """Effectue une vérification de sécurité"""
        if condition:
            print(f"✅ {name}: {message}")
            self.passed_checks += 1
            return True
        else:
            if warning:
                print(f"⚠️  {name}: {message}")
                self.warnings += 1
            else:
                print(f"❌ {name}: {message}")
                self.failed_checks += 1
            return False
    
    def check_file_exists(self, name: str, file_path: str, required: bool = True) -> bool:
        """Vérifie l'existence d'un fichier"""
        exists = os.path.exists(file_path)
        if exists:
            print(f"✅ {name}: Fichier trouvé")
            self.passed_checks += 1
        else:
            if required:
                print(f"❌ {name}: Fichier manquant: {file_path}")
                self.failed_checks += 1
            else:
                print(f"⚠️  {name}: Fichier optionnel manquant: {file_path}")
                self.warnings += 1
        return exists
    
    def check_file_content(self, name: str, file_path: str, content_checks: List[str], 
                          all_required: bool = True) -> bool:
        """Vérifie le contenu d'un fichier"""
        if not os.path.exists(file_path):
            print(f"❌ {name}: Fichier non trouvé: {file_path}")
            self.failed_checks += 1
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_checks = []
            for check in content_checks:
                if check in content:
                    found_checks.append(check)
            
            if all_required:
                success = len(found_checks) == len(content_checks)
            else:
                success = len(found_checks) > 0
            
            if success:
                print(f"✅ {name}: Contenu validé ({len(found_checks)}/{len(content_checks)} vérifications)")
                self.passed_checks += 1
            else:
                missing = [check for check in content_checks if check not in found_checks]
                print(f"❌ {name}: Contenu manquant: {missing}")
                self.failed_checks += 1
            
            return success
            
        except Exception as e:
            print(f"❌ {name}: Erreur lecture fichier: {e}")
            self.failed_checks += 1
            return False
    
    def check_environment_variable(self, name: str, var_name: str, required: bool = True) -> bool:
        """Vérifie une variable d'environnement"""
        value = os.getenv(var_name)
        has_value = value is not None and value.strip() != ""
        
        if has_value:
            # Masquer les valeurs sensibles
            if 'secret' in var_name.lower() or 'key' in var_name.lower() or 'password' in var_name.lower():
                display_value = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"✅ {name}: Variable définie ({display_value})")
            self.passed_checks += 1
        else:
            if required:
                print(f"❌ {name}: Variable d'environnement manquante: {var_name}")
                self.failed_checks += 1
            else:
                print(f"⚠️  {name}: Variable optionnelle manquante: {var_name}")
                self.warnings += 1
        
        return has_value

def main():
    print("🔒 VALIDATION DE SÉCURITÉ - TRADING ETF")
    print("=" * 50)
    
    validator = SecurityValidator()
    
    # 1. Vérification des fichiers de configuration de sécurité
    print("\n📁 FICHIERS DE CONFIGURATION")
    validator.check_file_exists(
        "Fichier de sécurité", 
        ".env.security"
    )
    
    # 2. Vérification des corrections de code
    print("\n🔧 CORRECTIONS DE SÉCURITÉ")
    
    # Configuration JWT sécurisée
    validator.check_file_content(
        "Configuration JWT sécurisée",
        "backend/app/core/config.py",
        [
            'os.getenv("JWT_SECRET_KEY")',
            'def __post_init__(self)',
            'JWT_SECRET_KEY manquante'
        ]
    )
    
    # Validation des mots de passe
    validator.check_file_content(
        "Validation mots de passe",
        "backend/app/schemas/user.py",
        [
            '@validator(\'password\')',
            'validate_password_strength',
            'au moins 3 types parmi'
        ]
    )
    
    # Correction refresh token
    validator.check_file_content(
        "Sécurisation refresh token",
        "backend/app/api/v1/endpoints/auth.py",
        [
            'uuid.UUID(str(user_id))',
            'Invalid user identifier',
            'except (ValueError, TypeError)'
        ]
    )
    
    # Import API corrigé
    validator.check_file_content(
        "Import API complet",
        "backend/app/api/v1/api.py",
        [
            'historical_data'
        ]
    )
    
    # Headers CORS sécurisés
    validator.check_file_content(
        "Headers CORS sécurisés",
        "backend/app/main.py",
        [
            '"Authorization"',
            '"X-CSRFToken"',
            '"Content-Type"'
        ]
    )
    
    # Validators de données
    validator.check_file_exists(
        "Validators de sécurité",
        "backend/app/core/validators.py"
    )
    
    # 3. Vérification des variables d'environnement critiques
    print("\n🌍 VARIABLES D'ENVIRONNEMENT")
    validator.check_environment_variable("Clé secrète JWT", "JWT_SECRET_KEY")
    validator.check_environment_variable("URL Base de données", "DATABASE_URL", required=False)
    validator.check_environment_variable("Environnement", "ENVIRONMENT", required=False)
    
    # 4. Vérification des permissions de fichiers
    print("\n🔐 PERMISSIONS ET ACCÈS")
    
    # Vérifier que .env.security n'est pas dans git
    if os.path.exists('.env.security'):
        try:
            result = subprocess.run(['git', 'status', '--porcelain', '.env.security'], 
                                  capture_output=True, text=True, cwd='.')
            is_tracked = result.returncode == 0 and result.stdout.strip() != ""
            
            validator.check(
                "Fichier .env.security non tracké",
                not is_tracked,
                "Le fichier .env.security ne doit pas être dans git" if is_tracked 
                else "Fichier correctement ignoré par git",
                warning=is_tracked
            )
        except:
            print("⚠️  Impossible de vérifier le statut git")
            validator.warnings += 1
    
    # 5. Tests de sécurité basiques
    print("\n🧪 TESTS DE SÉCURITÉ")
    
    # Test de validation d'ISIN
    try:
        sys.path.append('backend')
        from app.core.validators import validate_isin
        
        # Test ISIN valide
        try:
            validate_isin("IE00B4L5Y983")
            validator.check("Validation ISIN valide", True, "ISIN valide accepté")
        except:
            validator.check("Validation ISIN valide", False, "Échec validation ISIN valide")
        
        # Test ISIN invalide
        try:
            validate_isin("INVALID")
            validator.check("Rejet ISIN invalide", False, "ISIN invalide accepté à tort")
        except ValueError:
            validator.check("Rejet ISIN invalide", True, "ISIN invalide correctement rejeté")
        except:
            validator.check("Rejet ISIN invalide", False, "Erreur inattendue validation ISIN")
            
    except ImportError:
        validator.check("Tests validators", False, "Impossible d'importer les validators")
    
    # 6. Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DE SÉCURITÉ")
    print("=" * 50)
    
    total_checks = validator.passed_checks + validator.failed_checks
    success_rate = (validator.passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"✅ Tests réussis: {validator.passed_checks}")
    print(f"❌ Tests échoués: {validator.failed_checks}")
    print(f"⚠️  Avertissements: {validator.warnings}")
    print(f"📈 Taux de réussite: {success_rate:.1f}%")
    
    if validator.failed_checks == 0:
        print("\n🎉 TOUTES LES VÉRIFICATIONS CRITIQUES SONT PASSÉES!")
        print("🔒 L'application est sécurisée selon les standards vérifiés.")
        if validator.warnings > 0:
            print(f"⚠️  {validator.warnings} avertissement(s) à considérer pour optimisation.")
        return 0
    else:
        print(f"\n🚨 {validator.failed_checks} VÉRIFICATION(S) CRITIQUE(S) ÉCHOUÉE(S)")
        print("❌ Corriger ces problèmes avant mise en production!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)