from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pretty_midi
from charter.audio import normalize_and_save
from charter.chart_format import write_chart_file
from charter.config import ChartConfig
from charter.ini import write_song_ini
from charter.metadata import enrich_from_musicbrainz
from charter.midi import write_dummy_notes_mid, write_real_notes_mid
# Import the stats engine to calculate complexity
from charter.stats import compute_chart_stats
from charter.validator import validate_chart_file


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="1clickcharter CLI")
    p.add_argument("--audio", required=False)
    p.add_argument("--out", required=False)

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

    # Validation
    p.add_argument("--validate", help="Path to a song folder to validate (Health Check).")

    # Difficulty Scaling
    p.add_argument("--hard-gap-ms", type=int, default=120)
    p.add_argument("--med-gap-ms", type=int, default=220)
    p.add_argument("--easy-gap-ms", type=int, default=450)

    # Interoperability
    p.add_argument("--write-chart", action="store_true", help="Export .chart file for Moonscraper.") # <--- Added Arg

    return p.parse_args()

def main():
    args = parse_args()

    # --- HANDLE VALIDATION MODE ---
    if args.validate:
        folder = Path(args.validate)
        if not folder.exists():
            print(f"Error: Folder not found: {folder}")
            return 1
        validate_chart_file(folder, summary_only=True)
        return 0
    # ------------------------------

    # --- ENFORCE REQUIREMENTS FOR GENERATION ---
    if not args.audio or not args.out:
        print("Error: --audio and --out are required for chart generation.")
        print("usage: 1ClickCharter [--validate ...] | --audio AUDIO --out OUT ...")
        return 1
    # -------------------------------------------

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
        rhythmic_glue=not args.no_rhythmic_glue,
        hard_min_gap_ms=args.hard_gap_ms,
        medium_min_gap_ms=args.med_gap_ms,
        easy_min_gap_ms=args.easy_gap_ms,
        write_chart=args.write_chart,
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
        # Note: write_real_notes_mid returns shift_seconds used to align audio
        shift_seconds, final_sections, density_data = write_real_notes_mid(
            audio_path=audio_path,
            out_path=notes_mid,
            cfg=cfg,
            stats_out_path=stats_out,
            override_sections=loaded_sections,
            dry_run=args.analyze_only
        )

    if cfg.write_chart and not args.analyze_only and args.mode != "dummy":
        try:
            # Reload the generated MIDI to get the full combined note list
            # or refactor write_real_notes_mid to return notes.
            # Re-reading is safer and cleaner here as it captures exactly what was written.
            pm_data = pretty_midi.PrettyMIDI(str(notes_mid))

            # Find the GUITAR track
            guitar_notes = []
            for inst in pm_data.instruments:
                if inst.name == "PART GUITAR":
                    guitar_notes = inst.notes
                    break

            chart_path = out_dir / "notes.chart"

            # Determine tempo (use initial tempo from MIDI)
            tempo = pm_data.get_tempo_changes()[1][0]

            print(f"   Exporting Moonscraper chart: {chart_path.name}")
            write_chart_file(
                out_path=chart_path,
                song_name=title,
                artist_name=args.artist,
                charter_name=args.charter,
                bpm=tempo,
                notes=guitar_notes,
                sections=final_sections,
                offset_seconds=0.0 # MIDI is already shifted, so no offset needed relative to audio start?
                                   # Actually, .chart defines Offset=0 and SyncTrack starts at 0.
                                   # If audio is padded by shift_seconds, the notes align naturally.
            )
        except Exception as e:
            print(f"Warning: Failed to write .chart file: {e}")

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

    # --- CALCULATE COMPLEXITY ---
    complexity_tier = -1
    try:
        if notes_mid.exists():
            # Pass the just-generated MIDI to the stats engine
            full_stats = compute_chart_stats(
                notes_mid_path=notes_mid,
                title=title,
                artist=args.artist,
                mode=args.mode,
                # We don't strictly need precise audio duration for just complexity
                song_duration_sec=None
            )
            complexity_tier = full_stats.complexity
    except Exception as e:
        print(f"Warning: Could not calculate complexity: {e}")
    # ----------------------------

    write_song_ini(
        out_dir / "song.ini",
        title=title,
        artist=args.artist,
        album=args.album,
        genre=args.genre,
        year=args.year,
        charter=args.charter,
        delay_ms=final_delay,
        diff_guitar=complexity_tier # Pass it here
    )

    print(f"✅ Generated: {title}")
    if shift_seconds > 0:
        print(f"   (Auto-delayed by {shift_seconds:.2f}s for playability)")

if __name__ == "__main__":
    main()
