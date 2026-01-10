from __future__ import annotations

from pathlib import Path


def write_song_ini(
    out_path: Path,
    title: str,
    artist: str = "",
    album: str = "",
    genre: str = "",
    year: str = "",
    charter: str = "Zullo7569",
    delay_ms: int = 0,
    diff_guitar: int = -1,  # New param: -1 = ?, 0-6 = dots
    audio_filename: str = "song.mp3",
) -> None:
    """
    Minimal-but-nice Clone Hero song.ini.
    Now includes difficulty for the preview menu.
    """
    lines = [
        "[song]",
        f"name = {title}",
        f"artist = {artist}",
        f"album = {album}",
        f"genre = {genre}",
        f"year = {year}",
        f"charter = {charter}",
        f"delay = {delay_ms}",
        f"diff_guitar = {diff_guitar}",
        f"song = {audio_filename}",
        "preview_start_time = 0",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
