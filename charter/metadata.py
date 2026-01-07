from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests # type: ignore


@dataclass
class EnrichedMetadata:
    album: str = ""
    year: str = ""
    cover_bytes: bytes | None = None


def _cache_key(artist: str, title: str) -> str:
    h = hashlib.sha256(f"{artist}||{title}".encode("utf-8")).hexdigest()
    return h[:16]


def _load_cache(cache_path: Path) -> dict[str, Any]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache_path: Path, data: dict[str, Any]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        # Fallback: if the default path is read-only, try writing to the user's home directory
        user_fallback = Path.home() / ".1clickcharter_cache"
        user_fallback.parent.mkdir(parents=True, exist_ok=True)
        user_fallback.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Warning: Original cache path was read-only. Saved to {user_fallback} instead.")


def _sleep_polite() -> None:
    time.sleep(1.05)  # simple 1 req/sec-ish politeness


def enrich_from_musicbrainz(
    artist: str,
    title: str,
    *,
    user_agent: str,
    cache_path: Path,
) -> EnrichedMetadata:
    artist = artist.strip()
    title = title.strip()
    if not artist or not title:
        return EnrichedMetadata()

    cache = _load_cache(cache_path)
    key = _cache_key(artist, title)
    if key in cache:
        hit = cache[key]
        return EnrichedMetadata(album=hit.get("album", ""), year=hit.get("year", ""))

    # Search recordings
    q = f'recording:"{title}" AND artist:"{artist}"'
    _sleep_polite()
    r = requests.get(
        "https://musicbrainz.org/ws/2/recording/",
        params={"query": q, "fmt": "json", "limit": "5"},
        headers={"User-Agent": user_agent, "Accept": "application/json"},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    recs = data.get("recordings") or []
    if not recs:
        return EnrichedMetadata()

    rec = recs[0]
    releases = rec.get("releases") or []

    best = None
    for rel in releases:
        if rel.get("title"):
            best = rel
            if rel.get("date"):
                break

    album = (best or {}).get("title", "") or ""
    date = (best or {}).get("date", "") or ""
    year = date[:4] if len(date) >= 4 else ""
    rel_id = (best or {}).get("id")

    cover_bytes = None
    if rel_id:
        try:
            _sleep_polite()
            caa = requests.get(
                f"https://coverartarchive.org/release/{rel_id}",
                headers={"User-Agent": user_agent, "Accept": "application/json"},
                timeout=20,
            )
            if caa.status_code == 200:
                caa_json = caa.json()
                images = caa_json.get("images") or []
                front = next((img for img in images if img.get("front")), None) or (images[0] if images else None)
                if front and front.get("image"):
                    img_url = front["image"]
                    _sleep_polite()
                    img = requests.get(img_url, headers={"User-Agent": user_agent}, timeout=30)
                    if img.status_code == 200 and img.content:
                        cover_bytes = img.content
        except Exception:
            cover_bytes = None

    cache[key] = {"album": album, "year": year, "artist": artist, "title": title}
    _save_cache(cache_path, cache)

    return EnrichedMetadata(album=album, year=year, cover_bytes=cover_bytes)
