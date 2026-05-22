# 🐬 Lyric Flipper

> Every morning, a fragment of your most-played song lands on your iPhone — and on your Flipper Zero.

**Lyric Flipper** is a personal automation that connects your Spotify listening history with a daily push notification containing a lyric fragment from one of your top tracks. No apps to open, no feeds to scroll — it just arrives.

---

## What it does

Every day at 9:00 AM, the system:

1. Fetches your top 30 most-played tracks from Spotify (last 4 weeks)
2. Picks one at random — never repeating yesterday's song
3. Finds the lyrics through a cascade of providers (LRCLIB → Genius → Lyrics.ovh)
4. Cleans the text and selects a random block of 5 consecutive lines
5. Sends it as a push notification to your iPhone via [ntfy](https://ntfy.sh)
6. If a Flipper Zero is connected via USB, writes the lyric to its SD card too

Every Sunday at 9:00 PM, it sends a numbered top 10 recap of the week.

Nothing runs on your computer. Everything runs on GitHub Actions.

---

## Stack

- **Python 3.11** — core pipeline
- **Spotify Web API** — top tracks via OAuth 2.0 Authorization Code Flow
- **LRCLIB / Genius / Lyrics.ovh** — lyrics providers with automatic fallback
- **ntfy.sh** — push notifications to iPhone (no account needed)
- **pyserial** — serial communication with Flipper Zero over USB
- **GitHub Actions** — scheduled execution, zero infrastructure

---

## How it works

```
Spotify API → top 30 tracks
      ↓
Random shuffle (no repeat from yesterday)
      ↓
LRCLIB → Genius → Lyrics.ovh  (first one that finds lyrics wins)
      ↓
Regex cleanup + random 5-line block selection
      ↓
ntfy push notification → iPhone
      ↓
Flipper Zero SD card (if connected)
```

---

## Setup

```bash
pip install spotipy lyricsgenius requests pyserial
```

Create a Spotify app at [developer.spotify.com](https://developer.spotify.com/dashboard), then configure your credentials either in the `CONFIG` section of `lyric_flipper.py` or as environment variables:

```bash
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
NTFY_TOPIC=your-secret-topic
```

Run once locally to authenticate with Spotify (opens a browser):

```bash
python lyric_flipper.py
```

For automated daily delivery, deploy to GitHub Actions using the included workflows and store your credentials as repository secrets.

---

## Flipper Zero

If a Flipper Zero is connected via USB when the script runs, the lyric is written directly to `/ext/apps_data/lyric_of_day.txt` on its SD card via serial CLI. The port is auto-detected — no configuration needed.

---

*Inspired by the idea that your most-played song of the week probably has something worth reading.*

---

---

## 🇪🇸 Descripción en español

**Lyric Flipper** es una automatización personal que conecta tu historial de Spotify con una notificación diaria en el iPhone. Cada mañana a las 9:00 elige aleatoriamente una de tus 30 canciones más escuchadas del último mes, extrae un fragmento de la letra y te lo manda como notificación push — sin abrir ninguna app.

Los domingos por la noche envía además un resumen con tu top 10 de la semana.

Todo corre en GitHub Actions: no necesita ningún ordenador encendido. Si tienes un Flipper Zero, también escribe el fragmento en su tarjeta SD por USB.

**Tecnologías:** Python · Spotify Web API · OAuth 2.0 · LRCLIB · ntfy.sh · pyserial · GitHub Actions
