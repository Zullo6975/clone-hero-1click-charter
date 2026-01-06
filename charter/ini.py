from __future__ import annotations

from pathlib import Path


def write_song_ini(
    out_path: Path,
    title: str,
    artist: str = "",
    charter: str = "1clickcharter",
    delay_ms: int = 0,
    audio_filename: str = "song.ogg",
) -> None:
    """
    Minimal Clone Hero song.ini that works.
    """
    lines = [
        "[song]",
        f"name = {title}",
        f"artist = {artist}",
        "album = ",
        "genre = ",
        "year = ",
        f"charter = {charter}",
        f"delay = {delay_ms}",
        f"song = {audio_filename}",
        "preview_start_time = 0",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
