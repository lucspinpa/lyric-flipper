#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pinterest Scraper for Lyric sh0p1t
Extrae tableros públicos de Pinterest y genera JSON para la web
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
except ImportError:
    print("❌ Dependencias faltantes. Instala con:")
    print("pip install requests beautifulsoup4")
    sys.exit(1)


class PinterestScraper:
    def __init__(self, username):
        self.username = username
        self.base_url = f"https://pinterest.com/{username}"
        self.boards = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_boards(self):
        """Raspa los tableros públicos del perfil"""
        print(f"🔍 Buscando tableros para: {self.username}")
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Para un scraping más robusto, Pinterest usa API internamente
            # Este es un enfoque alternativo más simple
            self._parse_html(response.text)
            
        except requests.RequestException as e:
            print(f"❌ Error fetching {self.base_url}: {e}")
            return False
        
        return True

    def _parse_html(self, html):
        """Parsea el HTML para extraer info de tableros"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Pinterest carga datos en el HTML como JSON
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'hasPart' in data:
                    for part in data['hasPart']:
                        board = self._extract_board_info(part)
                        if board:
                            self.boards.append(board)
            except (json.JSONDecodeError, KeyError):
                continue

    def _extract_board_info(self, data):
        """Extrae información de un tablero"""
        try:
            return {
                'id': data.get('url', '').split('/')[-1].lower(),
                'name': data.get('name', 'Sin nombre'),
                'description': data.get('description', ''),
                'image_url': data.get('image', ''),
                'pin_count': int(data.get('numberOfItems', 0)),
                'collaborators_count': 1,
                'is_owner': True,
                'url': data.get('url', '')
            }
        except (KeyError, ValueError):
            return None

    def fetch_boards_api(self):
        """
        Alternativa: Usar la API REST de Pinterest
        Requiere access_token obtenido en https://developers.pinterest.com
        """
        access_token = self._get_access_token()
        if not access_token:
            print("⚠️  Sin access_token. Usando método alternativo...")
            return self.fetch_boards()

        print("🔐 Usando Pinterest API")
        
        api_url = "https://api.pinterest.com/v1/me/boards"
        params = {
            'access_token': access_token,
            'fields': 'id,name,description,image,counts,created_at'
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.boards = self._process_api_response(data)
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error con API: {e}")
            return False

    def _process_api_response(self, data):
        """Procesa respuesta de la API de Pinterest"""
        boards = []
        
        for board in data.get('data', []):
            processed = {
                'id': board.get('id', ''),
                'name': board.get('name', 'Sin nombre'),
                'description': board.get('description', ''),
                'image_url': board.get('image', {}).get('original', {}).get('url', ''),
                'pin_count': board.get('counts', {}).get('pins', 0),
                'collaborators_count': board.get('counts', {}).get('collaborators', 1),
                'is_owner': True,
                'url': f"https://pinterest.com/{self.username}/{board.get('url', '')}"
            }
            boards.append(processed)
        
        return boards

    def _get_access_token(self):
        """Lee access_token del archivo .env o variables de entorno"""
        import os
        
        # Buscar en .env
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith('PINTEREST_TOKEN='):
                        return line.split('=')[1].strip()
        
        # Buscar en variables de entorno
        return os.getenv('PINTEREST_TOKEN')

    def save_to_json(self, output_file='pinterest_data.json'):
        """Guarda los tableros en JSON"""
        if not self.boards:
            print("⚠️  No se encontraron tableros")
            return False
        
        output_path = Path(output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.boards, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {len(self.boards)} tableros guardados en {output_file}")
            return True
            
        except IOError as e:
            print(f"❌ Error escribiendo archivo: {e}")
            return False

    def print_summary(self):
        """Imprime resumen de tableros encontrados"""
        if not self.boards:
            print("❌ Sin tableros para mostrar")
            return
        
        print(f"\n📌 RESUMEN ({len(self.boards)} tableros):")
        print("=" * 60)
        
        for i, board in enumerate(self.boards, 1):
            print(f"\n{i}. {board['name']}")
            print(f"   ID: {board['id']}")
            print(f"   Pins: {board['pin_count']}")
            if board['description']:
                print(f"   Desc: {board['description'][:50]}...")
        
        print("\n" + "=" * 60)


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python pinterest_scraper.py <username> [output.json]")
        print("\nEjemplo: python pinterest_scraper.py lucspinpa")
        sys.exit(1)
    
    username = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'pinterest_data.json'
    
    print(f"\n🎨 Pinterest Scraper para Lyric sh0p1t")
    print(f"👤 Usuario: {username}")
    print(f"💾 Salida: {output_file}\n")
    
    scraper = PinterestScraper(username)
    
    # Intentar primero con scraping, luego con API
    if not scraper.fetch_boards():
        if not scraper.fetch_boards_api():
            print("❌ No se pudieron obtener los tableros")
            sys.exit(1)
    
    if scraper.save_to_json(output_file):
        scraper.print_summary()
        print("\n✨ Listo para usar en tu web!")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
