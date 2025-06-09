from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.portfolio import Portfolio, Position, Transaction, TransactionType
from app.models.etf import ETF
from app.schemas.portfolio import (
    PortfolioResponse, 
    PortfolioCreate, 
    PositionResponse, 
    TransactionResponse, 
    TransactionCreate
)
from app.services.portfolio_service import get_portfolio_calculation_service

router = APIRouter()


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's portfolio positions"""
    # Get user's default portfolio (first one)
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        return []
    
    positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
    return positions


@router.post("/transaction", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new transaction"""
    # Verify ETF exists
    etf = db.query(ETF).filter(ETF.isin == transaction.etf_isin).first()
    if not etf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETF not found"
        )
    
    # Get or create portfolio
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == transaction.portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Create transaction
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    
    # Update or create position
    position = db.query(Position).filter(
        Position.portfolio_id == portfolio.id,
        Position.etf_isin == transaction.etf_isin
    ).first()
    
    if position:
        # Update existing position
        if transaction.transaction_type == TransactionType.BUY:
            total_value = (position.quantity * position.average_price) + (transaction.quantity * transaction.price)
            total_quantity = position.quantity + transaction.quantity
            position.average_price = total_value / total_quantity
            position.quantity = total_quantity
        else:  # SELL
            position.quantity -= transaction.quantity
            if position.quantity <= 0:
                db.delete(position)
    else:
        # Create new position (only for BUY)
        if transaction.transaction_type == TransactionType.BUY:
            position = Position(
                portfolio_id=portfolio.id,
                etf_isin=transaction.etf_isin,
                quantity=transaction.quantity,
                average_price=transaction.price
            )
            db.add(position)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.get("/performance")
def get_portfolio_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    portfolio_service = Depends(get_portfolio_calculation_service)
):
    """Get real portfolio performance based on actual positions and market data"""
    # Get user's default portfolio (first one)
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        return {
            "total_value": 0.0,
            "total_gain_loss": 0.0,
            "total_gain_loss_percent": 0.0,
            "day_change": 0.0,
            "day_change_percent": 0.0,
            "positions_count": 0,
            "cash_balance": 0.0,
            "positions_detail": []
        }
    
    # Calculate real portfolio values
    portfolio_calc = portfolio_service.calculate_portfolio_value(db, str(portfolio.id))
    today_pnl = portfolio_service.calculate_today_pnl(db, str(portfolio.id))
    
    return {
        "total_value": portfolio_calc.get('total_value', 0.0),
        "total_gain_loss": portfolio_calc.get('total_pnl', 0.0),
        "total_gain_loss_percent": portfolio_calc.get('total_pnl_percent', 0.0),
        "day_change": today_pnl.get('today_pnl', 0.0),
        "day_change_percent": today_pnl.get('today_pnl_percent', 0.0),
        "positions_count": portfolio_calc.get('positions_count', 0),
        "cash_balance": 0.0,  # TODO: Implement cash balance tracking
        "positions_detail": portfolio_calc.get('positions_detail', [])
    }


@router.get("/portfolios", response_model=List[PortfolioResponse])
def get_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's portfolios"""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    return portfolios


@router.post("/portfolios", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new portfolio"""
    db_portfolio = Portfolio(
        user_id=current_user.id,
        name=portfolio.name
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's transactions"""
    # Get all user's portfolios
    portfolio_ids = [p.id for p in db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()]
    
    transactions = (
        db.query(Transaction)
        .filter(Transaction.portfolio_id.in_(portfolio_ids))
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return transactions