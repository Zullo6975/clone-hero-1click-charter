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
    p.add_argument("--delay-ms", type=int, default=0, help="Chart delay in ms (writes to song.ini)")
    p.add_argument("--bpm", type=float, default=120.0, help="Dummy chart BPM (v0 only)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or audio_path.stem

    # Copy audio into output folder (keep original filename)
    audio_out = out_dir / audio_path.name
    if audio_out.resolve() != audio_path:
        shutil.copy2(audio_path, audio_out)

    # Write song.ini
    write_song_ini(
        out_path=out_dir / "song.ini",
        title=title,
        artist=args.artist,
        delay_ms=args.delay_ms,
        audio_filename=audio_out.name,
    )

    # Write a dummy notes.mid (just to validate CH loading)
    write_dummy_notes_mid(out_path=out_dir / "notes.mid", bpm=args.bpm, bars=16)

    print("✅ Export complete")
    print(f"Folder: {out_dir}")
    print(f"Audio:  {audio_out.name}")
    print("Files:  song.ini, notes.mid")


if __name__ == "__main__":
    main()
