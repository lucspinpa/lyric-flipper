#!/usr/bin/env python3
"""
lyric_flipper.py
────────────────────────────────────────────────────────────────
Flujo completo: Spotify top tracks → letras (LRCLIB / Genius) → Flipper Zero
Basado en el informe de arquitectura de extracción automatizada de letras.

Dependencias:
    pip install spotipy lyricsgenius requests pyserial

Configuración:
    Edita la sección CONFIG o usa variables de entorno.
────────────────────────────────────────────────────────────────
"""

import os
import re
import random
import logging
import time
import json
from pathlib import Path
from typing import Optional

# ─── DEPENDENCIAS OPCIONALES ──────────────────────────────────
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:
    spotipy = None

try:
    import lyricsgenius
except ImportError:
    lyricsgenius = None

try:
    import requests
except ImportError:
    raise SystemExit("❌  Instala 'requests':  pip install requests")

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ─── LOGGING ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lyric_flipper")

# ══════════════════════════════════════════════════════════════
#  SECCIÓN CONFIG — edita estos valores o usa variables de entorno
# ══════════════════════════════════════════════════════════════
CONFIG = {
    # ── Spotify (Authorization Code Flow) ──────────────────────
    "SPOTIFY_CLIENT_ID":     os.getenv("SPOTIFY_CLIENT_ID",     ""),
    "SPOTIFY_CLIENT_SECRET": os.getenv("SPOTIFY_CLIENT_SECRET", ""),
    "SPOTIFY_REDIRECT_URI":  os.getenv("SPOTIFY_REDIRECT_URI",  "http://127.0.0.1:8888/callback"),
    
    # Rango temporal: short_term | medium_term | long_term
    "SPOTIFY_TIME_RANGE":    os.getenv("SPOTIFY_TIME_RANGE",    "short_term"),
    # Cuántas pistas top traer (1-50)
    "SPOTIFY_TOP_LIMIT":     int(os.getenv("SPOTIFY_TOP_LIMIT", "30")),

    # ── Genius (opcional, fallback si LRCLIB falla) ─────────────
    "GENIUS_ACCESS_TOKEN":   os.getenv("GENIUS_ACCESS_TOKEN",   ""),

    # ── Flipper Zero serial ─────────────────────────────────────
    # Déjalo vacío para auto-detección
    "FLIPPER_PORT":          os.getenv("FLIPPER_PORT",          ""),
    "FLIPPER_BAUD":          int(os.getenv("FLIPPER_BAUD",       "115200")),
    # Ruta en la SD del Flipper donde se guardará el lyric
    "FLIPPER_DEST_PATH":     "/ext/apps_data/lyric_of_day.txt",

    # ── Comportamiento general ──────────────────────────────────
    # Líneas consecutivas por fragmento
    "LYRIC_CHUNK_SIZE":      int(os.getenv("LYRIC_CHUNK_SIZE",  "5")),
    # Archivo local para guardar el fragmento aunque no haya Flipper
    "LOCAL_OUTPUT_FILE":     "lyric_of_day.txt",

    # ── Ntfy (notificaciones iPhone) ────────────────────────────
    # Cambia esto por tu topic personal (invéntate uno difícil de adivinar)
    "NTFY_TOPIC":            os.getenv("NTFY_TOPIC", "lucspiLyricFlipper"),
}
# ══════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────
#  MÓDULO 1 — Spotify: obtener top tracks
# ─────────────────────────────────────────────────────────────

def get_top_tracks() -> list[dict]:
    """
    Devuelve lista de dicts con {track, artist, duration_s} usando
    Authorization Code Flow (scope: user-top-read).
    """
    if spotipy is None:
        raise SystemExit("❌  Instala 'spotipy':  pip install spotipy")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CONFIG["SPOTIFY_CLIENT_ID"],
        client_secret=CONFIG["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=CONFIG["SPOTIFY_REDIRECT_URI"],
        scope="user-top-read",
        cache_path=".spotify_token_cache",
        open_browser=True,
    ))

    log.info("🎵  Solicitando top %d pistas (%s)…",
             CONFIG["SPOTIFY_TOP_LIMIT"], CONFIG["SPOTIFY_TIME_RANGE"])

    result = sp.current_user_top_tracks(
        limit=CONFIG["SPOTIFY_TOP_LIMIT"],
        time_range=CONFIG["SPOTIFY_TIME_RANGE"],
    )

    tracks = []
    for item in result["items"]:
        tracks.append({
            "track":      item["name"],
            "artist":     item["artists"][0]["name"],
            "album":      item["album"]["name"],
            "duration_s": round(item["duration_ms"] / 1000),
        })

    log.info("✅  %d pistas obtenidas.", len(tracks))
    return tracks


