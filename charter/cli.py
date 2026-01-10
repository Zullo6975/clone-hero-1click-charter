from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from charter.config import ChartConfig
from charter.ini import write_song_ini
from charter.metadata import enrich_from_musicbrainz
from charter.midi import write_dummy_notes_mid, write_real_notes_mid
from charter.stats import compute_chart_stats, write_stats_json, format_stats_summary
from charter.audio import normalize_and_save

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="1clickcharter CLI")
    p.add_argument("--audio", required=True)
    p.add_argument("--out", required=True)

    # Metadata
    p.add_argument("--title")
    p.add_argument("--artist", default="")
    p.add_argument("--album", default="")
    p.add_argument("--genre", default="")
    p.add_argument("--year", default="")
    p.add_argument("--charter", default="Zullo7569")
    p.add_argument("--fetch-metadata", action="store_true")
    p.add_argument("--user-agent", default="1clickcharter/0.1")
    p.add_argument("--delay-ms", type=int, default=0)

    # Engine Settings
    p.add_argument("--mode", default="real")
    p.add_argument("--max-nps", type=float, default=3.8)
    p.add_argument("--min-gap-ms", type=int, default=140)
    p.add_argument("--seed", type=int, default=42)

    # New Knobs
    p.add_argument("--no-orange", action="store_true")
    p.add_argument("--chord-prob", type=float, default=0.12)
    p.add_argument("--sustain-len", type=float, default=0.5)
    p.add_argument("--movement-bias", type=float, default=0.5)
    p.add_argument("--grid-snap", default="1/8")

    # Sustain Tuning (v1.1.2)
    p.add_argument("--sustain-threshold", type=float, default=0.8)
    p.add_argument("--sustain-buffer", type=float, default=0.25)

    # Rhythm (v1.2)
    p.add_argument("--no-rhythmic-glue", action="store_true")
    p.add_argument("--no-stats", action="store_true")

    # Manual Overrides (v1.2)
    p.add_argument("--analyze-only", action="store_true", help="Analyze audio and output sections, no chart generation.")
    p.add_argument("--section-overrides", help="Path to JSON file with section definitions.")

    # Dummy params
    p.add_argument("--bpm", type=float, default=120.0)
    p.add_argument("--bars", type=int, default=32)
    p.add_argument("--density", type=float, default=0.5)

    return p.parse_args()

def main():
    args = parse_args()

    cfg = ChartConfig(
        mode=args.mode,
        max_nps=args.max_nps,
        min_gap_ms=args.min_gap_ms,
        seed=args.seed,
        allow_orange=not args.no_orange,
        chord_prob=args.chord_prob,
        sustain_len=args.sustain_len,
        movement_bias=args.movement_bias,
        grid_snap=args.grid_snap,
        sustain_threshold=args.sustain_threshold,
        sustain_buffer=args.sustain_buffer,
        rhythmic_glue=not args.no_rhythmic_glue
    )

    audio_path = Path(args.audio).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or audio_path.stem

    # --- AUDIO PROCESSING (Normalize) ---
    dest_audio = out_dir / "song.mp3"

    if not args.analyze_only:
        print(f"Processing audio: {audio_path.name}...")
        normalize_and_save(audio_path, dest_audio)

    if args.fetch_metadata and args.artist and not args.analyze_only:
        try:
            cache_path = Path.home() / ".cache" / "1clickcharter" / "metadata.json"
            enriched = enrich_from_musicbrainz(
                artist=args.artist, title=title,
                user_agent=args.user_agent, cache_path=cache_path
            )
            if enriched.cover_bytes:
                (out_dir / "album.png").write_bytes(enriched.cover_bytes)
            if not args.album and enriched.album: args.album = enriched.album
            if not args.year and enriched.year: args.year = enriched.year
        except Exception as e:
            print(f"Metadata fetch failed: {e}")

    # Load Overrides
    loaded_sections = None
    if args.section_overrides:
        try:
            src = Path(args.section_overrides)
            if src.exists():
                data = json.loads(src.read_text(encoding='utf-8'))
                loaded_sections = data.get("sections", data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"Warning: Failed to load section overrides: {e}")

    # Generate Chart & Get Shift Amount
    notes_mid = out_dir / "notes.mid"
    stats_out = out_dir / "stats_internal.json"

    shift_seconds = 0.0
    final_sections = []
    density_data = []

    if args.mode == "dummy":
        shift_seconds = write_dummy_notes_mid(notes_mid, args.bpm, args.bars, args.density)
    else:
        shift_seconds, final_sections, density_data = write_real_notes_mid(
            audio_path=audio_path,
            out_path=notes_mid,
            cfg=cfg,
            stats_out_path=stats_out,
            override_sections=loaded_sections,
            dry_run=args.analyze_only
        )

    if args.analyze_only:
        out_json = out_dir / "sections.json"

        serializable_sections = []
        for s in final_sections:
             if hasattr(s, "__dict__"): serializable_sections.append(asdict(s))
             elif isinstance(s, dict): serializable_sections.append(s)
             else: serializable_sections.append(s)

        out_json.write_text(json.dumps({
            "sections": serializable_sections,
            "density": density_data
        }, indent=2))
        print(f"✅ Analysis Complete. Data written to: {out_json}")
        return

    final_delay = args.delay_ms + int(shift_seconds * 1000)

    write_song_ini(
        out_dir / "song.ini",
        title=title,
        artist=args.artist,
        album=args.album,
        genre=args.genre,
        year=args.year,
        charter=args.charter,
        delay_ms=final_delay
    )

    print(f"✅ Generated: {title}")
    if shift_seconds > 0:
        print(f"   (Auto-delayed by {shift_seconds:.2f}s for playability)")

if __name__ == "__main__":
    main()
