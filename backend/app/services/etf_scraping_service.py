"""
Service de scraping pour les données ETF temps réel
Sources : JustETF, Morningstar, et autres sites fiables
"""

import asyncio
import aiohttp
import logging
import re
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.etf import ETF, MarketData
from app.services.multi_source_etf_data import ETFDataPoint, DataSource

logger = logging.getLogger(__name__)

@dataclass
class ScrapedETFData:
    """Données ETF scrapées"""
    isin: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: Optional[int]
    currency: str
    exchange: str
    last_update: datetime
    source: str
    nav: Optional[float] = None

class ETFScrapingService:
    """Service de scraping pour les données ETF temps réel"""
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 2  # Délai entre les requêtes (respectueux)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = 15
        
        # URLs de base pour les différentes sources
        self.base_urls = {
            'justetf': 'https://www.justetf.com',
            'morningstar': 'https://www.morningstar.fr',
            'boursorama': 'https://www.boursorama.com',
        }
    
    async def get_session(self):
        """Récupère une session HTTP avec les bons headers"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=10)
            )
        return self.session
    
    async def scrape_justetf_etf(self, isin: str) -> Optional[ScrapedETFData]:
        """Scrape les données d'un ETF depuis JustETF"""
        try:
            session = await self.get_session()
            
            # URL directe vers l'ETF JustETF (plus fiable)
            etf_url = f"https://www.justetf.com/en/etf-profile.html?isin={isin}"
            
            async with session.get(etf_url) as response:
                if response.status != 200:
                    logger.warning(f"JustETF: Status {response.status} pour {isin}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Debug: sauvegarder le HTML pour voir la structure
                # logger.debug(f"JustETF HTML snippet: {html[:500]}")
                
                # Essayer différents sélecteurs pour le prix
                price_element = None
                price_selectors = [
                    'span.val',
                    'span.price',
                    '.val',
                    '.price-big',
                    '[data-field="price"]',
                    '.intraday-price',
                    '.quote-value'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        logger.debug(f"JustETF: Prix trouvé avec sélecteur {selector}")
                        break
                
                if not price_element:
                    # Chercher dans tout le texte une structure de prix
                    text = soup.get_text()
                    price_pattern = r'([\d,]+\.\d{2})\s*EUR'
                    price_match = re.search(price_pattern, text)
                    if price_match:
                        current_price = float(price_match.group(1).replace(',', ''))
                        logger.debug(f"JustETF: Prix extrait du texte: {current_price}")
                    else:
                        logger.warning(f"JustETF: Aucun prix trouvé pour {isin}")
                        return None
                else:
                    # Extraire le prix de l'élément trouvé
                    price_text = price_element.get_text().strip()
                    price_match = re.search(r'([\d,]+\.\d{2})', price_text.replace(',', ''))
                    
                    if not price_match:
                        logger.warning(f"JustETF: Format prix invalide pour {isin}: {price_text}")
                        return None
                    
                    current_price = float(price_match.group(1))
                
                # Chercher la devise
                currency_element = soup.find('span', class_='currency')
                currency = currency_element.get_text().strip() if currency_element else 'EUR'
                
                # Chercher la variation
                change_element = soup.find('span', class_='change')
                change = 0.0
                change_percent = 0.0
                
                if change_element:
                    change_text = change_element.get_text().strip()
                    # Format : "+1.23 (+0.45%)" ou "-1.23 (-0.45%)"
                    change_match = re.search(r'([+-]?[\d,]+\.\d{2})', change_text.replace(',', ''))
                    percent_match = re.search(r'([+-]?[\d,]+\.\d{2})%', change_text.replace(',', ''))
                    
                    if change_match:
                        change = float(change_match.group(1))
                    if percent_match:
                        change_percent = float(percent_match.group(1))
                
                # Chercher le nom de l'ETF
                name_element = soup.find('h1') or soup.find('title')
                name = name_element.get_text().strip() if name_element else f"ETF {isin}"
                
                # Nettoyage du nom
                if " | justETF" in name:
                    name = name.split(" | justETF")[0]
                
                return ScrapedETFData(
                    isin=isin,
                    name=name,
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=None,  # JustETF ne fournit pas toujours le volume
                    currency=currency,
                    exchange="European Exchanges",
                    last_update=datetime.now(),
                    source="justetf_scraping"
                )
                
        except Exception as e:
            logger.error(f"Erreur JustETF scraping pour {isin}: {e}")
            return None
        
        finally:
            # Rate limiting respectueux
            await asyncio.sleep(self.rate_limit_delay)
    
    async def scrape_boursorama_etf(self, isin: str) -> Optional[ScrapedETFData]:
        """Scrape les données d'un ETF depuis Boursorama"""
        try:
            session = await self.get_session()
            
            # URL de recherche Boursorama
            search_url = f"https://www.boursorama.com/cours/{isin}/"
            
            async with session.get(search_url) as response:
                if response.status != 200:
                    logger.warning(f"Boursorama: Status {response.status} pour {isin}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Chercher le prix principal
                price_element = soup.find('span', class_='c-faceplate__price-value')
                if not price_element:
                    price_element = soup.find('span', class_='c-instrument c-instrument--last')
                
                if not price_element:
                    logger.warning(f"Boursorama: Prix non trouvé pour {isin}")
                    return None
                
                # Extraire le prix
                price_text = price_element.get_text().strip()
                price_match = re.search(r'([\d\s]+,\d{2})', price_text)
                
                if not price_match:
                    logger.warning(f"Boursorama: Format prix invalide pour {isin}: {price_text}")
                    return None
                
                current_price = float(price_match.group(1).replace(' ', '').replace(',', '.'))
                
                # Chercher la variation
                change_element = soup.find('span', class_='c-instrument c-instrument--variation')
                change = 0.0
                change_percent = 0.0
                
                if change_element:
                    change_text = change_element.get_text().strip()
                    change_match = re.search(r'([+-]?[\d\s]+,\d{2})', change_text)
                    if change_match:
                        change = float(change_match.group(1).replace(' ', '').replace(',', '.'))
                
                # Chercher le pourcentage
                percent_element = soup.find('span', class_='c-instrument c-instrument--percent')
                if percent_element:
                    percent_text = percent_element.get_text().strip()
                    percent_match = re.search(r'([+-]?[\d\s]+,\d{2})', percent_text)
                    if percent_match:
                        change_percent = float(percent_match.group(1).replace(' ', '').replace(',', '.'))
                
                # Nom de l'ETF
                name_element = soup.find('h1', class_='c-faceplate__company-name')
                name = name_element.get_text().strip() if name_element else f"ETF {isin}"
                
                return ScrapedETFData(
                    isin=isin,
                    name=name,
                    current_price=current_price,
                    change=change,
                    change_percent=change_percent,
                    volume=None,
                    currency="EUR",  # Boursorama affiche principalement en EUR
                    exchange="European Exchanges",
                    last_update=datetime.now(),
                    source="boursorama_scraping"
                )
                
        except Exception as e:
            logger.error(f"Erreur Boursorama scraping pour {isin}: {e}")
            return None
        
        finally:
            await asyncio.sleep(self.rate_limit_delay)
    
    async def scrape_yahoo_finance_direct(self, isin: str) -> Optional[ScrapedETFData]:
        """Scrape direct depuis Yahoo Finance (plus simple et fiable)"""
        try:
            session = await self.get_session()
            
            # Essayer avec différents symboles Yahoo selon l'ISIN
            yahoo_symbols = []
            if isin == "IE00B5BMR087":  # iShares Core S&P 500
                yahoo_symbols = ["CSPX.AS", "CSPX.L", "CSPX.PA"]
            elif isin == "IE00B4L5Y983":  # iShares Core MSCI World
                yahoo_symbols = ["IWDA.AS", "IWDA.L"]
            elif isin == "IE00BK5BQT80":  # Vanguard FTSE All-World
                yahoo_symbols = ["VWRL.AS", "VWRL.L"]
            
            for symbol in yahoo_symbols:
                try:
                    url = f"https://finance.yahoo.com/quote/{symbol}"
                    
                    async with session.get(url) as response:
                        if response.status != 200:
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Chercher le prix principal
                        price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
                        if not price_element:
                            price_element = soup.find('span', class_='Trsdu(0.3s)')
                        
                        if price_element:
                            price_text = price_element.get_text().strip()
                            price_match = re.search(r'([\d,]+\.\d{2})', price_text.replace(',', ''))
                            
                            if price_match:
                                current_price = float(price_match.group(1))
                                
                                # Chercher la variation
                                change_element = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})
                                change = 0.0
                                if change_element:
                                    change_text = change_element.get_text().strip()
                                    change_match = re.search(r'([+-]?[\d,]+\.\d{2})', change_text.replace(',', ''))
                                    if change_match:
                                        change = float(change_match.group(1))
                                
                                # Chercher le pourcentage
                                percent_element = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
                                change_percent = 0.0
                                if percent_element:
                                    percent_text = percent_element.get_text().strip()
                                    percent_match = re.search(r'([+-]?[\d,]+\.\d{2})', percent_text.replace(',', '').replace('%', ''))
                                    if percent_match:
                                        change_percent = float(percent_match.group(1))
                                
                                # Nom de l'ETF
                                name_element = soup.find('h1', class_='D(ib)')
                                name = name_element.get_text().strip() if name_element else f"ETF {symbol}"
                                
                                # Déterminer la devise selon le symbole
                                currency = "EUR" if ".AS" in symbol or ".PA" in symbol or ".DE" in symbol else "USD"
                                
                                return ScrapedETFData(
                                    isin=isin,
                                    name=name,
                                    current_price=current_price,
                                    change=change,
                                    change_percent=change_percent,
                                    volume=None,
                                    currency=currency,
                                    exchange="Yahoo Finance",
                                    last_update=datetime.now(),
                                    source="yahoo_scraping"
                                )
                        
                except Exception as e:
                    logger.warning(f"Erreur Yahoo {symbol}: {e}")
                    continue
            
            logger.warning(f"Yahoo Finance: Pas de données pour {isin}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur Yahoo Finance scraping pour {isin}: {e}")
            return None
        
        finally:
            await asyncio.sleep(self.rate_limit_delay)
    
    async def scrape_etf_data(self, isin: str) -> Optional[ScrapedETFData]:
        """Récupère les données d'un ETF en essayant plusieurs sources"""
        scrapers = [
            self.scrape_yahoo_finance_direct,  # Priorité 1: Yahoo Finance (le plus fiable)
            self.scrape_boursorama_etf,        # Priorité 2: Boursorama
            self.scrape_justetf_etf,           # Priorité 3: JustETF
        ]
        
        for scraper in scrapers:
            try:
                data = await scraper(isin)
                if data and data.current_price > 0:
                    logger.info(f"Données récupérées pour {isin} depuis {data.source}: {data.current_price} {data.currency}")
                    return data
            except Exception as e:
                logger.warning(f"Erreur scraper {scraper.__name__} pour {isin}: {e}")
                continue
        
        logger.warning(f"Aucune donnée trouvée pour {isin} via scraping")
        return None
    
    async def scrape_multiple_etfs(self, isins: List[str]) -> List[ScrapedETFData]:
        """Récupère les données de plusieurs ETFs"""
        tasks = []
        for isin in isins:
            tasks.append(self.scrape_etf_data(isin))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, ScrapedETFData):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur scraping pour {isins[i]}: {result}")
        
        logger.info(f"Scraping terminé: {len(valid_results)}/{len(isins)} ETFs récupérés")
        return valid_results
    
    async def save_to_database(self, scraped_data: List[ScrapedETFData]):
        """Sauvegarde les données scrapées en base de données"""
        db = SessionLocal()
        try:
            for data in scraped_data:
                # Créer une entrée dans market_data
                market_data = MarketData(
                    time=data.last_update,
                    etf_isin=data.isin,
                    open_price=None,  # Pas disponible via scraping
                    high_price=None,  # Pas disponible via scraping
                    low_price=None,   # Pas disponible via scraping
                    close_price=data.current_price,
                    volume=data.volume,
                    nav=data.nav
                )
                
                # Vérifier si on a déjà une entrée récente (dernière heure)
                existing = db.query(MarketData).filter(
                    MarketData.etf_isin == data.isin,
                    MarketData.time >= datetime.now() - timedelta(hours=1)
                ).order_by(MarketData.time.desc()).first()
                
                if not existing or (datetime.now() - existing.time).total_seconds() > 300:  # Plus de 5 minutes
                    db.add(market_data)
                    logger.debug(f"Données sauvegardées pour {data.isin}: {data.current_price} {data.currency}")
            
            db.commit()
            logger.info(f"Sauvegarde terminée pour {len(scraped_data)} ETFs")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde base de données: {e}")
            db.rollback()
        finally:
            db.close()
    
    def convert_to_etf_data_point(self, scraped_data: ScrapedETFData, etf_info: Dict) -> ETFDataPoint:
        """Convertit les données scrapées en ETFDataPoint"""
        return ETFDataPoint(
            symbol=f"SCRAPED_{scraped_data.isin}",
            isin=scraped_data.isin,
            name=scraped_data.name,
            current_price=scraped_data.current_price,
            change=scraped_data.change,
            change_percent=scraped_data.change_percent,
            volume=scraped_data.volume or 0,
            market_cap=None,
            currency=scraped_data.currency,
            exchange=scraped_data.exchange,
            sector=etf_info.get('sector', 'Unknown'),
            last_update=scraped_data.last_update,
            source=DataSource.CACHE if 'scraping' in scraped_data.source else DataSource.HYBRID,
            confidence_score=0.85  # Bonne confiance pour les données scrapées
        )
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()

# Instance globale
etf_scraping_service = None

def get_etf_scraping_service() -> ETFScrapingService:
    """Dependency injection pour FastAPI"""
    global etf_scraping_service
    if etf_scraping_service is None:
        etf_scraping_service = ETFScrapingService()
    return etf_scraping_service