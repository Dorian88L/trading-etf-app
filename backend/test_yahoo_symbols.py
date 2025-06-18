#!/usr/bin/env python3
"""
Test des symboles Yahoo Finance pour les ETFs européens
"""
import yfinance as yf
import sys

# Symboles à tester
test_symbols = [
    # Versions multiples pour les mêmes ETFs
    'IWDA.AS',     # Amsterdam
    'IWDA.L',      # London  
    'IWDA.MI',     # Milan
    'CSPX.L',      # London
    'CSPX.MI',     # Milan
    'VWCE.DE',     # Xetra
    'VWRL.L',      # London (Vanguard All-World)
    'VUSA.L',      # London
    'VUSA.AS',     # Amsterdam
    'SXR8.DE',     # S&P 500 EUR
    'EUNL.DE',     # MSCI World EUR
    'XMAW.DE',     # Xtrackers MSCI World
]

print("🧪 Test des symboles Yahoo Finance...")
print("=" * 50)

working_symbols = []
failed_symbols = []

for symbol in test_symbols:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period='1d')
        
        if not hist.empty and 'regularMarketPrice' in info:
            price = info.get('regularMarketPrice', hist['Close'].iloc[-1])
            name = info.get('longName', info.get('shortName', 'N/A'))
            currency = info.get('currency', 'N/A')
            
            print(f"✅ {symbol}: {name[:50]}...")
            print(f"   Prix: {price:.2f} {currency}")
            working_symbols.append({
                'symbol': symbol,
                'name': name,
                'price': price,
                'currency': currency
            })
        else:
            failed_symbols.append(symbol)
            print(f"❌ {symbol}: Pas de données")
            
    except Exception as e:
        failed_symbols.append(symbol)
        print(f"❌ {symbol}: Erreur - {str(e)[:50]}")

print("\n" + "=" * 50)
print(f"✅ Symboles fonctionnels: {len(working_symbols)}")
print(f"❌ Symboles en échec: {len(failed_symbols)}")

if working_symbols:
    print("\n🎯 Symboles recommandés:")
    for etf in working_symbols[:5]:  # Top 5
        print(f"  {etf['symbol']}: {etf['price']:.2f} {etf['currency']}")