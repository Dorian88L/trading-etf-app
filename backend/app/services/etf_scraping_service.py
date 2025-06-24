"""
Service de scraping pour les données ETF temps réel
Sources : JustETF, Morningstar, et autres sites fiables
"""

import asyncio
import aiohttp
import logging
import re
import random
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote, urljoin
from sqlalchemy.orm import Session
import hashlib
import base64
from fake_useragent import UserAgent

from app.core.database import SessionLocal
from app.models.etf import ETF, MarketData
from app.services.multi_source_etf_data import ETFDataPoint, DataSource

logger = logging.getLogger(__name__)

@dataclass
class ScrapedETFData:
    """Données ETF scrapées complètes"""
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
    
    # Données complètes ajoutées
    description: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    expense_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    pe_ratio: Optional[float] = None
    beta: Optional[float] = None
    
    # Données techniques
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    
    # Qualité des données
    confidence_score: float = 0.85
    data_source_url: Optional[str] = None

class ETFScrapingService:
    """Service de scraping avancé pour les données ETF temps réel"""
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 1.5  # Délai optimisé entre les requêtes
        self.ua = UserAgent()
        self.timeout = 20
        self.max_retries = 3
        
        # Rotation des User Agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # URLs de base étendues pour plus de sources
        self.base_urls = {
            'justetf': 'https://www.justetf.com',
            'morningstar': 'https://www.morningstar.fr',
            'boursorama': 'https://www.boursorama.com',
            'investing': 'https://fr.investing.com',
            'marketwatch': 'https://www.marketwatch.com',
            'tradingview': 'https://fr.tradingview.com',
            'euronext': 'https://live.euronext.com',
            'yahoo_fr': 'https://fr.finance.yahoo.com'
        }
        
        # Mapping ISIN vers symboles pour différentes sources
        self.isin_symbol_mapping = {
            "IE00B5BMR087": {  # iShares Core S&P 500
                "investing": "etfs/ishares-core-s-p-500-ucits-etf",
                "yahoo": "CSPX.AS",
                "marketwatch": "cspx",
                "euronext": "NL0011051055"
            },
            "IE00B4L5Y983": {  # iShares Core MSCI World
                "investing": "etfs/ishares-core-msci-world-ucits-etf",
                "yahoo": "IWDA.AS",
                "marketwatch": "iwda",
                "euronext": "NL0009989629"
            },
            "IE00BK5BQT80": {  # Vanguard FTSE All-World
                "investing": "etfs/vanguard-ftse-all-world-ucits-etf",
                "yahoo": "VWRL.AS",
                "marketwatch": "vwrl",
                "euronext": "NL0009690246"
            }
        }
        
        # Cache pour éviter les doublons
        self.cache = {}
        self.cache_ttl = 30  # 30 secondes de cache
    
    def _get_cache_key(self, isin: str, source: str) -> str:
        """Génère une clé de cache"""
        return f"{source}_{isin}_{int(time.time() // self.cache_ttl)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie si le cache est valide"""
        return cache_key in self.cache and (time.time() - self.cache[cache_key]['timestamp']) < self.cache_ttl
    
    async def get_session(self, rotate_ua=True):
        """Récupère une session HTTP avec rotation des User Agents"""
        if not self.session or rotate_ua:
            if self.session:
                await self.session.close()
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            user_agent = random.choice(self.user_agents) if rotate_ua else self.user_agents[0]
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/avif,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'DNT': '1'
            }
            
            # Connecteur avec plus d'options
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=connector
            )
        return self.session
    
    async def scrape_investing_com(self, isin: str) -> Optional[ScrapedETFData]:
        """Scrape les données depuis Investing.com (source prioritaire)"""
        cache_key = self._get_cache_key(isin, 'investing')
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit pour Investing.com {isin}")
            return self.cache[cache_key]['data']
        
        try:
            session = await self.get_session()
            symbol_data = self.isin_symbol_mapping.get(isin, {})
            investing_path = symbol_data.get('investing')
            
            if not investing_path:
                logger.warning(f"Investing.com: Pas de mapping pour {isin}")
                return None
            
            etf_url = f"https://fr.investing.com/{investing_path}"
            
            for attempt in range(self.max_retries):
                try:
                    async with session.get(etf_url) as response:
                        if response.status == 429:  # Rate limited
                            await asyncio.sleep(5 * (attempt + 1))
                            continue
                            
                        if response.status != 200:
                            logger.warning(f"Investing.com: Status {response.status} pour {isin}")
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extraire le prix principal
                        price_element = soup.find('span', {'data-test': 'instrument-price-last'})
                        if not price_element:
                            price_element = soup.find('span', class_='text-2xl')
                        
                        if not price_element:
                            logger.warning(f"Investing.com: Prix non trouvé pour {isin}")
                            continue
                        
                        # Nettoyer et extraire le prix
                        price_text = price_element.get_text().strip().replace(',', '')
                        price_match = re.search(r'([\d.]+)', price_text)
                        
                        if not price_match:
                            logger.warning(f"Investing.com: Format prix invalide pour {isin}: {price_text}")
                            continue
                        
                        current_price = float(price_match.group(1))
                        
                        # Extraire la variation
                        change_element = soup.find('span', {'data-test': 'instrument-price-change'})
                        change = 0.0
                        change_percent = 0.0
                        
                        if change_element:
                            change_text = change_element.get_text().strip()
                            # Format: "+1.23 (+0.45%)"
                            change_match = re.search(r'([+-]?[\d.]+)', change_text)
                            percent_match = re.search(r'\(([+-]?[\d.]+)%\)', change_text)
                            
                            if change_match:
                                change = float(change_match.group(1))
                            if percent_match:
                                change_percent = float(percent_match.group(1))
                        
                        # Extraire le nom
                        name_element = soup.find('h1', {'data-test': 'instrument-header-title'})
                        if not name_element:
                            name_element = soup.find('h1')
                        name = name_element.get_text().strip() if name_element else f"ETF {isin}"
                        
                        # Extraire le volume
                        volume = None
                        volume_element = soup.find('span', string=re.compile(r'Volume'))
                        if volume_element and volume_element.parent:
                            volume_text = volume_element.parent.get_text()
                            volume_match = re.search(r'([\d,]+)', volume_text.replace(' ', ''))
                            if volume_match:
                                volume = int(volume_match.group(1).replace(',', ''))
                        
                        # Extraire des données supplémentaires
                        market_cap = None
                        expense_ratio = None
                        
                        # Secteur depuis les catégories
                        sector = "Unknown"
                        sector_element = soup.find('span', string=re.compile(r'Secteur|Category'))
                        if sector_element and sector_element.parent:
                            sector = sector_element.parent.get_text().strip()
                        
                        result = ScrapedETFData(
                            isin=isin,
                            name=name,
                            current_price=current_price,
                            change=change,
                            change_percent=change_percent,
                            volume=volume,
                            currency="EUR",  # Investing.com affiche généralement en EUR pour les ETFs européens
                            exchange="European Exchanges",
                            last_update=datetime.now(),
                            source="investing_com_scraping",
                            sector=sector,
                            market_cap=market_cap,
                            expense_ratio=expense_ratio,
                            confidence_score=0.95,  # Très haute confiance pour Investing.com
                            data_source_url=etf_url
                        )
                        
                        # Mettre en cache
                        self.cache[cache_key] = {
                            'data': result,
                            'timestamp': time.time()
                        }
                        
                        return result
                        
                except Exception as e:
                    logger.warning(f"Investing.com: Tentative {attempt + 1} échouée pour {isin}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur Investing.com scraping pour {isin}: {e}")
            return None
        
        finally:
            await asyncio.sleep(self.rate_limit_delay)
    
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
        """Récupère les données d'un ETF en essayant plusieurs sources (priorité optimisée)"""
        scrapers = [
            self.scrape_investing_com,         # Priorité 1: Investing.com (excellent)
            self.scrape_yahoo_finance_direct,  # Priorité 2: Yahoo Finance (fiable)
            self.scrape_boursorama_etf,        # Priorité 3: Boursorama (bon)
            self.scrape_justetf_etf,           # Priorité 4: JustETF (détail)
        ]
        
        for scraper in scrapers:
            try:
                data = await scraper(isin)
                if data and data.current_price > 0:
                    logger.info(f"Données récupérées pour {isin} depuis {data.source}: {data.current_price} {data.currency} (confiance: {data.confidence_score:.2f})")
                    
                    # Sauvegarder automatiquement en base
                    await self.save_single_to_database(data)
                    
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
    
    async def save_single_to_database(self, data: ScrapedETFData):
        """Sauvegarde une donnée ETF unique en base (optimisé)"""
        db = SessionLocal()
        try:
            # Vérifier si on a déjà une entrée récente (dernières 2 minutes)
            existing = db.query(MarketData).filter(
                MarketData.etf_isin == data.isin,
                MarketData.time >= datetime.now() - timedelta(minutes=2)
            ).order_by(MarketData.time.desc()).first()
            
            if not existing:
                # Créer une nouvelle entrée
                market_data = MarketData(
                    time=data.last_update,
                    etf_isin=data.isin,
                    open_price=None,
                    high_price=data.day_high,
                    low_price=data.day_low,
                    close_price=data.current_price,
                    volume=data.volume,
                    nav=data.nav
                )
                
                db.add(market_data)
                db.commit()
                logger.debug(f"[{data.source}] Données sauvegardées pour {data.isin}: {data.current_price} {data.currency}")
            else:
                logger.debug(f"Données récentes déjà en cache pour {data.isin}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde individuelle pour {data.isin}: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def save_to_database(self, scraped_data: List[ScrapedETFData]):
        """Sauvegarde les données scrapées en base de données (batch)"""
        db = SessionLocal()
        try:
            saved_count = 0
            for data in scraped_data:
                # Vérifier si on a déjà une entrée récente (dernières 2 minutes)
                existing = db.query(MarketData).filter(
                    MarketData.etf_isin == data.isin,
                    MarketData.time >= datetime.now() - timedelta(minutes=2)
                ).order_by(MarketData.time.desc()).first()
                
                if not existing:
                    # Créer une entrée dans market_data avec toutes les données disponibles
                    market_data = MarketData(
                        time=data.last_update,
                        etf_isin=data.isin,
                        open_price=None,  # Pas toujours disponible via scraping
                        high_price=data.day_high,
                        low_price=data.day_low,
                        close_price=data.current_price,
                        volume=data.volume,
                        nav=data.nav
                    )
                    
                    db.add(market_data)
                    saved_count += 1
                    logger.debug(f"[{data.source}] Données préparées pour {data.isin}: {data.current_price} {data.currency}")
            
            if saved_count > 0:
                db.commit()
                logger.info(f"Sauvegarde batch terminée: {saved_count}/{len(scraped_data)} nouveaux enregistrements")
            else:
                logger.info(f"Aucune nouvelle donnée à sauvegarder (cache récent)")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde base de données batch: {e}")
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