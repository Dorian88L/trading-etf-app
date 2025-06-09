"""
Endpoints pour le système de scoring et ranking des ETF
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.etf_scoring import ETFScoringService
from app.schemas.etf import ETFScoreResponse, ETFRankingResponse

router = APIRouter()

@router.get("/score/{etf_isin}", response_model=ETFScoreResponse)
async def get_etf_score(
    etf_isin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calcule le score complet d'un ETF
    """
    try:
        scoring_service = ETFScoringService()
        score_data = await scoring_service.calculate_etf_score(etf_isin, db)
        
        if not score_data:
            raise HTTPException(
                status_code=404,
                detail=f"Impossible de calculer le score pour l'ETF {etf_isin}"
            )
        
        return ETFScoreResponse(**score_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ranking", response_model=List[ETFRankingResponse])
async def get_etf_ranking(
    limit: int = Query(10, ge=1, le=50, description="Nombre d'ETF à retourner"),
    sector: Optional[str] = Query(None, description="Filtrer par secteur"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Score minimum"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le classement des ETF par score
    """
    try:
        scoring_service = ETFScoringService()
        ranked_etfs = await scoring_service.get_top_etfs(
            limit=limit,
            sector=sector,
            db=db
        )
        
        # Filtrage par score minimum si spécifié
        if min_score is not None:
            ranked_etfs = [etf for etf in ranked_etfs if etf['final_score'] >= min_score]
        
        return [ETFRankingResponse(**etf) for etf in ranked_etfs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-performers", response_model=List[ETFRankingResponse])
async def get_top_performers(
    timeframe: str = Query("1M", description="Période: 1D, 1W, 1M, 3M"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les ETF avec les meilleures performances récentes
    """
    try:
        scoring_service = ETFScoringService()
        
        # Récupération de tous les ETF avec scores
        all_etfs = await scoring_service.get_top_etfs(limit=50, db=db)
        
        # Tri par score de momentum pour les top performers
        top_performers = sorted(
            all_etfs,
            key=lambda x: x['momentum_score'],
            reverse=True
        )[:limit]
        
        return [ETFRankingResponse(**etf) for etf in top_performers]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sector-analysis")
async def get_sector_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyse des secteurs avec scores moyens
    """
    try:
        scoring_service = ETFScoringService()
        
        # Liste des secteurs principaux
        sectors = ['Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer', 'Industrial']
        sector_analysis = {}
        
        for sector in sectors:
            etfs = await scoring_service.get_top_etfs(limit=10, sector=sector, db=db)
            if etfs:
                avg_score = sum(etf['final_score'] for etf in etfs) / len(etfs)
                avg_risk = sum(etf['risk_score'] for etf in etfs) / len(etfs)
                avg_momentum = sum(etf['momentum_score'] for etf in etfs) / len(etfs)
                
                sector_analysis[sector] = {
                    'average_score': round(avg_score, 2),
                    'average_risk_score': round(avg_risk, 2),
                    'average_momentum': round(avg_momentum, 2),
                    'etf_count': len(etfs),
                    'top_etf': etfs[0] if etfs else None
                }
        
        # Tri par score moyen décroissant
        sorted_sectors = dict(sorted(
            sector_analysis.items(),
            key=lambda x: x[1]['average_score'],
            reverse=True
        ))
        
        return {
            'status': 'success',
            'data': {
                'sector_analysis': sorted_sectors,
                'generated_at': scoring_service.technical_service.get_current_time(),
                'best_sector': list(sorted_sectors.keys())[0] if sorted_sectors else None,
                'market_summary': {
                    'total_sectors_analyzed': len(sorted_sectors),
                    'average_market_score': round(
                        sum(s['average_score'] for s in sorted_sectors.values()) / len(sorted_sectors), 2
                    ) if sorted_sectors else 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare")
async def compare_etfs(
    etf_isins: str = Query(..., description="ISINs séparés par des virgules"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare plusieurs ETF côte à côte
    """
    try:
        isin_list = [isin.strip() for isin in etf_isins.split(',')]
        if len(isin_list) > 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum 5 ETF peuvent être comparés simultanément"
            )
        
        scoring_service = ETFScoringService()
        comparison_data = []
        
        for isin in isin_list:
            score_data = await scoring_service.calculate_etf_score(isin, db)
            if score_data:
                comparison_data.append(score_data)
        
        if not comparison_data:
            raise HTTPException(
                status_code=404,
                detail="Aucun ETF trouvé pour les ISIN fournis"
            )
        
        # Analyse comparative
        best_overall = max(comparison_data, key=lambda x: x['final_score'])
        lowest_risk = max(comparison_data, key=lambda x: x['risk_score'])
        best_momentum = max(comparison_data, key=lambda x: x['momentum_score'])
        
        return {
            'status': 'success',
            'data': {
                'etfs': comparison_data,
                'analysis': {
                    'best_overall_score': best_overall['etf_isin'],
                    'lowest_risk': lowest_risk['etf_isin'],
                    'best_momentum': best_momentum['etf_isin'],
                    'score_range': {
                        'min': min(etf['final_score'] for etf in comparison_data),
                        'max': max(etf['final_score'] for etf in comparison_data),
                        'spread': max(etf['final_score'] for etf in comparison_data) - 
                                min(etf['final_score'] for etf in comparison_data)
                    }
                },
                'generated_at': scoring_service.technical_service.get_current_time()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screening")
async def screen_etfs(
    min_score: float = Query(70, ge=0, le=100, description="Score minimum"),
    max_risk: float = Query(50, ge=0, le=100, description="Risque maximum (score inverse)"),
    min_momentum: float = Query(60, ge=0, le=100, description="Momentum minimum"),
    sectors: Optional[str] = Query(None, description="Secteurs séparés par des virgules"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Screening avancé des ETF avec critères multiples
    """
    try:
        scoring_service = ETFScoringService()
        
        # Récupération d'un échantillon large d'ETF
        all_etfs = await scoring_service.get_top_etfs(limit=100, db=db)
        
        # Application des filtres
        filtered_etfs = []
        sector_list = [s.strip() for s in sectors.split(',')] if sectors else None
        
        for etf in all_etfs:
            # Filtres de score
            if etf['final_score'] < min_score:
                continue
            if (100 - etf['risk_score']) > max_risk:  # Inversion car risk_score élevé = faible risque
                continue
            if etf['momentum_score'] < min_momentum:
                continue
            
            # Filtre de secteur (nécessite les données ETF)
            # if sector_list and etf.get('sector') not in sector_list:
            #     continue
            
            filtered_etfs.append(etf)
        
        # Limitation des résultats
        filtered_etfs = filtered_etfs[:limit]
        
        return {
            'status': 'success',
            'data': {
                'etfs': filtered_etfs,
                'filters_applied': {
                    'min_score': min_score,
                    'max_risk': max_risk,
                    'min_momentum': min_momentum,
                    'sectors': sector_list
                },
                'results_count': len(filtered_etfs),
                'generated_at': scoring_service.technical_service.get_current_time()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))