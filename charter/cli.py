from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import librosa  # type: ignore

from charter.ini import write_song_ini
from charter.metadata import enrich_from_musicbrainz
from charter.midi import write_dummy_notes_mid, write_real_notes_mid
from charter.stats import compute_chart_stats, write_stats_json, format_stats_summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="1clickcharter - export a Clone Hero-ready folder")
    p.add_argument("--audio", required=True, help="Path to audio file (mp3/ogg/wav/flac)")
    p.add_argument("--out", required=True, help="Output folder (will be created/used)")

    p.add_argument("--title", default=None, help="Song title (defaults to filename stem)")
    p.add_argument("--artist", default="", help="Artist (optional)")
    p.add_argument("--album", default="", help="Album (optional)")
    p.add_argument("--genre", default="", help="Genre (optional)")
    p.add_argument("--year", default="", help="Year (optional)")
    p.add_argument("--charter", default="Zullo7569", help="Charter name to write into song.ini")
    p.add_argument("--delay-ms", type=int, default=0, help="Chart delay in ms")

    p.add_argument("--fetch-metadata", action="store_true", help="Fetch album/year/cover art via MusicBrainz")
    p.add_argument("--user-agent", default="1clickcharter/0.1 (Zullo7569)", help="HTTP User-Agent string")

    p.add_argument("--mode", choices=["dummy", "real"], default="dummy", help="Chart generation mode")

    # dummy chart params (baseline)
    p.add_argument("--bpm", type=float, default=115.0, help="Dummy chart BPM")
    p.add_argument("--bars", type=int, default=24, help="Dummy chart length in bars")
    p.add_argument("--density", type=float, default=0.58, help="Dummy chart density 0..1 (higher=harder)")

    # real chart params (v0 knobs)
    p.add_argument("--min-gap-ms", type=int, default=140, help="Minimum spacing between notes (ms)")
    p.add_argument("--max-nps", type=float, default=3.8, help="Max notes per second (rolling 1s window)")
    p.add_argument("--seed", type=int, default=42, help="Deterministic lane feel")

    # stats
    p.add_argument("--stats-window-sec", type=float, default=15.0, help="Section window size for stats (seconds)")
    p.add_argument("--no-stats", action="store_true", help="Disable stats.json output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or audio_path.stem

    # Always output audio as song.mp3
    audio_out = out_dir / "song.mp3"
    shutil.copy2(audio_path, audio_out)

    # Optional metadata enrichment (best-effort, never overwrites explicit CLI fields)
    if args.fetch_metadata and args.artist and title:
        cache_path = Path.home() / ".cache" / "1clickcharter" / "metadata.json"
        enriched = enrich_from_musicbrainz(
            artist=args.artist,
            title=title,
            user_agent=args.user_agent,
            cache_path=cache_path,
        )
        if not args.album and enriched.album:
            args.album = enriched.album
        if not args.year and enriched.year:
            args.year = enriched.year
        if enriched.cover_bytes:
            (out_dir / "album.png").write_bytes(enriched.cover_bytes)

    # Write song.ini referencing song.mp3
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

    # Write notes.mid
    notes_mid = out_dir / "notes.mid"
    if args.mode == "dummy":
        write_dummy_notes_mid(
            out_path=notes_mid,
            bpm=args.bpm,
            bars=args.bars,
            density=args.density,
        )
    else:
        write_real_notes_mid(
            audio_path=audio_path,
            out_path=notes_mid,
            min_gap_ms=args.min_gap_ms,
            max_nps=args.max_nps,
            seed=args.seed,
        )

    print("✅ Export complete")
    print(f"Mode:     {args.mode}")
    print(f"Folder:   {out_dir}")
    print("Audio:    song.mp3")
    print("Files:    song.ini, notes.mid" + (", album.png" if (out_dir / "album.png").exists() else ""))

    # ---- Stats (safe, read-only on notes.mid) ----
    if not args.no_stats:
        try:
            song_duration = float(librosa.get_duration(path=str(audio_path)))
        except Exception:
            song_duration = 0.0

        stats = compute_chart_stats(
            notes_mid_path=notes_mid,
            title=title,
            artist=args.artist,
            mode=args.mode,
            song_duration_sec=song_duration,
            window_sec=float(args.stats_window_sec),
        )
        write_stats_json(out_dir / "stats.json", stats)
        print()
        print(format_stats_summary(stats))
        print(f"Wrote:    {out_dir / 'stats.json'}")


if __name__ == "__main__":
    main()
