#!/usr/bin/env python3
"""
Script pour créer des signaux de test
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.signal import Signal, SignalType
from app.models.etf import ETF
import uuid

def create_test_signals():
    """Crée des signaux de test réalistes"""
    db = SessionLocal()
    
    try:
        # Supprimer les anciens signaux de test
        db.query(Signal).delete()
        db.commit()
        
        # ETFs disponibles
        etfs = db.query(ETF).all()
        if not etfs:
            print("❌ Aucun ETF trouvé. Exécutez d'abord create_test_portfolio.py")
            return
        
        # Types de signaux avec probabilités réalistes
        signal_types = [SignalType.BUY, SignalType.SELL, SignalType.HOLD, SignalType.WAIT]
        signal_weights = [0.3, 0.2, 0.35, 0.15]  # Plus de HOLD que de BUY/SELL
        
        signals_data = []
        
        for i in range(15):  # Créer 15 signaux
            etf = random.choice(etfs)
            signal_type = random.choices(signal_types, weights=signal_weights)[0]
            
            # Confidence réaliste selon le type de signal
            if signal_type in [SignalType.BUY, SignalType.SELL]:
                confidence = random.uniform(65, 95)  # Signaux d'action plus confiants
            else:
                confidence = random.uniform(50, 80)  # HOLD/WAIT moins confiants
            
            # Prix basés sur des données réalistes
            base_price = random.uniform(80, 150)
            
            # Prix cible et stop loss selon le type
            price_target = None
            stop_loss = None
            
            if signal_type == SignalType.BUY:
                price_target = base_price * random.uniform(1.05, 1.20)  # +5% à +20%
                stop_loss = base_price * random.uniform(0.92, 0.97)     # -3% à -8%
            elif signal_type == SignalType.SELL:
                price_target = base_price * random.uniform(0.90, 0.98)  # -2% à -10%
                stop_loss = base_price * random.uniform(1.02, 1.08)     # +2% à +8%
            
            # Scores techniques et de risque
            technical_score = random.uniform(40, 90)
            risk_score = random.uniform(20, 80)
            
            # Dates réalistes
            created_at = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            expires_at = created_at + timedelta(days=random.randint(7, 30))
            
            # Probabilité d'être actif (90% actifs)
            is_active = random.random() < 0.9
            
            signal_data = {
                'id': str(uuid.uuid4()),
                'etf_isin': etf.isin,
                'signal_type': signal_type,
                'confidence': Decimal(str(round(confidence, 1))),
                'price_target': Decimal(str(round(price_target, 2))) if price_target else None,
                'stop_loss': Decimal(str(round(stop_loss, 2))) if stop_loss else None,
                'technical_score': Decimal(str(round(technical_score, 1))),
                'risk_score': Decimal(str(round(risk_score, 1))),
                'is_active': is_active,
                'created_at': created_at,
                'expires_at': expires_at if is_active else None
            }
            
            signals_data.append(signal_data)
        
        # Insérer les signaux
        for signal_data in signals_data:
            signal = Signal(**signal_data)
            db.add(signal)
        
        db.commit()
        
        # Statistiques
        active_signals = [s for s in signals_data if s['is_active']]
        type_counts = {}
        for signal_type in SignalType:
            count = sum(1 for s in active_signals if s['signal_type'] == signal_type)
            type_counts[signal_type.value] = count
        
        avg_confidence = sum(float(s['confidence']) for s in active_signals) / len(active_signals) if active_signals else 0
        
        print("✅ Signaux de test créés avec succès!")
        print(f"📊 Total des signaux: {len(signals_data)}")
        print(f"📈 Signaux actifs: {len(active_signals)}")
        print(f"🎯 Confiance moyenne: {avg_confidence:.1f}%")
        print()
        print("📋 Répartition par type:")
        for signal_type, count in type_counts.items():
            print(f"   {signal_type}: {count}")
        
        print()
        print("📝 Signaux les plus récents:")
        recent_signals = sorted(active_signals, key=lambda x: x['created_at'], reverse=True)[:5]
        for signal in recent_signals:
            etf_name = next((e.name for e in etfs if e.isin == signal['etf_isin']), signal['etf_isin'])
            print(f"   {signal['signal_type'].value} {etf_name[:30]}... ({signal['confidence']}%)")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_signals()