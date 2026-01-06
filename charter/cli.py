from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from charter.ini import write_song_ini
from charter.midi import write_dummy_notes_mid


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="1clickcharter (v0) - export a Clone Hero-ready folder")
    p.add_argument("--audio", required=True, help="Path to audio file (mp3/ogg/wav/flac)")
    p.add_argument("--out", required=True, help="Output folder (will be created/used)")

    p.add_argument("--title", default=None, help="Song title (defaults to filename stem)")
    p.add_argument("--artist", default="", help="Artist (optional)")
    p.add_argument("--album", default="", help="Album (optional)")
    p.add_argument("--genre", default="", help="Genre (optional)")
    p.add_argument("--year", default="", help="Year (optional)")

    p.add_argument("--charter", default="Zullo7569", help="Charter name to write into song.ini")
    p.add_argument("--delay-ms", type=int, default=0, help="Chart delay in ms (writes to song.ini)")

    # dummy chart params (temporary)
    p.add_argument("--bpm", type=float, default=120.0, help="Dummy chart BPM (v0 only)")
    p.add_argument("--bars", type=int, default=16, help="Dummy chart length in bars (v0 only)")
    p.add_argument("--density", type=float, default=0.55, help="Dummy chart density 0..1 (lower=easier)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or audio_path.stem

    # Always output audio as "song.mp3"
    audio_out = out_dir / "song.mp3"
    shutil.copy2(audio_path, audio_out)

    # Write song.ini referencing "song.mp3"
    write_song_ini(
        out_path=out_dir / "song.ini",
        title=title,
        artist=args.artist,
        album=args.album,
        genre=args.genre,
        year=args.year,
        charter=args.charter,
        delay_ms=args.delay_ms,
        audio_filename="song.mp3",
    )

    # Write dummy notes.mid (easy baseline)
    write_dummy_notes_mid(
        out_path=out_dir / "notes.mid",
        bpm=args.bpm,
        bars=args.bars,
        density=args.density,
    )

    print("✅ Export complete")
    print(f"Folder:   {out_dir}")
    print("Audio:    song.mp3")
    print("Files:    song.ini, notes.mid")


if __name__ == "__main__":
    main()
