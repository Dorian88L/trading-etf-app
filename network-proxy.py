#!/usr/bin/env python3
"""
Proxy simple pour rendre l'application accessible sur le réseau avec un nom personnalisé
"""
import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs
import json
import socket

class TradingETFProxy(http.server.BaseHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.frontend_url = "http://127.0.0.1:3000"
        self.backend_url = "http://127.0.0.1:8000"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def handle_request(self):
        try:
            # Déterminer vers quel service rediriger
            if self.path.startswith('/api/') or self.path.startswith('/docs') or self.path.startswith('/openapi'):
                target_url = self.backend_url + self.path
            else:
                # Tout le reste va au frontend
                target_url = self.frontend_url + self.path
            
            # Créer la requête
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                req = urllib.request.Request(target_url, data=post_data)
            else:
                req = urllib.request.Request(target_url)
            
            # Copier les headers
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host', 'connection']:
                    req.add_header(header_name, header_value)
            
            # Faire la requête
            with urllib.request.urlopen(req, timeout=30) as response:
                # Envoyer la réponse
                self.send_response(response.getcode())
                
                # Copier les headers de réponse
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header_name, header_value)
                
                # Headers CORS
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                self.end_headers()
                
                # Copier le contenu
                self.wfile.write(response.read())
                
        except urllib.error.URLError as e:
            # Service non disponible
            self.send_error(503, f"Service unavailable: {e}")
        except Exception as e:
            # Erreur générale
            self.send_error(500, f"Internal error: {e}")
    
    def log_message(self, format, *args):
        print(f"[PROXY] {self.address_string()} - {format % args}")

def get_local_ip():
    """Obtient l'IP locale"""
    try:
        # Se connecter à une adresse externe pour obtenir l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    PORT = 80
    local_ip = get_local_ip()
    
    print("🌐 Trading ETF Network Proxy")
    print("=" * 50)
    
    try:
        # Essayer le port 80 d'abord
        with socketserver.TCPServer(("0.0.0.0", PORT), TradingETFProxy) as httpd:
            print(f"✅ Proxy démarré sur le port {PORT}")
            print(f"📍 Accès local: http://localhost")
            print(f"🌐 Accès réseau: http://{local_ip}")
            print(f"📱 Depuis autres appareils: http://{local_ip}")
            print("")
            print("📋 Instructions pour les autres appareils:")
            print(f"   1. Connectez-vous au même WiFi")
            print(f"   2. Ouvrez: http://{local_ip}")
            print("")
            print("⏹️  Appuyez sur Ctrl+C pour arrêter")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except PermissionError:
        # Port 80 nécessite des privilèges, utiliser le port 8080
        PORT = 8080
        print(f"⚠️  Port 80 non accessible, utilisation du port {PORT}")
        
        with socketserver.TCPServer(("0.0.0.0", PORT), TradingETFProxy) as httpd:
            print(f"✅ Proxy démarré sur le port {PORT}")
            print(f"📍 Accès local: http://localhost:{PORT}")
            print(f"🌐 Accès réseau: http://{local_ip}:{PORT}")
            print(f"📱 Depuis autres appareils: http://{local_ip}:{PORT}")
            print("")
            print("📋 Instructions pour les autres appareils:")
            print(f"   1. Connectez-vous au même WiFi")
            print(f"   2. Ouvrez: http://{local_ip}:{PORT}")
            print("")
            print("⏹️  Appuyez sur Ctrl+C pour arrêter")
            print("=" * 50)
            
            httpd.serve_forever()
    
    except KeyboardInterrupt:
        print("\n🛑 Proxy arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")