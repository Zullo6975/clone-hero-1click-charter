from __future__ import annotations
from pathlib import Path

import pretty_midi
from charter.config import DIFFICULTY_PITCHES, SP_PITCH

RESOLUTION = 192  # Standard .chart ticks per quarter note

def seconds_to_ticks(seconds: float, bpm: float) -> int:
    return int(seconds * bpm * RESOLUTION / 60.0)

def write_chart_file(
    out_path: Path,
    song_name: str,
    artist_name: str,
    charter_name: str,
    bpm: float,
    notes: list[pretty_midi.Note],
    sections: list[dict] | list,
    offset_seconds: float = 0.0
):
    """
    Writes a .chart file compatible with Moonscraper/Clone Hero.
    """

    # Organize notes by difficulty
    # Filter notes by pitch ranges defined in config
    layers = {
        "Expert": [],
        "Hard": [],
        "Medium": [],
        "Easy": []
    }

    star_power = []

    # Reverse lookup for lane mapping (Pitch -> Lane Index)
    # We need separate maps for each difficulty because pitches differ
    pitch_to_lane = {}
    diff_map_name = {}

    for diff, mapping in DIFFICULTY_PITCHES.items():
        for lane, pitch in mapping.items():
            pitch_to_lane[pitch] = lane
            diff_map_name[pitch] = diff

    for note in notes:
        start_ticks = seconds_to_ticks(note.start - offset_seconds, bpm)
        end_ticks = seconds_to_ticks(note.end - offset_seconds, bpm)
        duration = max(0, end_ticks - start_ticks)

        p = note.pitch

        if p == SP_PITCH:
            star_power.append((start_ticks, duration))
            continue

        if p == 103: # Solo Marker
            # We handle solos via Section events, skip note marker
            continue

        if p in diff_map_name:
            d_name = diff_map_name[p]
            lane = pitch_to_lane[p]
            layers[d_name].append({
                "tick": start_ticks,
                "lane": lane,
                "length": duration
            })

    # Sort events
    for d in layers:
        layers[d].sort(key=lambda x: x["tick"])
    star_power.sort(key=lambda x: x[0])

    lines = []

    # --- [Song] ---
    lines.append("[Song]")
    lines.append("{")
    lines.append(f'  Name = "{song_name}"')
    lines.append(f'  Artist = "{artist_name}"')
    lines.append(f'  Charter = "{charter_name}"')
    lines.append(f'  Resolution = {RESOLUTION}')
    lines.append(f'  Offset = 0')
    lines.append(f'  MusicStream = "song.mp3"')
    lines.append("}")

    # --- [SyncTrack] ---
    lines.append("[SyncTrack]")
    lines.append("{")
    lines.append("  0 = TS 4")
    # BPM is stored as BPM * 1000
    lines.append(f"  0 = B {int(bpm * 1000)}")
    lines.append("}")

    # --- [Events] ---
    lines.append("[Events]")
    lines.append("{")
    if sections:
        for s in sections:
            # Handle both dict (JSON) and Section object
            s_name = s['name'] if isinstance(s, dict) else s.name
            s_start = float(s['start'] if isinstance(s, dict) else s.start)

            # Apply offset shift correction (audio padding)
            # The offset_seconds passed here is usually negative of the shift
            # or we calculate relative to audio start.
            # In midi.py, 'times' are already shifted.

            # Use max(0) to prevent negative ticks on Intro
            tick = max(0, seconds_to_ticks(s_start - offset_seconds, bpm))
            lines.append(f'  {tick} = E "section {s_name}"')
    lines.append("}")

    # --- Difficulty Tracks ---
    # Map internal names to .chart section headers
    chart_headers = {
        "Expert": "ExpertSingle",
        "Hard": "HardSingle",
        "Medium": "MediumSingle",
        "Easy": "EasySingle"
    }

    for diff_name, events in layers.items():
        if not events: continue

        header = chart_headers.get(diff_name)
        if not header: continue

        lines.append(f"[{header}]")
        lines.append("{")

        # Write Notes: tick = N lane length
        for e in events:
            lines.append(f"  {e['tick']} = N {e['lane']} {e['length']}")

        # Write Star Power: tick = S 2 length
        # SP is shared across difficulties in the generator, so we replicate it
        for start, dur in star_power:
            lines.append(f"  {start} = S 2 {dur}")

        lines.append("}")

    # Write file
    out_path.write_text("\n".join(lines), encoding="utf-8")
