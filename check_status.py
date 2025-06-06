#!/usr/bin/env python3

"""
Script de vérification du statut de l'application Trading ETF
"""

import requests
import json
from datetime import datetime

def check_service(name, url, expected_key=None):
    """Vérifie le statut d'un service"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            if expected_key:
                data = response.json()
                if expected_key in str(data):
                    return "✅ ONLINE", response.json()
                else:
                    return "⚠️  PARTIAL", response.text[:100]
            else:
                return "✅ ONLINE", "OK"
        else:
            return "❌ ERROR", f"Status: {response.status_code}"
    except Exception as e:
        return "❌ OFFLINE", str(e)

def main():
    print("🚀 Trading ETF Application Status Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Services à vérifier
    services = [
        ("Backend Health", "http://localhost:8000/health", "healthy"),
        ("Frontend", "http://localhost:3000", "html"),
        ("Authentication", "http://localhost:8000/api/v1/auth/login", None),
        ("Advanced Signals", "http://localhost:8000/api/v1/signals/advanced", "etf_"),
        ("Market Data", "http://localhost:8000/api/v1/market-data/FR0010296061", "timestamp"),
        ("Market Indices", "http://localhost:8000/api/v1/indices", "CAC"),
    ]

    all_services_ok = True
    
    for service_name, url, key in services:
        status, info = check_service(service_name, url, key)
        print(f"{service_name:20s} {status}")
        
        if "ERROR" in status or "OFFLINE" in status:
            all_services_ok = False
            print(f"   Error: {info}")
        elif "PARTIAL" in status:
            print(f"   Warning: {info}")
            
    print()
    
    if all_services_ok:
        print("🎉 Application Status: ALL SYSTEMS OPERATIONAL")
        print()
        print("✅ Frontend: http://localhost:3000")
        print("✅ Backend API: http://localhost:8000")
        print("✅ Health Check: http://localhost:8000/health")
        print("✅ API Docs: http://localhost:8000/docs")
        print()
        print("🔐 Test Account:")
        print("   Email: test@trading.com")
        print("   Password: test123")
        print()
        print("📊 Available Features:")
        print("   • Advanced signals with 0-100 scoring")
        print("   • Real-time market data")
        print("   • Interactive charts with technical indicators")
        print("   • Market indices and sentiment analysis")
        print("   • 4 trading algorithms (Breakout, Mean Reversion, Momentum, Statistical Arbitrage)")
        print("   • Risk/Reward analysis")
        print("   • Professional dashboard")
        
        # Test d'un signal avancé
        try:
            resp = requests.get("http://localhost:8000/api/v1/signals/advanced?limit=1")
            if resp.status_code == 200:
                signal = resp.json()[0]
                print(f"\n📈 Latest Signal Sample:")
                print(f"   {signal['etf_name']}")
                print(f"   Signal: {signal['signal_type']} | Confidence: {signal['confidence']}%")
                print(f"   Algorithm: {signal['algorithm_type']}")
                print(f"   Expected Return: {signal['expected_return']}%")
                print(f"   Risk/Reward: 1:{signal['risk_reward_ratio']}")
        except:
            pass
            
    else:
        print("❌ Application Status: SOME ISSUES DETECTED")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check if all processes are running:")
        print("      ps aux | grep -E '(uvicorn|node)' | grep -v grep")
        print("   2. Restart services:")
        print("      cd /home/dorian/trading-etf-app")
        print("      ./restart_app.sh")
        print("   3. Check logs:")
        print("      tail -f backend/backend.log")

if __name__ == "__main__":
    main()