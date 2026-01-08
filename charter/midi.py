from __future__ import annotations
from pathlib import Path
import random
import json

import pretty_midi # type: ignore
import librosa # type: ignore
import numpy as np # type: ignore

from charter.config import ChartConfig, LANE_PITCHES, TRACK_NAME, SP_PITCH
from charter.audio import detect_onsets
from charter.sections import generate_sections, compute_section_stats
from charter.star_power import generate_star_power_phrases

def _filter_onsets(
    candidates: list,
    duration: float,
    cfg: ChartConfig
) -> list:
    """Selects onsets based on density settings."""
    # Window size for density check
    window = 4.0
    # Minimum gap in seconds
    min_gap = max(0.05, cfg.min_gap_ms / 1000.0)

    selected = []

    # Simple bucket sort by time window
    buckets = {}
    for c in candidates:
        idx = int(c.t // window)
        buckets.setdefault(idx, []).append(c)

    for w in sorted(buckets.keys()):
        # Sort candidates in this window by strength (loudest first)
        items = sorted(buckets[w], key=lambda x: x.strength, reverse=True)

        # How many notes allowed in this window?
        # max_nps * window_seconds
        quota = int(cfg.max_nps * window)

        count = 0
        for c in items:
            if count >= quota: break

            # Distance check against already selected notes
            if any(abs(c.t - s.t) < min_gap for s in selected):
                continue

            selected.append(c)
            count += 1

    selected.sort(key=lambda x: x.t)
    return selected

def _assign_lane(
    prev_lane: int,
    rng: random.Random,
    cfg: ChartConfig
) -> int:
    """
    Decides the next lane based on Movement Bias and Available Lanes.
    """
    # Available lanes: 0=G, 1=R, 2=Y, 3=B, 4=O
    options = [0, 1, 2, 3]
    if cfg.allow_orange:
        options.append(4)

    weights = []
    for lane in options:
        dist = abs(lane - prev_lane)

        if dist == 0:
            # Stay in lane
            w = 2.0 * (1.0 - cfg.movement_bias) # Lower bias = stickier lanes
        elif dist == 1:
            # Move by 1
            w = 2.0
        elif dist == 2:
            # Move by 2
            w = 1.0 + (cfg.movement_bias * 0.5) # Higher bias = jumps ok
        else:
            # Big jump
            w = 0.2 + (cfg.movement_bias * 0.8)

        weights.append(max(0.1, w))

    return rng.choices(options, weights=weights, k=1)[0]

def write_chart(
    audio_path: Path,
    out_path: Path,
    cfg: ChartConfig,
    stats_out: Path | None = None
) -> None:
    rng = random.Random(cfg.seed)

    # 1. Analyze
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    onsets = detect_onsets(audio_path) # Raw candidates

    # 2. Filter (Density Control)
    notes = _filter_onsets(onsets, duration, cfg)
    times = [n.t for n in notes]

    # 3. Quantize (Grid Snap)
    # librosa beat track
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)

    if len(beat_times) > 1:
        # Create a grid based on grid_snap setting
        grid = []
        divs = {"1/4": 1, "1/8": 2, "1/16": 4}.get(cfg.grid_snap, 2)

        for i in range(len(beat_times)-1):
            s, e = beat_times[i], beat_times[i+1]
            span = e - s
            for d in range(divs):
                grid.append(s + (span * (d/divs)))
        grid = np.array(grid)

        # Snap times to nearest grid point
        snapped_times = []
        for t in times:
            idx = (np.abs(grid - t)).argmin()
            snapped_times.append(grid[idx])

        # Remove duplicates from snapping
        times = sorted(list(set(snapped_times)))

    # 4. Assign Lanes & Generate Events
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))
    guitar = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    prev_lane = 2 # Start on Yellow
    chord_starts = []

    for i, t in enumerate(times):
        # Lane Logic
        lane = _assign_lane(prev_lane, rng, cfg)
        prev_lane = lane

        # Note Length / Sustain Logic
        # Gap to next note
        next_t = times[i+1] if i+1 < len(times) else t + 2.0
        gap = next_t - t

        # Base length: Staccato (0.1) vs Sustain
        # sustain_len 0.0 -> almost never sustain
        # sustain_len 1.0 -> sustain everything > 0.5s

        is_sustain = False
        if gap > 0.4:
            chance = cfg.sustain_len # Simple probability if gap is big enough
            if rng.random() < chance:
                is_sustain = True

        dur = min(gap - 0.05, 0.15) # Default short
        if is_sustain:
            dur = gap - 0.1

        # Chord Logic
        # If random check passes AND we aren't forcing taps
        lanes = [lane]
        if rng.random() < cfg.chord_prob:
            # Pick a second lane adjacent or nearby
            opts = [l for l in [lane-1, lane+1] if 0 <= l <= 4]
            if not cfg.allow_orange:
                opts = [l for l in opts if l != 4]

            if opts:
                l2 = rng.choice(opts)
                lanes.append(l2)
                chord_starts.append(t)

        # Write to MIDI
        for l in lanes:
            pitch = LANE_PITCHES[l]
            note = pretty_midi.Note(
                velocity=100,
                pitch=pitch,
                start=t,
                end=t + dur
            )
            guitar.notes.append(note)

    pm.instruments.append(guitar)

    # 5. Sections
    final_sections = []
    if cfg.add_sections:
        # Pass audio path for analysis
        final_sections = generate_sections(str(audio_path), duration)
        evt_inst = pretty_midi.Instrument(0, name="EVENTS")
        for s in final_sections:
            pm.lyrics.append(pretty_midi.Lyric(f"[section {s.name}]", float(s.start)))
        pm.instruments.append(evt_inst)

    # 6. Star Power
    if cfg.add_star_power:
        phrases = generate_star_power_phrases(
            note_times=times,
            duration_sec=duration
        )
        for p in phrases:
            guitar.notes.append(pretty_midi.Note(
                velocity=100, pitch=SP_PITCH, start=p.start, end=p.end
            ))

    # Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))

    # 7. Stats
    if stats_out:
        stats = compute_section_stats(
            note_starts=times,
            chord_starts=chord_starts,
            sections=final_sections,
            duration_sec=duration
        )
        # Quick export
        data = {
            "title": "Generated Chart",
            "stats": [asdict(s) for s in stats]
        }
        stats_out.write_text(json.dumps(data, indent=2))
