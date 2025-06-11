"""
Middleware de sécurité pour la production
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import Callable
import time
import logging
from collections import defaultdict, deque
import ipaddress

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de sécurité pour la production"""
    
    def __init__(self, app, settings):
        super().__init__(app)
        self.settings = settings
        self.rate_limiter = defaultdict(lambda: deque())
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Rate Limiting par IP
        client_ip = self._get_client_ip(request)
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # 2. Validation des headers de sécurité
        if not self._validate_security_headers(request):
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request headers"}
            )
        
        # 3. Traitement de la requête
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Erreur dans la requête: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # 4. Ajout des headers de sécurité à la réponse
        response = self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Récupère l'IP client en tenant compte des proxies"""
        # En production, utiliser X-Forwarded-For si derrière un proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Prendre la première IP (client original)
            return forwarded_for.split(",")[0].strip()
        
        # Fallback sur l'IP directe
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Vérifie si l'IP est rate limitée"""
        now = time.time()
        window_start = now - self.settings.RATE_LIMIT_WINDOW
        
        # Nettoyer les anciennes entrées
        client_requests = self.rate_limiter[client_ip]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Vérifier la limite
        if len(client_requests) >= self.settings.RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit dépassé pour IP: {client_ip}")
            return True
        
        # Ajouter la requête actuelle
        client_requests.append(now)
        return False
    
    def _validate_security_headers(self, request: Request) -> bool:
        """Valide les headers de sécurité"""
        # Vérifier User-Agent (bloquer les bots malveillants)
        user_agent = request.headers.get("User-Agent", "")
        suspicious_agents = ["bot", "crawler", "spider", "scan"]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            # En production, vous pourriez vouloir bloquer certains bots
            logger.info(f"Requête de bot détectée: {user_agent}")
        
        # Vérifier Host header (protection contre Host Header Injection)
        host = request.headers.get("Host", "")
        if self.settings.ALLOWED_HOSTS and host not in self.settings.ALLOWED_HOSTS:
            logger.warning(f"Host non autorisé: {host}")
            return False
        
        return True
    
    def _add_security_headers(self, response: Response) -> Response:
        """Ajoute les headers de sécurité à la réponse"""
        security_headers = {
            # Protection contre le clickjacking
            "X-Frame-Options": "DENY",
            
            # Protection contre le sniffing de type MIME
            "X-Content-Type-Options": "nosniff",
            
            # Protection XSS
            "X-XSS-Protection": "1; mode=block",
            
            # Politique de sécurité du contenu (ajuster selon vos besoins)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:; "
                "font-src 'self'; "
                "frame-ancestors 'none';"
            ),
            
            # Strict Transport Security (HTTPS)
            "Strict-Transport-Security": f"max-age={self.settings.SECURE_HSTS_SECONDS}; includeSubDomains; preload",
            
            # Référer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Politique de permissions
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )
        }
        
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware pour whitelist d'IPs (optionnel pour admin)"""
    
    def __init__(self, app, allowed_ips: list = None):
        super().__init__(app)
        self.allowed_networks = []
        
        if allowed_ips:
            for ip in allowed_ips:
                try:
                    self.allowed_networks.append(ipaddress.ip_network(ip, strict=False))
                except ValueError:
                    logger.error(f"IP invalide dans la whitelist: {ip}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.allowed_networks:
            # Pas de restriction si pas de whitelist configurée
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            client_addr = ipaddress.ip_address(client_ip)
            if not any(client_addr in network for network in self.allowed_networks):
                logger.warning(f"Accès refusé pour IP non autorisée: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
        except ValueError:
            logger.error(f"IP invalide: {client_ip}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid client IP"}
            )
        
        return await call_next(request)