from flask import Flask, jsonify, redirect, request
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
TOKEN_CACHE_FILE = '.spotify_token_cache.json'

# ═══════════════════════════════════════════════════════════════════════════
# TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def load_token_cache():
    """Carga el token cacheado del archivo"""
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_token_cache(data):
    """Guarda el token cacheado"""
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def refresh_access_token(refresh_token):
    """Renueva el access token usando refresh token"""
    try:
        resp = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': SPOTIFY_CLIENT_ID,
                'client_secret': SPOTIFY_CLIENT_SECRET,
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            cache = load_token_cache()
            cache['access_token'] = data['access_token']
            cache['expires_at'] = (datetime.now() + timedelta(seconds=data['expires_in'])).isoformat()
            save_token_cache(cache)
            return data['access_token']
    except Exception as e:
        print(f'Error refreshing token: {e}')
    return None

def get_valid_access_token():
    """Obtiene un access token válido (refresca si es necesario)"""
    cache = load_token_cache()
    
    if not cache.get('refresh_token'):
        return None  # No hay refresh token, necesita OAuth inicial
    
    # Si el token existe y no ha expirado, úsalo
    if cache.get('access_token') and cache.get('expires_at'):
        try:
            if datetime.fromisoformat(cache['expires_at']) > datetime.now():
                return cache['access_token']
        except:
            pass
    
    # Token expirado, refrescar
    return refresh_access_token(cache['refresh_token'])

# ═══════════════════════════════════════════════════════════════════════════
# SPOTIFY OAUTH
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/spotify/auth')
def spotify_auth():
    """Redirige a Spotify para autenticarse (solo primera vez)"""
    print('🎯 DEBUG: spotify_auth() was called!')
    scope = 'user-read-currently-playing user-modify-playback-state'
    return redirect(
        f'https://accounts.spotify.com/authorize?'
        f'client_id={SPOTIFY_CLIENT_ID}&'
        f'response_type=code&'
        f'redirect_uri={quote(SPOTIFY_REDIRECT_URI)}&'
        f'scope={quote(scope)}&'
        f'show_dialog=true'
    )

@app.route('/spotify/callback')
def spotify_callback():
    """Maneja el callback de Spotify y cachea el token"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f'Error en Spotify: {error}', 400
    
    if not code:
        return 'No authorization code received', 400
    
    try:
        resp = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': SPOTIFY_REDIRECT_URI,
                'client_id': SPOTIFY_CLIENT_ID,
                'client_secret': SPOTIFY_CLIENT_SECRET,
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            cache = {
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
                'expires_at': (datetime.now() + timedelta(seconds=data['expires_in'])).isoformat(),
            }
            save_token_cache(cache)
            return '''
            <h1>✓ Autorización completada</h1>
            <p>Tu refresh token ha sido guardado.</p>
            <p>Ahora puedes volver a <a href="/">tu dashboard</a></p>
            '''
        else:
            return f'Error al obtener token: {resp.status_code}', 400
    
    except Exception as e:
        return f'Error: {str(e)}', 500

# ═══════════════════════════════════════════════════════════════════════════
# SPOTIFY API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/spotify/now-playing')
def now_playing():
    """Obtiene la canción que está sonando ahora"""
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No authorized'}), 401
    
    try:
        resp = requests.get(
            'https://api.spotify.com/v1/me/player/currently-playing',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if resp.status_code == 204:  # No hay reproducción
            return jsonify(None), 200
        
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
        
        return jsonify({'error': f'Spotify API error: {resp.status_code}'}), resp.status_code
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/play', methods=['POST'])
def play():
    """Reanuda la reproducción"""
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No authorized'}), 401
    
    try:
        resp = requests.put(
            'https://api.spotify.com/v1/me/player/play',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify({'ok': resp.status_code < 400}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/pause', methods=['POST'])
def pause():
    """Pausa la reproducción"""
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No authorized'}), 401
    
    try:
        resp = requests.put(
            'https://api.spotify.com/v1/me/player/pause',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify({'ok': resp.status_code < 400}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/next', methods=['POST'])
def next_track():
    """Siguiente canción"""
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No authorized'}), 401
    
    try:
        resp = requests.post(
            'https://api.spotify.com/v1/me/player/next',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify({'ok': resp.status_code < 400}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/prev', methods=['POST'])
def prev_track():
    """Canción anterior"""
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No authorized'}), 401
    
    try:
        resp = requests.post(
            'https://api.spotify.com/v1/me/player/previous',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify({'ok': resp.status_code < 400}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# STATIC FILES (tu HTML/CSS)
# ═══════════════════════════════════════════════════════════════════════════

from flask import send_file, send_from_directory
import os

@app.route('/')
def index():
    return send_file('index.html', mimetype='text/html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Sirve archivos estáticos, pero NO rutas de API/OAuth"""
    # 🛡️ Protege tus rutas de API/OAuth
    if filename.startswith('api/') or filename.startswith('spotify/'):
        return 'Not found', 404
    
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        return f'File not found: {filename}', 404

if __name__ == '__main__':
    print('🚀 Flask running on http://localhost:5001')
    print('📍 First time? Visit: http://localhost:5001/spotify/auth')
    app.run(debug=True, port=5001)