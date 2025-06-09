#!/usr/bin/env python3
"""
Script pour créer des données de test pour le portfolio
"""
import sys
import os

# Ajouter le répertoire parent au path pour permettre les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from decimal import Decimal
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.etf import ETF
from app.models.portfolio import Portfolio, Position, Transaction, TransactionType
from app.core.security import get_password_hash
import uuid

def create_test_data():
    """Crée des données de test pour le portfolio"""
    db = SessionLocal()
    
    try:
        # Créer un utilisateur de test s'il n'existe pas
        test_email = "test@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        
        if not user:
            user = User(
                email=test_email,
                full_name="Test User",
                hashed_password=get_password_hash("testpassword123"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Utilisateur créé: {user.email}")
        else:
            print(f"✅ Utilisateur existant: {user.email}")
        
        # Créer les ETFs s'ils n'existent pas
        etfs_data = [
            {
                'isin': 'IE00B4L5Y983',
                'name': 'iShares Core MSCI World UCITS ETF',
                'sector': 'Global Developed',
                'currency': 'EUR',
                'exchange': 'Euronext Amsterdam'
            },
            {
                'isin': 'IE00BK5BQT80',
                'name': 'Vanguard FTSE All-World UCITS ETF',
                'sector': 'Global All Cap',
                'currency': 'EUR',
                'exchange': 'XETRA'
            },
            {
                'isin': 'IE00B5BMR087',
                'name': 'iShares Core S&P 500 UCITS ETF',
                'sector': 'US Large Cap',
                'currency': 'GBP',
                'exchange': 'London Stock Exchange'
            }
        ]
        
        for etf_info in etfs_data:
            etf = db.query(ETF).filter(ETF.isin == etf_info['isin']).first()
            if not etf:
                etf = ETF(**etf_info)
                db.add(etf)
                print(f"✅ ETF créé: {etf_info['name']}")
        
        db.commit()
        
        # Créer un portfolio de test
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        if not portfolio:
            portfolio = Portfolio(
                user_id=user.id,
                name="Portfolio Principal"
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            print(f"✅ Portfolio créé: {portfolio.name}")
        else:
            print(f"✅ Portfolio existant: {portfolio.name}")
        
        # Créer des transactions de test
        transactions_data = [
            {
                'etf_isin': 'IE00B4L5Y983',  # IWDA
                'transaction_type': TransactionType.BUY,
                'quantity': Decimal('50'),
                'price': Decimal('98.50'),
                'fees': Decimal('2.50')
            },
            {
                'etf_isin': 'IE00BK5BQT80',  # VWCE
                'transaction_type': TransactionType.BUY,
                'quantity': Decimal('30'),
                'price': Decimal('128.75'),
                'fees': Decimal('2.00')
            },
            {
                'etf_isin': 'IE00B5BMR087',  # CSPX
                'transaction_type': TransactionType.BUY,
                'quantity': Decimal('20'),
                'price': Decimal('635.20'),
                'fees': Decimal('3.00')
            }
        ]
        
        # Supprimer les anciennes transactions/positions pour refaire les tests
        existing_transactions = db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id).all()
        for trans in existing_transactions:
            db.delete(trans)
        
        existing_positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        for pos in existing_positions:
            db.delete(pos)
        
        db.commit()
        
        # Créer les nouvelles transactions et positions
        for trans_data in transactions_data:
            # Créer la transaction
            transaction = Transaction(
                portfolio_id=portfolio.id,
                **trans_data
            )
            db.add(transaction)
            
            # Créer ou mettre à jour la position
            position = Position(
                portfolio_id=portfolio.id,
                etf_isin=trans_data['etf_isin'],
                quantity=trans_data['quantity'],
                average_price=trans_data['price']
            )
            db.add(position)
            
            print(f"✅ Transaction créée: {trans_data['quantity']} parts de {trans_data['etf_isin']}")
        
        db.commit()
        
        print("\n🎉 Données de test créées avec succès!")
        print(f"📧 Email: {test_email}")
        print(f"🔑 Mot de passe: testpassword123")
        print(f"📊 Portfolio ID: {portfolio.id}")
        
        # Afficher un résumé du portfolio
        from app.services.portfolio_service import PortfolioCalculationService
        portfolio_service = PortfolioCalculationService()
        
        portfolio_calc = portfolio_service.calculate_portfolio_value(db, str(portfolio.id))
        today_pnl = portfolio_service.calculate_today_pnl(db, str(portfolio.id))
        
        print(f"\n📈 RÉSUMÉ DU PORTFOLIO:")
        print(f"   💰 Valeur totale: €{portfolio_calc.get('total_value', 0):,.2f}")
        print(f"   📊 Coût total: €{portfolio_calc.get('total_cost', 0):,.2f}")
        print(f"   📈 P&L total: €{portfolio_calc.get('total_pnl', 0):,.2f} ({portfolio_calc.get('total_pnl_percent', 0):.2f}%)")
        print(f"   📅 P&L du jour: €{today_pnl.get('today_pnl', 0):,.2f} ({today_pnl.get('today_pnl_percent', 0):.2f}%)")
        print(f"   📋 Positions: {portfolio_calc.get('positions_count', 0)}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()