# ─────────────────────────────────────────────────────────────
#  MÓDULO 2 — Proveedor A: LRCLIB (open source, sin token)
# ─────────────────────────────────────────────────────────────

def fetch_lyrics_lrclib(track: str, artist: str, album: str, duration_s: int) -> Optional[str]:
    """
    Intenta /api/get (firma exacta) → /api/search (difuso).
    """
    base = "https://lrclib.net"

    # Intento 1: firma exacta
    params = {
        "track_name":   track,
        "artist_name":  artist,
        "album_name":   album,
        "duration":     duration_s,
    }
    log.info('🔍  LRCLIB /api/get  "%s - %s"...', artist, track)
    try:
        r = requests.get(f"{base}/api/get", params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("instrumental"):
                log.info("🎸  Pista instrumental, sin letras.")
                return None
            text = data.get("plainLyrics") or data.get("syncedLyrics") or ""
            if text.strip():
                log.info("✅  Letra obtenida vía LRCLIB /api/get")
                return text
    except requests.RequestException as e:
        log.warning("⚠️   LRCLIB /api/get error: %s", e)

    # Intento 2: búsqueda difusa
    log.info("🔄  Probando LRCLIB /api/search…")
    try:
        r = requests.get(f"{base}/api/search",
                         params={"q": f"{track} {artist}"}, timeout=8)
        if r.status_code == 200:
            results = r.json()
            for item in results[:5]:
                if abs(item.get("duration", 0) - duration_s) <= 10:
                    text = item.get("plainLyrics", "")
                    if text.strip():
                        log.info("✅  Letra obtenida vía LRCLIB /api/search")
                        return text
    except requests.RequestException as e:
        log.warning("⚠️   LRCLIB /api/search error: %s", e)

    return None


# ─────────────────────────────────────────────────────────────
#  MÓDULO 2 — Proveedor B: Genius (fallback, requiere token)
# ─────────────────────────────────────────────────────────────

def fetch_lyrics_genius(track: str, artist: str) -> Optional[str]:
    if not CONFIG["GENIUS_ACCESS_TOKEN"]:
        log.info("ℹ️   Genius no configurado (sin token), saltando.")
        return None
    if lyricsgenius is None:
        log.warning("⚠️   lyricsgenius no instalado:  pip install lyricsgenius")
        return None

    log.info('🔍  Genius buscando "%s - %s"...', artist, track)
    try:
        genius = lyricsgenius.Genius(
            CONFIG["GENIUS_ACCESS_TOKEN"],
            remove_section_headers=True,
            skip_non_songs=True,
            timeout=10,
            verbose=False,
        )
        song = genius.search_song(track, artist)
        if song and song.lyrics:
            log.info("✅  Letra obtenida vía Genius.")
            return song.lyrics
    except Exception as e:
        log.warning("⚠️   Genius error: %s", e)
    return None


# ─────────────────────────────────────────────────────────────
#  MÓDULO 2 — Proveedor C: Lyrics.ovh (fallback terciario)
# ─────────────────────────────────────────────────────────────

def fetch_lyrics_ovh(track: str, artist: str) -> Optional[str]:
    url = f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist)}/{requests.utils.quote(track)}"
    log.info('🔍  Lyrics.ovh buscando "%s - %s"...', artist, track)
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("lyrics"):
                log.info("✅  Letra obtenida vía Lyrics.ovh.")
                return data["lyrics"]
    except requests.RequestException as e:
        log.warning("⚠️   Lyrics.ovh error: %s", e)
    return None


# ─────────────────────────────────────────────────────────────
#  MÓDULO 3 — NLP: limpieza + selección estocástica de fragmento
# ─────────────────────────────────────────────────────────────

def sanitize_lyrics(raw: str) -> list[str]:
    """
    Elimina etiquetas estructurales [Chorus], (Verse 1), etc.
    Retorna lista de líneas no vacías.
    """
    # Eliminar etiquetas entre corchetes y paréntesis
    clean = re.sub(r'[\[(\[].*?[\])\]]', '', raw)
    # Filtrar líneas vacías
    lines = [s.strip() for s in clean.splitlines() if s.strip()]
    return lines


