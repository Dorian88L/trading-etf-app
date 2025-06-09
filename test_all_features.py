#!/usr/bin/env python3
"""
Script de test complet pour vérifier toutes les fonctionnalités de l'application Trading ETF
"""
import requests
import time
import json
from datetime import datetime

def test_backend_apis():
    """Test toutes les APIs du backend"""
    base_url = "http://localhost:8002/api/v1"
    
    print("🚀 TEST COMPLET DES APIS BACKEND")
    print("=" * 50)
    
    endpoints = [
        {
            'name': 'ETFs temps réel',
            'url': f'{base_url}/market/real-etfs',
            'method': 'GET',
            'auth': False
        },
        {
            'name': 'Signaux de démonstration',
            'url': f'{base_url}/market/signals-demo',
            'method': 'GET',
            'auth': False
        },
        {
            'name': 'Indices européens',
            'url': f'{base_url}/market/enhanced-indices',
            'method': 'GET',
            'auth': False
        },
        {
            'name': 'Statistiques dashboard',
            'url': f'{base_url}/market/dashboard-stats',
            'method': 'GET',
            'auth': False
        },
        {
            'name': 'Monitoring santé',
            'url': f'{base_url}/monitoring/health',
            'method': 'GET',
            'auth': False
        },
        {
            'name': 'Cache statistiques',
            'url': f'{base_url}/monitoring/cache/stats',
            'method': 'GET',
            'auth': False
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(endpoint['url'], timeout=5)
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'name': endpoint['name'],
                    'status': '✅ SUCCESS',
                    'response_time': f'{response_time}ms',
                    'details': extract_details(data)
                }
            else:
                result = {
                    'name': endpoint['name'],
                    'status': f'❌ HTTP {response.status_code}',
                    'response_time': f'{response_time}ms',
                    'details': 'Erreur HTTP'
                }
                
            results.append(result)
            
        except requests.exceptions.Timeout:
            results.append({
                'name': endpoint['name'],
                'status': '⏰ TIMEOUT',
                'response_time': '>5000ms',
                'details': 'Délai d\'attente dépassé'
            })
        except Exception as e:
            results.append({
                'name': endpoint['name'],
                'status': '💥 ERROR',
                'response_time': 'N/A',
                'details': str(e)[:50]
            })
    
    # Afficher les résultats
    for result in results:
        print(f"{result['status']} {result['name']}: {result['response_time']}")
        print(f"   {result['details']}\n")
    
    # Statistiques globales
    success_count = sum(1 for r in results if '✅' in r['status'])
    total_count = len(results)
    
    print(f"📊 RÉSULTAT GLOBAL: {success_count}/{total_count} APIs fonctionnelles")
    print(f"🎯 Taux de succès: {(success_count/total_count)*100:.1f}%")
    
    return success_count == total_count

def extract_details(data):
    """Extrait les détails pertinents de la réponse API"""
    if isinstance(data, dict):
        if 'count' in data:
            return f"{data['count']} éléments"
        elif 'data' in data and isinstance(data['data'], dict):
            if 'total_etfs' in data['data']:
                return f"Marché: {data['data']['total_etfs']} ETFs, {data['data']['avg_change_percent']:+.2f}%"
            elif 'api_status' in data['data']:
                return f"Santé: {data['data']['api_status']}, Cache: {data['data']['cache_entries']} entrées"
            elif 'total_entries' in data['data']:
                return f"Cache: {data['data']['total_entries']} entrées, {data['data']['valid_entries']} valides"
            else:
                return f"{len(data['data'])} éléments"
        elif 'status' in data:
            return data['status']
    return "Données reçues"

def test_real_data_accuracy():
    """Teste la précision des données temps réel"""
    print("\n🎯 TEST DE PRÉCISION DES DONNÉES")
    print("=" * 50)
    
    try:
        # Test CAC 40
        response = requests.get("http://localhost:8002/api/v1/market/enhanced-indices")
        data = response.json()
        
        cac40_data = next((v for k, v in data['data'].items() if 'CAC40' in k), None)
        
        if cac40_data:
            price = cac40_data['value']
            change = cac40_data['change_percent']
            source = cac40_data['source']
            confidence = cac40_data['confidence'] * 100
            
            print(f"📈 CAC 40: {price:,.2f} EUR ({change:+.2f}%)")
            print(f"   Source: {source} (Confiance: {confidence:.0f}%)")
            
            # Validation basique
            if 7000 <= price <= 9000:  # Fourchette réaliste pour le CAC 40
                print("   ✅ Prix dans la fourchette réaliste")
            else:
                print("   ⚠️  Prix en dehors de la fourchette attendue")
                
            if abs(change) <= 10:  # Variation journalière réaliste
                print("   ✅ Variation journalière réaliste")
            else:
                print("   ⚠️  Variation journalière suspecte")
        
        # Test ETFs
        etf_response = requests.get("http://localhost:8002/api/v1/market/real-etfs")
        etf_data = etf_response.json()
        
        if etf_data['status'] == 'success':
            print(f"\n📊 ETFs: {etf_data['count']} disponibles")
            
            for etf in etf_data['data'][:3]:  # Premiers 3 ETFs
                print(f"   {etf['symbol']}: {etf['current_price']:.2f} {etf['currency']} ({etf['change_percent']:+.2f}%)")
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de précision: {e}")
        return False

def test_frontend_accessibility():
    """Teste l'accessibilité du frontend"""
    print("\n🌐 TEST D'ACCESSIBILITÉ FRONTEND")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        
        if response.status_code == 200:
            print("✅ Frontend accessible sur http://localhost:3000")
            
            # Vérifier la présence des éléments React
            content = response.text
            if 'root' in content and 'react' in content.lower():
                print("✅ Application React détectée")
            else:
                print("⚠️  Structure React non détectée")
                
            return True
        else:
            print(f"❌ Frontend inaccessible (HTTP {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend non accessible - serveur peut-être arrêté")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test frontend: {e}")
        return False

def main():
    """Fonction principale de test"""
    print(f"🔍 TEST COMPLET DE L'APPLICATION TRADING ETF")
    print(f"⏰ Démarré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Tests
    backend_ok = test_backend_apis()
    data_ok = test_real_data_accuracy()
    frontend_ok = test_frontend_accessibility()
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ FINAL DES TESTS")
    print("=" * 60)
    
    tests = [
        ("APIs Backend", backend_ok),
        ("Données temps réel", data_ok),
        ("Frontend", frontend_ok)
    ]
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    all_passed = all(result for _, result in tests)
    
    if all_passed:
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("🚀 Application Trading ETF prête pour utilisation")
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    print(f"\n⏰ Terminé le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)