#!/usr/bin/env python3
"""
Test de l'API Alpha Vantage
"""
import sys
sys.path.append('/app')
import requests
from app.core.config import settings

print(f"🧪 Test de Alpha Vantage API")
print(f"Clé API: {settings.ALPHA_VANTAGE_API_KEY}")
print("=" * 50)

# Test avec des symboles US d'abord
us_symbols = ['AAPL', 'MSFT', 'SPY', 'QQQ']

for symbol in us_symbols:
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = quote.get('05. price', 'N/A')
                change = quote.get('09. change', 'N/A')
                
                print(f"✅ {symbol}: Prix {price}, Variation {change}")
            else:
                print(f"❌ {symbol}: {data}")
        else:
            print(f"❌ {symbol}: Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ {symbol}: Erreur - {str(e)[:50]}")

# Test avec ETFs européens
print("\n🇪🇺 Test ETFs européens...")
eu_symbols = ['VTI', 'URTH', 'EWJ']  # ETFs disponibles sur Alpha Vantage

for symbol in eu_symbols:
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = quote.get('05. price', 'N/A')
                change = quote.get('09. change', 'N/A')
                
                print(f"✅ {symbol}: Prix {price}, Variation {change}")
            else:
                print(f"❌ {symbol}: {data}")
                
    except Exception as e:
        print(f"❌ {symbol}: Erreur - {str(e)[:50]}")