#!/usr/bin/env python3
"""
Serveur simple pour test réseau direct
"""
import http.server
import socketserver
import socket

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trading ETF - Test Réseau</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 50px; background: #f0f8ff; }}
                    .container {{ max-width: 600px; margin: 0 auto; text-align: center; }}
                    .success {{ color: #28a745; font-size: 24px; }}
                    .info {{ background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    .button {{ background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✅ Connexion réseau réussie !</h1>
                    <div class="info">
                        <h2>🌐 Trading ETF App</h2>
                        <p>Vous accédez depuis : <strong>{self.client_address[0]}</strong></p>
                        <p>Serveur : <strong>{socket.gethostname()}</strong></p>
                    </div>
                    
                    <h3>🚀 Applications disponibles :</h3>
                    <a href="http://172.17.232.143:3000" class="button">📱 Frontend React</a>
                    <a href="http://172.17.232.143:8000/docs" class="button">📚 API Documentation</a>
                    <a href="http://172.17.232.143:8000/health" class="button">💚 Health Check</a>
                    
                    <div class="info">
                        <h4>📋 Instructions :</h4>
                        <p>Si ces liens fonctionnent depuis votre appareil, le réseau est configuré correctement !</p>
                        <p>Sinon, il faut configurer le port forwarding Windows.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            super().do_GET()

def get_all_ips():
    """Get all available IP addresses"""
    hostname = socket.gethostname()
    ips = []
    try:
        # Get all IP addresses for this host
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ':' not in ip and ip != '127.0.0.1':  # IPv4 only, exclude localhost
                ips.append(ip)
    except:
        pass
    return list(set(ips))

if __name__ == "__main__":
    PORT = 9999
    
    print("🌐 Trading ETF - Test de connectivité réseau")
    print("=" * 60)
    
    # Get all available IPs
    all_ips = get_all_ips()
    
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), SimpleHandler) as httpd:
            print(f"✅ Serveur de test démarré sur le port {PORT}")
            print("")
            print("📱 Testez depuis vos appareils :")
            print(f"   http://localhost:{PORT}")
            
            for ip in all_ips:
                print(f"   http://{ip}:{PORT}")
            
            print("")
            print("🔍 Si ça fonctionne, votre réseau est OK !")
            print("   Sinon, il faut configurer Windows port forwarding")
            print("")
            print("⏹️  Ctrl+C pour arrêter")
            print("=" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")