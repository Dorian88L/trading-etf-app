#!/usr/bin/env python3
"""
Test de l'API Financial Modeling Prep
"""
import sys
sys.path.append('/app')
import requests
from app.core.config import settings

# Symboles ETFs européens à tester
etf_symbols = [
    'IWDA.L',    # iShares MSCI World
    'CSPX.L',    # iShares S&P 500
    'VWRL.L',    # Vanguard All-World  
    'VUSA.L',    # Vanguard S&P 500
    'EXS1.DE',   # iShares DAX
    'SX5E.DE',   # iShares EURO STOXX 50
]

print(f"🧪 Test de Financial Modeling Prep API")
print(f"Clé API: {settings.FINANCIAL_MODELING_PREP_API_KEY[:10]}...")
print("=" * 50)

working_symbols = []

for symbol in etf_symbols:
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        params = {'apikey': settings.FINANCIAL_MODELING_PREP_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                price = item.get('price', 0)
                change = item.get('change', 0)
                name = item.get('name', 'N/A')
                
                print(f"✅ {symbol}: {name[:40]}...")
                print(f"   Prix: {price:.2f}, Variation: {change:.2f}")
                working_symbols.append(symbol)
            else:
                print(f"❌ {symbol}: Données vides")
        else:
            print(f"❌ {symbol}: Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ {symbol}: Erreur - {str(e)[:50]}")

print("\n" + "=" * 50)
print(f"✅ Symboles fonctionnels avec FMP: {len(working_symbols)}")

# Test d'indices aussi
print("\n🔍 Test des indices européens...")
indices = ['^FCHI', '^GDAXI', '^FTSE', '^STOXX50E']

for index in indices:
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{index}"
        params = {'apikey': settings.FINANCIAL_MODELING_PREP_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                price = item.get('price', 0)
                print(f"✅ {index}: {price:.2f}")
            else:
                print(f"❌ {index}: Données vides")
        else:
            print(f"❌ {index}: Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {index}: Erreur - {str(e)[:30]}")