def pick_lyric_chunk(lines: list[str], chunk_size: int = 5) -> str:
    """
    Selecciona un bloque de `chunk_size` líneas consecutivas.
    Usa shuffle de índices para garantizar variedad entre ejecuciones.
    """
    if len(lines) < chunk_size:
        return "\n".join(lines)

    # Generar todos los bloques posibles
    blocks = [lines[i:i + chunk_size] for i in range(len(lines) - chunk_size + 1)]
    random.shuffle(blocks)

    # Guardar el orden en un archivo de estado para no repetir
    state_file = Path(".lyric_state.json")
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            state = {}

    used = set(state.get("used_hashes", []))

    for block in blocks:
        block_text = "\n".join(block)
        h = str(hash(block_text))
        if h not in used:
            used.add(h)
            # Limpiar historial si se agotaron todos los bloques
            if len(used) >= len(blocks):
                used = {h}
            state["used_hashes"] = list(used)
            state_file.write_text(json.dumps(state))
            return block_text

    # Si todos usados, devolver primero
    return "\n".join(blocks[0])


# ─────────────────────────────────────────────────────────────
#  MÓDULO 4 — Flipper Zero: transferencia serial
# ─────────────────────────────────────────────────────────────

def detect_flipper_port() -> Optional[str]:
    """Auto-detecta el puerto serial del Flipper Zero."""
    if not SERIAL_AVAILABLE:
        return None
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        if "flipper" in desc or "flip_" in desc or "stlink" in desc:
            log.info("🔌  Flipper detectado en %s", port.device)
            return port.device
    return None


def send_to_flipper(text: str, dest_path: str) -> bool:
    """
    Escribe `text` en `dest_path` del Flipper via CLI serial.
    Retorna True si tuvo éxito.
    """
    if not SERIAL_AVAILABLE:
        log.warning("⚠️   pyserial no instalado:  pip install pyserial")
        return False

    port = CONFIG["FLIPPER_PORT"] or detect_flipper_port()
    if not port:
        log.warning("⚠️   No se encontró el Flipper Zero conectado.")
        return False

    try:
        with serial.Serial(port, CONFIG["FLIPPER_BAUD"], timeout=5) as ser:
            time.sleep(1)  # Esperar que el CLI inicialice

            # Limpiar buffer
            ser.read_all()

            # Crear / sobreescribir el archivo en la SD del Flipper
            # El CLI de Flipper usa: storage write <path>
            cmd_write = f"storage write {dest_path}\r\n"
            ser.write(cmd_write.encode())
            time.sleep(0.3)

            # Enviar contenido línea a línea
            for line in text.splitlines():
                ser.write((line + "\r\n").encode())
                time.sleep(0.05)

            # Señal de fin de escritura (Ctrl+C / EOF)
            ser.write(b"\x03")
            time.sleep(0.3)

            # Vibración háptica de confirmación
            ser.write(b"vibro 1\r\n")
            time.sleep(0.2)
            ser.write(b"vibro 0\r\n")
            time.sleep(0.2)

        log.info("✅  Lyric enviado al Flipper → %s", dest_path)
        return True

    except serial.SerialException as e:
        log.error("❌  Error serial con Flipper: %s", e)
        return False


# ─────────────────────────────────────────────────────────────
#  MÓDULO 5 — Ntfy: notificación al iPhone
# ─────────────────────────────────────────────────────────────

def send_ntfy(title: str, body: str) -> bool:
    """
    Envía una notificación push al iPhone via ntfy.sh.
    No requiere cuenta ni token — solo el topic.
    """
    topic = CONFIG.get("NTFY_TOPIC", "")
    if not topic:
        log.info("ℹ️   NTFY_TOPIC no configurado, saltando notificación.")
        return False

    try:
        r = requests.post(
            f"https://ntfy.sh/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title":    title.encode("utf-8"),
                "Priority": "default",
                "Tags":     "musical_note",
            },
            timeout=8,
        )
        if r.status_code == 200:
            log.info("📱  Notificación enviada a ntfy topic '%s'.", topic)
            return True
        else:
            log.warning("⚠️   Ntfy respondió con status %d.", r.status_code)
    except requests.RequestException as e:
        log.warning("⚠️   Error enviando a ntfy: %s", e)
    return False

# ─────────────────────────────────────────────────────────────
#  MÓDULO 7 — Generar stats.json + index.html para GitHub Pages
# ─────────────────────────────────────────────────────────────
 
