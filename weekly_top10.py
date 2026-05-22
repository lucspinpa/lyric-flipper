#!/usr/bin/env python3
"""
weekly_top10.py
────────────────────────────────────────────────────────────────
Cada domingo envía tu top 10 de la semana via ntfy al iPhone.
────────────────────────────────────────────────────────────────
"""

import os
import logging
import requests
from spotipy.oauth2 import SpotifyOAuth
import spotipy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("weekly_top10")

CONFIG = {
    "SPOTIFY_CLIENT_ID":     os.getenv("SPOTIFY_CLIENT_ID"),
    "SPOTIFY_CLIENT_SECRET": os.getenv("SPOTIFY_CLIENT_SECRET"),
    "SPOTIFY_REDIRECT_URI":  os.getenv("SPOTIFY_REDIRECT_URI"),
    "NTFY_TOPIC":            os.getenv("NTFY_TOPIC"),
}

def get_top10():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CONFIG["SPOTIFY_CLIENT_ID"],
        client_secret=CONFIG["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=CONFIG["SPOTIFY_REDIRECT_URI"],
        scope="user-top-read",
        cache_path=".spotify_token_cache",
        open_browser=False,
    ))

    result = sp.current_user_top_tracks(limit=10, time_range="short_term")
    tracks = []
    for i, item in enumerate(result["items"], 1):
        tracks.append(f"{i}. {item['artists'][0]['name']} — {item['name']}")
    return tracks

def send_ntfy(title, body):
    topic = CONFIG["NTFY_TOPIC"]
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=body.encode("utf-8"),
        headers={
            "Title":    title.encode("utf-8"),
            "Priority": "default",
            "Tags":     "chart_with_upwards_trend",
        },
        timeout=8,
    )
    log.info("Notificacion enviada.")

def run():
    log.info("Obteniendo top 10 semanal...")
    tracks = get_top10()
    body = "\n".join(tracks)
    log.info("\n%s", body)
    send_ntfy("Tu top 10 de la semana", body)
    log.info("Listo.")

if __name__ == "__main__":
    run()
