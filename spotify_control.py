from flask import jsonify
import requests
import json
import os
from datetime import datetime, timedelta

SPOTIFY_CLIENT_ID     = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI  = os.getenv('SPOTIFY_REDIRECT_URI')
TOKEN_CACHE_FILE      = '.spotify_token_cache.json'  # ← En .gitignore

def load_token_cache():
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_token_cache(cache):
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def refresh_access_token(refresh_token):
    """Renueva el access token usando refresh token"""
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        cache = load_token_cache()
        cache['access_token'] = data['access_token']
        cache['expires_at'] = (datetime.now() + timedelta(seconds=data['expires_in'])).isoformat()
        save_token_cache(cache)
        return data['access_token']
    return None

def get_valid_access_token():
    """Obtiene un access token válido (refresca si es necesario)"""
    cache = load_token_cache()
    if not cache.get('refresh_token'):
        return None  # ← Necesitas OAuth flow inicial
    
    if cache.get('expires_at'):
        if datetime.fromisoformat(cache['expires_at']) > datetime.now():
            return cache['access_token']
    
    return refresh_access_token(cache['refresh_token'])

# Rutas Flask
from flask import Blueprint
spotify_bp = Blueprint('spotify', __name__, url_prefix='/api/spotify')

@spotify_bp.route('/now-playing', methods=['GET'])
def now_playing():
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    
    resp = requests.get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if resp.status_code == 204:  # No playback
        return jsonify(None), 200
    
    if resp.status_code == 200:
        return jsonify(resp.json()), 200
    
    return jsonify({'error': 'API Error'}), resp.status_code

@spotify_bp.route('/pause', methods=['POST'])
def pause():
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    
    resp = requests.put(
        'https://api.spotify.com/v1/me/player/pause',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify({'ok': resp.status_code < 400}), resp.status_code

@spotify_bp.route('/play', methods=['POST'])
def play():
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    
    resp = requests.put(
        'https://api.spotify.com/v1/me/player/play',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify({'ok': resp.status_code < 400}), resp.status_code

@spotify_bp.route('/next', methods=['POST'])
def next_track():
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    
    resp = requests.post(
        'https://api.spotify.com/v1/me/player/next',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify({'ok': resp.status_code < 400}), resp.status_code

@spotify_bp.route('/prev', methods=['POST'])
def prev_track():
    token = get_valid_access_token()
    if not token:
        return jsonify({'error': 'No token'}), 401
    
    resp = requests.post(
        'https://api.spotify.com/v1/me/player/previous',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify({'ok': resp.status_code < 400}), resp.status_code