def generate_stats(chunk: str, chosen_track: dict, top_tracks: list[dict]) -> None:
    """
    Escribe stats.json con el lyric del día y el top de canciones.
    La web (index.html) lee este archivo estático — sin auth ni backend.
    """
    from datetime import date
 
    data = {
        "generated": date.today().isoformat(),
        "lyric": {
            "artist": chosen_track["artist"],
            "track":  chosen_track["track"],
            "album":  chosen_track.get("album", ""),
            "chunk":  chunk,
        },
        "top_tracks": [
            {
                "track":  t["track"],
                "artist": t["artist"],
                "album":  t.get("album", ""),
            }
            for t in top_tracks[:10]
        ],
    }
 
    Path("stats.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("📊  stats.json generado.")

# ─────────────────────────────────────────────────────────────
#  PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────

def run_pipeline():
    log.info("═" * 50)
    log.info("  LYRIC FLIPPER — inicio del pipeline")
    log.info("═" * 50)

    # ── PASO 1: Top tracks de Spotify ──────────────────────────
    try:
        tracks = get_top_tracks()
        top_tracks_ordered = list(tracks)  # copia ordenada para la web
    except Exception as e:
        log.error("❌  No se pudo obtener top tracks: %s", e)
        return

    # ── PASO 2: Obtener letra (con cascada de proveedores) ──────
    lyrics_raw = None
    chosen_track = None

    # Mezclar el orden para que no sea siempre la #1
    random.shuffle(tracks)

    # Evitar repetir la canción del día anterior
    state_file = Path(".lyric_state.json")
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            state = {}
    last_track = state.get("last_track", "")

    # Si la primera candidata es la misma que ayer, moverla al final
    if tracks and f"{tracks[0]['artist']} - {tracks[0]['track']}" == last_track:
        tracks = tracks[1:] + tracks[:1]

    for track_info in tracks:
        t = track_info["track"]
        a = track_info["artist"]
        al = track_info["album"]
        d = track_info["duration_s"]

        log.info("─" * 40)
        log.info("🎶  Intentando: %s — %s", a, t)

        # Cascada: LRCLIB → Genius → Lyrics.ovh
        lyrics_raw = (
            fetch_lyrics_lrclib(t, a, al, d) or
            fetch_lyrics_genius(t, a) or
            fetch_lyrics_ovh(t, a)
        )

        if lyrics_raw:
            chosen_track = track_info
            break
        else:
            log.info("⏭️   Sin letra disponible, probando siguiente pista…")

    if not lyrics_raw or not chosen_track:
        log.error("❌  No se encontró letra para ninguna pista del top.")
        return

    # Guardar la canción elegida para no repetirla mañana
    state_file = Path(".lyric_state.json")
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            state = {}
    state["last_track"] = f"{chosen_track['artist']} - {chosen_track['track']}"
    state_file.write_text(json.dumps(state))

    # ── PASO 3: Limpiar y seleccionar fragmento ─────────────────
    lines = sanitize_lyrics(lyrics_raw)
    if not lines:
        log.error("❌  La letra quedó vacía tras el saneamiento.")
        return

    chunk = pick_lyric_chunk(lines, CONFIG["LYRIC_CHUNK_SIZE"])

    # Cabecera del mensaje
    header = f"♪ {chosen_track['artist']} — {chosen_track['track']}\n{'─'*30}\n"
    final_text = header + chunk

    log.info("\n%s\n%s\n%s", "=" * 50, final_text, "=" * 50)

    # ── PASO 4: Guardar localmente siempre ──────────────────────
    out_path = Path(CONFIG["LOCAL_OUTPUT_FILE"])
    out_path.write_text(final_text, encoding="utf-8")
    log.info("💾  Guardado localmente en '%s'", out_path)

    # ── PASO 5: Enviar al Flipper Zero ──────────────────────────
    success = send_to_flipper(final_text, CONFIG["FLIPPER_DEST_PATH"])
    if not success:
        log.info("ℹ️   Flipper no conectado. El lyric está en '%s'.", out_path)

    # ── PASO 6: Notificación al iPhone via ntfy ─────────────────
    notif_title = f"♪ {chosen_track['artist']} — {chosen_track['track']}"
    send_ntfy(notif_title, chunk)

    generate_stats(chunk, chosen_track, top_tracks_ordered)
    
    log.info("✨  Pipeline completado.")


# ─────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()
