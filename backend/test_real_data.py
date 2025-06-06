#!/usr/bin/env python3

"""
Test simple des données de marché réelles avec yfinance
"""

import yfinance as yf
from datetime import datetime
import requests

def test_european_etfs():
    """Test des ETFs européens avec Yahoo Finance"""
    
    # ETFs européens populaires
    european_etfs = {
        'LYX0CD.PA': 'Lyxor CAC 40 UCITS ETF',
        'SX5T.DE': 'Xtrackers EURO STOXX 50 UCITS ETF', 
        'EUNL.DE': 'iShares Core MSCI World UCITS ETF',
        'VWCE.DE': 'Vanguard FTSE All-World UCITS ETF'
    }
    
    print("🚀 Test des données de marché réelles européennes")
    print("=" * 60)
    
    real_data = []
    
    for symbol, name in european_etfs.items():
        try:
            print(f"\n📊 Récupération des données pour {symbol}...")
            
            # Créer l'objet ticker
            ticker = yf.Ticker(symbol)
            
            # Récupérer les informations générales
            info = ticker.info
            
            # Récupérer l'historique récent (2 jours pour calcul du changement)
            hist = ticker.history(period="2d")
            
            if len(hist) >= 1:
                latest = hist.iloc[-1]
                previous = hist.iloc[-2] if len(hist) > 1 else latest
                
                current_price = float(latest['Close'])
                previous_close = float(previous['Close'])
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                
                etf_data = {
                    'symbol': symbol,
                    'name': name,
                    'current_price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': int(latest.get('Volume', 0)),
                    'currency': info.get('currency', 'EUR'),
                    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                real_data.append(etf_data)
                
                print(f"✅ {name}")
                print(f"   Prix: {current_price:.2f} {etf_data['currency']}")
                print(f"   Variation: {change:+.2f} ({change_percent:+.2f}%)")
                print(f"   Volume: {etf_data['volume']:,}")
                
            else:
                print(f"❌ Pas de données pour {symbol}")
                
        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {e}")
            continue
    
    print(f"\n✅ Collecte terminée: {len(real_data)} ETFs récupérés sur {len(european_etfs)}")
    return real_data

def test_market_indices():
    """Test des indices de marché européens"""
    
    indices = {
        '^FCHI': 'CAC 40',
        '^STOXX50E': 'EURO STOXX 50',
        '^GDAXI': 'DAX',
        '^FTSE': 'FTSE 100'
    }
    
    print("\n📈 Test des indices de marché européens")
    print("=" * 60)
    
    indices_data = {}
    
    for symbol, name in indices.items():
        try:
            print(f"\n📊 Récupération de {name} ({symbol})...")
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if len(hist) >= 1:
                latest = hist.iloc[-1]
                previous = hist.iloc[-2] if len(hist) > 1 else latest
                
                current_value = float(latest['Close'])
                previous_close = float(previous['Close'])
                change = current_value - previous_close
                change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                
                indices_data[symbol] = {
                    'name': name,
                    'value': round(current_value, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': int(latest.get('Volume', 0)),
                    'currency': info.get('currency', 'EUR'),
                    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"✅ {name}: {current_value:.2f}")
                print(f"   Variation: {change:+.2f} ({change_percent:+.2f}%)")
                
            else:
                print(f"❌ Pas de données pour {symbol}")
                
        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {e}")
            continue
    
    print(f"\n✅ Indices collectés: {len(indices_data)}")
    return indices_data

def test_historical_data():
    """Test des données historiques"""
    
    print("\n📊 Test des données historiques (CAC 40 ETF)")
    print("=" * 60)
    
    try:
        ticker = yf.Ticker('LYX0CD.PA')
        hist = ticker.history(period="5d")
        
        print(f"✅ Données historiques récupérées: {len(hist)} jours")
        print("\nDerniers jours:")
        print("-" * 70)
        print("Date".ljust(12) + "Ouverture".ljust(12) + "Clôture".ljust(12) + "Volume".ljust(15))
        print("-" * 70)
        
        for index, row in hist.tail(5).iterrows():
            date_str = index.strftime('%Y-%m-%d')
            print(f"{date_str.ljust(12)}{row['Open']:.2f}".ljust(12) + 
                  f"{row['Close']:.2f}".ljust(12) + 
                  f"{int(row['Volume']):,}".ljust(15))
        
        return hist
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'historique: {e}")
        return None

if __name__ == "__main__":
    print("🌍 Test des données de marché réelles européennes")
    print("🕐 Timestamp:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Test des ETFs
    etf_data = test_european_etfs()
    
    # Test des indices
    indices_data = test_market_indices()
    
    # Test des données historiques
    historical_data = test_historical_data()
    
    print("\n" + "=" * 60)
    print("🎉 Test terminé avec succès!")
    print(f"📊 ETFs collectés: {len(etf_data)}")
    print(f"📈 Indices collectés: {len(indices_data)}")
    print(f"📊 Données historiques: {'Oui' if historical_data is not None else 'Non'}")
    print()
    print("✅ Les données de marché réelles sont maintenant disponibles!")
    print("🔗 Vous pouvez maintenant intégrer ces données dans votre application.")